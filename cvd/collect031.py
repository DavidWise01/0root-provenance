#!/usr/bin/env python3
"""CVD-031: Git-only FORMIC observation collector. Dry-run unless --apply.
One configured observer; no synthetic witnesses; only public repositories.
"""
import argparse, datetime, hashlib, json, os, re, sys
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import quote
from urllib.error import HTTPError,URLError

SCHEMA="CVD-WITNESS-030-v1"
ROLES=("ff","fr","cf","cr","rf","rr")
SHA=re.compile(r"^[0-9a-f]{40}$")
REPO=re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")

def digest(record):
    value={k:v for k,v in record.items() if k!="record_sha256"}
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

class GitHubAPI:
    def __init__(self,token=None):
        self.token=token or os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
    def get(self,path):
        headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"FORMIC-CVD-031"}
        if self.token:headers["Authorization"]="Bearer "+self.token
        try:
            with urlopen(Request("https://api.github.com"+path,headers=headers),timeout=30) as response:
                return json.loads(response.read())
        except (HTTPError,URLError,TimeoutError,ValueError) as error:
            raise RuntimeError("GitHub unavailable: "+str(error)) from error

def public_repos(api,owner,start_page=1,max_pages=0):
    page=start_page
    while not max_pages or page<start_page+max_pages:
        found=api.get("/users/"+quote(owner)+"/repos?type=owner&per_page=100&page="+str(page))
        if not isinstance(found,list):raise RuntimeError("Invalid GitHub listing")
        if not found:return
        for repo in found:
            if repo.get("private") or repo.get("visibility")!="public":continue
            if repo.get("owner",{}).get("login","").casefold()!=owner.casefold():continue
            yield repo
        page+=1

def history(root,witness):
    directory=Path(root)/"cvd"/"observations"/witness
    records=[]
    for file in sorted(directory.glob("*.json")) if directory.exists() else []:
        record=json.loads(file.read_text(encoding="utf-8"))
        if record.get("schema")!=SCHEMA or record.get("witness_id")!=witness:
            raise ValueError("Invalid witness record")
        if type(record.get("sequence"))!=int or record["sequence"]!=len(records):
            raise ValueError("Discontinuous witness sequence")
        if record.get("previous_record_sha256")!=(records[-1]["record_sha256"] if records else None):
            raise ValueError("Broken witness chain")
        if record.get("record_sha256")!=digest(record):
            raise ValueError("Tampered witness record")
        if file.name!=f"{record['sequence']:09d}-{record['record_sha256']}.json":
            raise ValueError("Misnamed witness record")
        records.append(record)
    return records

def collect(api,root,owner,witness,start_page=1,max_pages=0,max_new=0,clock=None):
    if witness not in ROLES or not re.fullmatch(r"[A-Za-z0-9-]+",owner):
        raise ValueError("Invalid owner or witness")
    old=history(root,witness)
    latest={r["github_repository_id"]:r for r in old}
    prev=old[-1]["record_sha256"] if old else None
    seq=len(old)
    stamp=clock or datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    added=[];counts={"public_scanned":0,"unchanged":0,"created_candidate":0,"hold":0}
    for repo in public_repos(api,owner,start_page,max_pages):
        counts["public_scanned"]+=1
        name=repo.get("full_name");rid=repo.get("id");branch=repo.get("default_branch")
        if not isinstance(name,str) or not REPO.fullmatch(name) or type(rid)!=int or not branch:
            counts["hold"]+=1;continue
        try:
            commit=api.get("/repos/"+name+"/commits/"+quote(branch,safe=""))
        except RuntimeError:
            counts["hold"]+=1;continue
        sha=commit.get("sha") if isinstance(commit,dict) else None
        if not isinstance(sha,str) or not SHA.fullmatch(sha):
            counts["hold"]+=1;continue
        prior=latest.get(rid)
        if prior and prior["commit"]==sha and prior["repository"]==name:
            counts["unchanged"]+=1;continue
        record={"schema":SCHEMA,"event_id":"github-head:"+str(rid)+":"+sha,
            "witness_id":witness,"sequence":seq,"previous_record_sha256":prev,
            "github_repository_id":rid,"repository":name,"commit":sha,
            "observed_utc":stamp,"outcome":"VERIFIED",
            "details":{"source":"GitHub public repo and commit APIs","branch":branch,
                       "prior_record_sha256":prior["record_sha256"] if prior else None}}
        record["record_sha256"]=digest(record)
        added.append(record);latest[rid]=record;prev=record["record_sha256"];seq+=1
        counts["created_candidate"]+=1
        if max_new and len(added)>=max_new:break
    return added,counts

def append(root,records):
    paths=[]
    for record in records:
        folder=Path(root)/"cvd"/"observations"/record["witness_id"]
        folder.mkdir(parents=True,exist_ok=True)
        path=folder/f"{record['sequence']:09d}-{record['record_sha256']}.json"
        with path.open("x",encoding="utf-8") as output:
            json.dump(record,output,indent=2,ensure_ascii=False);output.write("\n")
        paths.append(str(path))
    return paths

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--owner",default="DavidWise01")
    p.add_argument("--observer",choices=ROLES,default="ff")
    p.add_argument("--start-page",type=int,default=1)
    p.add_argument("--max-pages",type=int,default=0)
    p.add_argument("--max-new",type=int,default=250)
    p.add_argument("--apply",action="store_true")
    args=p.parse_args(argv)
    try:
        if args.start_page<1 or args.max_pages<0 or args.max_new<0:raise ValueError("Invalid scan limits")
        rows,counts=collect(GitHubAPI(),args.root,args.owner,args.observer,args.start_page,args.max_pages,args.max_new)
        if counts["hold"]:
            print(json.dumps({"status":"HOLD","stats":counts,"reason":"Unobserved repositories; no files published"}))
            return 2
        paths=append(args.root,rows) if args.apply else []
        print(json.dumps({"status":"PASS","mode":"apply" if args.apply else "dry_run","counts":counts,
                          "new_paths":paths},indent=2))
        return 0
    except (RuntimeError,ValueError,OSError) as exc:
        print(json.dumps({"status":"FAIL","error":str(exc)}),file=sys.stderr)
        return 2
if __name__=="__main__":sys.exit(main())
