#!/usr/bin/env python3
"""FORMIC 036: public Git -> witness -> temporal overlay -> causal evidence.
One invocation is ONE process/observer; no fabricated independent observers.
"""
import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from collect031 import GitHubAPI, append as append_observations, collect, history
from reconcile033 import append as append_temporal, plan as plan_temporal, read as read_records
from closure035 import GitHubReader, closure, payload_digest

ROLES = ("ff", "fr", "cf", "cr", "rf", "rr")
HASH64 = re.compile(r"^[0-9a-f]{64}$")
SCHEMA = "CVD-FORMIC-CAUSAL-036-v1"

def evidence_path(root, record):
    h = record["record_sha256"]
    if not isinstance(h,str) or not HASH64.fullmatch(h):
        raise ValueError("invalid witness digest")
    return Path(root)/"cvd"/"causal"/record["witness_id"]/(h+".json")

def causal_evidence(record,reader,max_nodes=12,max_depth=5,clock=None):
    result=closure(record["repository"],record["commit"],reader,
                   max_nodes=max_nodes,max_depth=max_depth,observed_utc=clock)
    return {
        "schema":SCHEMA,
        "source_witness_sha256":record["record_sha256"],
        "witness_id":record["witness_id"],
        "github_repository_id":record["github_repository_id"],
        "repository":record["repository"],
        "commit":record["commit"],
        "causal_status":result["status"],
        "causal_digest_sha256":result["record_sha256"],
        "causal_result":result,
        "note":"GitHub API observation, not proof of ownership or signed independent attestation"
    }

def inspect_existing(root, records, witness=None):
    known=set()
    count=0
    for source in records:
        path=evidence_path(root,source)
        known.add(path.name)
        if not path.exists():continue
        evidence=json.loads(path.read_text(encoding="utf-8"))
        result=evidence.get("causal_result") or {}
        if (evidence.get("schema")!=SCHEMA
            or evidence.get("source_witness_sha256")!=source["record_sha256"]
            or evidence.get("witness_id")!=source["witness_id"]
            or evidence.get("github_repository_id")!=source["github_repository_id"]
            or evidence.get("repository")!=source["repository"]
            or evidence.get("commit")!=source["commit"]
            or result.get("repository")!=source["repository"]
            or result.get("head")!=source["commit"]
            or evidence.get("causal_status")!=result.get("status")
            or evidence.get("causal_digest_sha256")!=result.get("record_sha256")
            or result.get("record_sha256")!=payload_digest(
                 {k:v for k,v in result.items() if k!="record_sha256"})):
            raise ValueError("causal integrity mismatch: "+str(path))
        count+=1
    folder=Path(root)/"cvd"/"causal"/(witness or (records[0]["witness_id"] if records else "ff"))
    if folder.exists():
        for path in folder.glob("*.json"):
            if path.name not in known:raise ValueError("orphan causal record: "+str(path))
    return count

def execute(root,owner,witness,api,reader,*,apply=False,max_new=120,
            max_closures=12,max_nodes=12,max_depth=5,clock=None):
    if witness not in ROLES:raise ValueError("unrecognized FORMIC witness")
    if not all(type(v)==int and v>=0 for v in (max_new,max_closures,max_nodes,max_depth)):
        raise ValueError("invalid budget")
    if max_nodes<1 or max_new<1:raise ValueError("zero scan/node budget")
    stamp=clock or dt.datetime.now(dt.timezone.utc).isoformat(
        timespec="seconds").replace("+00:00","Z")
    old=history(root,witness)
    read_records(root,witness,True)
    causal_known=inspect_existing(root,old,witness)
    candidates,stats=collect(api,root,owner,witness,max_new=max_new,clock=stamp)
    if stats["hold"]:
        return {"status":"HOLD","phase":"collection","counts":stats,
                "written":0,"message":"Incomplete Git observation; publishing withheld"}
    if not apply:
        return {"status":"PASS","mode":"dry_run","observer":witness,"counts":stats,
                "pending_observations":len(candidates),
                "existing_causal_sidecars":causal_known,"written":0}
    observation_files=append_observations(root,candidates)
    temporal_files=append_temporal(root,witness,plan_temporal(root,witness,stamp))
    causal_files=[];backlog=0
    for row in history(root,witness):
        target=evidence_path(root,row)
        if target.exists():continue
        if len(causal_files)>=max_closures:
            backlog+=1
            continue
        evidence=causal_evidence(row,reader,max_nodes,max_depth,stamp)
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("x",encoding="utf-8") as handle:
            json.dump(evidence,handle,indent=2);handle.write("\n")
        causal_files.append(str(target))
    return {"status":"PASS","mode":"apply","observer":witness,"counts":stats,
            "observation_files":observation_files,"temporal_files":temporal_files,
            "causal_files":causal_files,"causal_backlog":backlog,
            "causal_scope":"bounded GitHub API parent traversal, not legal authorship proof"}

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--owner",default="DavidWise01")
    p.add_argument("--observer",choices=ROLES,default="ff")
    p.add_argument("--max-new",type=int,default=120)
    p.add_argument("--max-closures",type=int,default=12)
    p.add_argument("--max-nodes",type=int,default=12)
    p.add_argument("--max-depth",type=int,default=5)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args(argv)
    try:
        result=execute(a.root,a.owner,a.observer,GitHubAPI(),GitHubReader(),
            apply=a.apply,max_new=a.max_new,max_closures=a.max_closures,
            max_nodes=a.max_nodes,max_depth=a.max_depth)
        print(json.dumps(result,indent=2))
        return 0 if result["status"]=="PASS" else 2
    except (ValueError,OSError,RuntimeError,KeyError,TypeError) as error:
        print(json.dumps({"status":"HOLD","error":str(error)}),file=sys.stderr)
        return 2
if __name__=="__main__":sys.exit(main())
