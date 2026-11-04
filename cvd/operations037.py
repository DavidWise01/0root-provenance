#!/usr/bin/env python3
"""CVD-037: retrospective GitHub Actions operational receipts.
Only previously completed runs; workflow configuration is not a success claim.
"""
import argparse, datetime, hashlib, json, os, re, sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SCHEMA="CVD-OPERATIONAL-RECEIPT-037-v1"
WORKFLOW="cvd-formic-031.yml"
REPO="DavidWise01/0root-provenance"
HEX40=re.compile(r"^[0-9a-f]{40}$")

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def receipt(run):
    if run.get("status")!="completed":
        return None
    run_id=run.get("id")
    attempt=run.get("run_attempt")
    name=run.get("name")
    sha=run.get("head_sha")
    event=run.get("event")
    repo=(run.get("repository") or {}).get("full_name")
    url=run.get("html_url")
    conclusion=run.get("conclusion")
    if (type(run_id)!=int or run_id<=0 or type(attempt)!=int or attempt<=0
        or not isinstance(sha,str) or not HEX40.fullmatch(sha)
        or repo!=REPO or name!="FORMIC CVD - Six Witness Git Perimeter"
        or event not in ("schedule","workflow_dispatch")
        or conclusion not in ("success","failure","cancelled","timed_out","action_required","neutral","skipped","stale")
        or not isinstance(url,str)
        or not url.startswith("https://github.com/"+REPO+"/actions/runs/"+str(run_id))):
        raise ValueError("Invalid completed run metadata")
    r={"schema":SCHEMA,"run_id":run_id,"run_attempt":attempt,"repository":repo,
       "workflow":WORKFLOW,"event":event,"head_sha":sha,"conclusion":conclusion,
       "result":"REPORTED_SUCCESS" if conclusion=="success" else "REPORTED_NON_SUCCESS",
       "run_url":url,"created_at":run.get("created_at"),
       "updated_at":run.get("updated_at"),
       "source":"GitHub Actions REST run metadata",
       "scope":"Previously completed workflow run; GitHub-reported conclusion, not independent verification of Git observations"}
    r["record_sha256"]=canonical_hash(r)
    return r

class API:
    def __init__(self,token=None):
        self.token=token or os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    def runs(self):
        headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"FORMIC-CVD-037"}
        if self.token:headers["Authorization"]="Bearer "+self.token
        path="/repos/"+REPO+"/actions/workflows/"+WORKFLOW+"/runs?per_page=100"
        try:
            with urlopen(Request("https://api.github.com"+path,headers=headers),timeout=30) as response:
                data=json.load(response)
        except (HTTPError,URLError,TimeoutError,ValueError) as error:
            raise RuntimeError("GitHub workflow metadata unavailable") from error
        if not isinstance(data,dict) or not isinstance(data.get("workflow_runs"),list):
            raise RuntimeError("Invalid workflow run listing")
        return data["workflow_runs"]

def plan(root,runs,current_run_id=None):
    if current_run_id is not None and (type(current_run_id)!=int or current_run_id<=0):
        raise ValueError("Invalid current run id")
    folder=Path(root)/"cvd"/"operations"/"github-actions"
    new=[];seen=set();counts={"completed":0,"incomplete":0,"already_recorded":0,"new":0}
    for run in runs:
        if current_run_id is not None and run.get("id")==current_run_id:continue
        r=receipt(run)
        if r is None:
            counts["incomplete"]+=1;continue
        counts["completed"]+=1
        key=(r["run_id"],r["run_attempt"])
        if key in seen:continue
        seen.add(key)
        path=folder/(f"{r['run_id']}-{r['run_attempt']}.json")
        if path.exists():
            old=json.loads(path.read_text(encoding="utf-8"))
            if old!=r or old.get("record_sha256")!=canonical_hash({k:v for k,v in old.items() if k!="record_sha256"}):
                raise ValueError("Operational receipt changed: "+str(path))
            counts["already_recorded"]+=1
        else:
            new.append((path,r));counts["new"]+=1
    # Also check all prior saved receipts, including those not in the API's latest-100 window.
    if folder.exists():
        for path in folder.glob("*.json"):
            old=json.loads(path.read_text(encoding="utf-8"))
            if (old.get("schema")!=SCHEMA or old.get("record_sha256")!=canonical_hash(
                {k:v for k,v in old.items() if k!="record_sha256"})
                or path.name!=f"{old.get('run_id')}-{old.get('run_attempt')}.json"):
                raise ValueError("Previously saved receipt corrupt: "+str(path))
    return new,counts

def apply(records):
    files=[]
    for path,r in records:
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open("x",encoding="utf-8") as file:
            json.dump(r,file,indent=2);file.write("\n")
        files.append(str(path))
    return files

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--apply",action="store_true")
    p.add_argument("--current-run-id",type=int,default=None)
    args=p.parse_args()
    try:
        records,counts=plan(args.root,API().runs(),args.current_run_id)
        paths=apply(records) if args.apply else []
        print(json.dumps({"status":"PASS","mode":"apply" if args.apply else "dry_run",
                          "counts":counts,"files":paths},indent=2))
        return 0
    except (OSError,RuntimeError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({"status":"HOLD","reason":str(error)}),file=sys.stderr)
        return 2
if __name__=="__main__":sys.exit(main())
