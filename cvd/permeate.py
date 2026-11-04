#!/usr/bin/env python3
"""CVD Git-native permeation utility. Requires: gh CLI authenticated with repo write permission.
Default is DRY RUN. --apply writes only a missing .well-known/cvd.json file.
Never enumerates private repos into a public registry or changes license files.
"""
import argparse,json,subprocess,sys,time
REGISTRY="https://github.com/DavidWise01/0root-provenance/blob/main/cvd/public-registry-2026-11-03.json"
PROTOCOL="https://github.com/DavidWise01/0root-provenance/tree/main/cvd"
def gh(*args):
    p=subprocess.run(["gh",*args],text=True,capture_output=True)
    if p.returncode: raise RuntimeError(p.stderr.strip() or p.stdout.strip())
    return p.stdout
def repos(owner):
    page=1
    while True:
        batch=json.loads(gh("api",f"/users/{owner}/repos?per_page=100&page={page}&type=owner"))
        if not batch: break
        for repo in batch: yield repo
        page+=1
def pointer(name):
    return json.dumps({"schema":"CVD-PERMEATION-v1","repository":name,"registry":REGISTRY,
      "protocol":PROTOCOL,"roles":{"D1":"source attribution claims","D2":"rights/licensing claims",
      "D3":"derivation lineage","D4":"repository custody"},
      "policy":"Git evidence only; no automatic assertion or transfer of authorship or ownership",
      "state":"linked","formic":{"observer":"repository","steward":"Jane/Grandmother","mode":"witness-only"}},
      indent=2)+"\n"
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--owner",default="DavidWise01")
    ap.add_argument("--apply",action="store_true")
    ap.add_argument("--limit",type=int,default=0)
    ap.add_argument("--include-archived",action="store_true")
    args=ap.parse_args()
    counts={"observed":0,"public":0,"private_skipped":0,"archived_skipped":0,"exists":0,"created":0,"failed":0,"dry_run":0}
    for repo in repos(args.owner):
        counts["observed"]+=1
        if repo.get("private") or repo.get("visibility")!="public":
            counts["private_skipped"]+=1;continue
        counts["public"]+=1
        if repo.get("archived") and not args.include_archived:
            counts["archived_skipped"]+=1;continue
        name=repo["full_name"];path=".well-known/cvd.json"
        try:
            existing=subprocess.run(["gh","api",f"/repos/{name}/contents/{path}"],capture_output=True,text=True)
            if existing.returncode==0:
                counts["exists"]+=1;continue
            # A genuine HTTP 404 is different from permissions or network failure.
            if "HTTP 404" not in existing.stderr and "404 Not Found" not in existing.stderr:
                raise RuntimeError("Cannot establish pointer absence: "+existing.stderr.strip()[:150])
            if not args.apply:
                counts["dry_run"]+=1;continue
            branch=repo["default_branch"]
            # gh api takes raw JSON; GitHub Contents API expects base64 text.
            import base64
            payload={"message":"CVD: link public provenance registry","content":base64.b64encode(pointer(name).encode()).decode(),"branch":branch}
            cp=subprocess.run(["gh","api","--method","PUT",f"/repos/{name}/contents/{path}","--input","-"],input=json.dumps(payload),text=True,capture_output=True)
            if cp.returncode: raise RuntimeError(cp.stderr.strip())
            counts["created"]+=1
        except Exception as exc:
            counts["failed"]+=1
            print(json.dumps({"repo":name,"error":str(exc)[:160]}),file=sys.stderr)
        if args.limit and counts["public"]>=args.limit: break
        if args.apply: time.sleep(0.2)
    print(json.dumps(counts,indent=2))
if __name__=="__main__":main()
