#!/usr/bin/env python3
"""CVD Boundary 026: read-only public Git provenance census.

Requires authenticated GitHub CLI (gh). Writes local JSON, never modifies repos.
Private repository identities are neither printed nor stored in the public report.
Exit nonzero if discovery is incomplete; do not claim full-estate coverage.
"""
import argparse, base64, datetime, json, subprocess, sys
from pathlib import Path

EXPECTED_REGISTRY = "https://github.com/DavidWise01/0root-provenance/blob/main/cvd/public-registry-2026-11-03.json"
POINTER_PATH = ".well-known/cvd.json"

def api(path):
    proc = subprocess.run(["gh", "api", "--include", path], capture_output=True, text=True)
    # --include prints HTTP status + headers followed by JSON body.
    output = proc.stdout
    if proc.returncode != 0:
        if "HTTP 404" in output or "HTTP 404" in proc.stderr or "404 Not Found" in proc.stderr:
            return None
        raise RuntimeError(proc.stderr.strip() or output[:300])
    split = output.find("\r\n\r\n")
    if split >= 0:
        body = output[split+4:]
    else:
        split = output.find("\n\n")
        body = output[split+2:] if split >= 0 else output
    return json.loads(body)

def scan(owner, max_pages):
    records, seen = [], set()
    private_count = 0
    pages = 0
    complete = False
    for page in range(1, max_pages + 1):
        batch = api(f"/user/repos?affiliation=owner&per_page=100&page={page}&sort=full_name")
        if not isinstance(batch, list):
            raise RuntimeError(f"Unexpected repository list shape on page {page}")
        if not batch:
            complete = True
            break
        pages += 1
        for repo in batch:
            if repo.get("owner", {}).get("login", "").casefold() != owner.casefold():
                continue
            name = repo["full_name"]
            if name in seen:
                continue
            seen.add(name)
            if repo.get("private") or repo.get("visibility") != "public":
                private_count += 1
                continue
            row = {"repository": name, "archived": bool(repo.get("archived")),
                   "branch": repo.get("default_branch")}
            try:
                content = api(f"/repos/{name}/contents/{POINTER_PATH}")
                if content is None:
                    row["status"] = "absent"
                elif content.get("type") != "file":
                    row["status"] = "unexpected_object"
                else:
                    decoded = base64.b64decode(content["content"]).decode("utf-8")
                    payload = json.loads(decoded)
                    correct = (payload.get("schema") == "CVD-PERMEATION-v1"
                               and payload.get("repository") == name
                               and payload.get("registry") == EXPECTED_REGISTRY)
                    row["status"] = "verified" if correct else "mismatch"
                    row["blob_sha"] = content.get("sha")
            except (ValueError, KeyError, UnicodeError) as exc:
                row["status"] = "malformed"
                row["error_type"] = type(exc).__name__
            except RuntimeError as exc:
                row["status"] = "unavailable"
                row["error_type"] = "api_error"
            records.append(row)
    counts = {}
    for row in records:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {"schema": "CVD-ESTATE-CENSUS-v1",
            "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "owner": owner,
            "scan_complete": complete,
            "pages_with_results": pages,
            "public_repositories_seen": len(records),
            "private_repositories_excluded": private_count,
            "counts": counts, "records": sorted(records, key=lambda r: r["repository"].lower())}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--owner", default="DavidWise01")
    p.add_argument("--output", default="cvd-estate-census.json")
    p.add_argument("--max-pages", type=int, default=100)
    args = p.parse_args()
    result = scan(args.owner, args.max_pages)
    Path(args.output).write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "records"}, indent=2))
    if not result["scan_complete"]:
        print("INCOMPLETE: pagination did not reach an empty final page",file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    sys.exit(main())
