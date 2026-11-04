#!/usr/bin/env python3
"""CVD-029: read-only external-location checkpoint verifier. Requires 'gh auth login'."""
import json,re,subprocess,sys
from pathlib import Path
HEX40=re.compile(r"^[0-9a-f]{40}$")
def api(path):
    p=subprocess.run(["gh","api",path],capture_output=True,text=True,timeout=30)
    if p.returncode: raise RuntimeError(p.stderr.strip()[:250])
    return json.loads(p.stdout)
def verify(w,lookup=api,current=False):
    issues=[]
    src=w.get("source") or {}
    repo=src.get("repository");commit=src.get("commit");path=src.get("path");blob=src.get("git_blob_sha")
    if w.get("schema")!="CVD-REMOTE-CHECKPOINT-v1":issues.append("invalid schema")
    if not isinstance(repo,str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",repo):issues.append("invalid repo")
    if not isinstance(path,str) or path.startswith("/") or ".." in path.split("/"):issues.append("invalid file path")
    if not isinstance(commit,str) or not HEX40.fullmatch(commit):issues.append("invalid commit")
    if not isinstance(blob,str) or not HEX40.fullmatch(blob):issues.append("invalid blob")
    if w.get("witness_repository")==repo:issues.append("witness is not external")
    if issues:return {"status":"REJECT","issues":issues}
    try:
        meta=lookup("/repos/"+repo)
        if meta.get("id")!=src.get("github_repository_id"):issues.append("repository ID mismatch")
        observed=lookup("/repos/"+repo+"/contents/"+path+"?ref="+commit)
        if observed.get("type")!="file" or observed.get("sha")!=blob:issues.append("anchored blob mismatch")
        if current:
            present=lookup("/repos/"+repo+"/contents/"+path)
            if present.get("sha")!=blob:issues.append("current default-branch blob differs from checkpoint")
    except (RuntimeError,KeyError,ValueError,TypeError,subprocess.TimeoutExpired):
        return {"status":"HOLD","issues":["GitHub observation unavailable"]}
    return {"status":"REJECT" if issues else "VERIFIED","issues":issues,"checkpoint_id":w.get("checkpoint_id")}
if __name__=="__main__":
    doc=json.loads(Path(sys.argv[1]).read_text())
    outcome=verify(doc,current="--current" in sys.argv[2:])
    print(json.dumps(outcome,indent=2))
    sys.exit(0 if outcome["status"]=="VERIFIED" else 2)
