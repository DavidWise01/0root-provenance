#!/usr/bin/env python3
"""CVD-028 external Git witness: validate repository numeric ID and commit existence.
Read-only; does not establish copyright, authorship, priority, or genuine fork ancestry.
"""
import datetime,json,re,subprocess,sys
from pathlib import Path
REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA=re.compile(r"^[0-9a-f]{40}$")
def github(path):
    p=subprocess.run(["gh","api",path],capture_output=True,text=True,timeout=30)
    if p.returncode: raise RuntimeError("GitHub inaccessible: "+p.stderr.strip()[:160])
    return json.loads(p.stdout)
def attest(event,fetch=github):
    name=event.get("repository_full_name");rid=event.get("github_repository_id");sha=event.get("observed_commit")
    if not isinstance(name,str) or not REPO.fullmatch(name):return {"status":"REJECT","reason":"invalid repository"}
    if type(rid)!=int or rid<=0:return {"status":"REJECT","reason":"invalid numeric repository ID"}
    if not isinstance(sha,str) or not SHA.fullmatch(sha):return {"status":"REJECT","reason":"invalid SHA"}
    try:
        meta=fetch("/repos/"+name)
        if meta.get("id")!=rid:return {"status":"REJECT","reason":"repository identity mismatch"}
        if meta.get("full_name")!=name:return {"status":"HOLD","reason":"locator changed; continuity event needed"}
        c=fetch("/repos/"+name+"/commits/"+sha)
        if c.get("sha")!=sha:return {"status":"REJECT","reason":"commit mismatch"}
        url="https://github.com/"+name+"/commit/"+sha
        if c.get("html_url")!=url:return {"status":"HOLD","reason":"unexpected commit URL"}
        return {"status":"VERIFIED","github_repository_id":rid,"repository":name,
                "commit":sha,"commit_url":url,
                "observed_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "scope":"repository identity and commit existence"}
    except (RuntimeError,ValueError,TypeError,KeyError,subprocess.TimeoutExpired):
        return {"status":"HOLD","reason":"GitHub evidence unavailable"}
def verify_events(events,fetch=github):
    results=[attest(e,fetch) for e in events]
    return {"schema":"CVD-GITHUB-ATTESTATION-v1","results":results,
            "counts":{s:sum(r["status"]==s for r in results) for s in ("VERIFIED","HOLD","REJECT")}}
if __name__=="__main__":
    from continuity import check
    events=json.loads(Path(sys.argv[1]).read_text())["events"]
    errors=check(events)
    outcome={"status":"REJECT","errors":errors} if errors else verify_events(events)
    print(json.dumps(outcome,indent=2))
    sys.exit(bool(errors) or outcome["counts"]["VERIFIED"]!=len(events))
