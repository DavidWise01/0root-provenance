#!/usr/bin/env python3
"""CVD-030: append-only, non-voting Git witness observations and divergence analysis.
Records are claims, not independently authenticated GitHub evidence.
"""
import argparse, hashlib, json, re, sys
from pathlib import Path
SHA40=re.compile(r"^[0-9a-f]{40}$")
REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ROLES=("ff","fr","cf","cr","rf","rr")
SCHEMA="CVD-WITNESS-030-v1"
def digest(record):
    raw=json.dumps({k:v for k,v in record.items() if k!="record_sha256"},sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
def observation(*,event_id,witness_id,sequence,prev_sha,repo_id,repository,commit,observed_utc,outcome,details=None):
    record={"schema":SCHEMA,"event_id":event_id,"witness_id":witness_id,
      "sequence":sequence,"previous_record_sha256":prev_sha,
      "github_repository_id":repo_id,"repository":repository,"commit":commit,
      "observed_utc":observed_utc,"outcome":outcome,"details":details or {}}
    record["record_sha256"]=digest(record)
    return record
def validate(records):
    errors=[];by_witness={};seen_hashes=set()
    for i,r in enumerate(records):
        tag=f"record[{i}]";w=r.get("witness_id")
        if r.get("schema")!=SCHEMA:errors.append(tag+":schema")
        if w not in ROLES:errors.append(tag+":witness")
        if not isinstance(r.get("event_id"),str) or not r["event_id"].strip():errors.append(tag+":event_id")
        if type(r.get("github_repository_id")) is not int or r["github_repository_id"]<=0:errors.append(tag+":repository_id")
        name=r.get("repository")
        if not isinstance(name,str) or not REPO.fullmatch(name):errors.append(tag+":repository")
        sha=r.get("commit")
        if not isinstance(sha,str) or not SHA40.fullmatch(sha):errors.append(tag+":commit")
        if not isinstance(r.get("observed_utc"),str) or not r["observed_utc"].endswith("Z"):errors.append(tag+":timestamp")
        if r.get("outcome") not in ("VERIFIED","HOLD","REJECT","OBSERVED"):errors.append(tag+":outcome")
        if not isinstance(r.get("details"),dict):errors.append(tag+":details")
        previous=by_witness.get(w)
        if type(r.get("sequence")) is not int or r["sequence"]!=(previous[0]+1 if previous else 0):errors.append(tag+":sequence")
        if r.get("previous_record_sha256")!=(previous[1] if previous else None):errors.append(tag+":previous_hash")
        signed=r.get("record_sha256")
        if signed!=digest(r) or signed in seen_hashes:errors.append(tag+":integrity")
        if isinstance(signed,str):seen_hashes.add(signed)
        if w in ROLES:by_witness[w]=(r.get("sequence"),signed)
    return errors
def compare(records,event_id):
    errors=validate(records)
    if errors:return {"status":"INVALID","errors":errors}
    latest={}
    for r in records:
        if r["event_id"]==event_id:latest[r["witness_id"]]=r
    if not latest:return {"status":"NO_OBSERVATIONS","event_id":event_id}
    snapshots=[{"witness":w,"repository_id":r["github_repository_id"],"repository":r["repository"],"commit":r["commit"],
      "outcome":r["outcome"],"observed_utc":r["observed_utc"],"record_sha256":r["record_sha256"]}
      for w,r in sorted(latest.items())]
    targets={(r["github_repository_id"],r["commit"]) for r in latest.values()}
    outcomes={r["outcome"] for r in latest.values()}
    state="DIFFERENT_TARGETS" if len(targets)>1 else "DIVERGENT_REPORTS" if len(outcomes)>1 else "CONSISTENT_REPORTS"
    return {"schema":"CVD-COMPARISON-030-v1","event_id":event_id,"state":state,
      "observed_witnesses":len(latest),"statements":snapshots,"decision":"NONE","quorum":None,
      "meaning":"Agreement is not proof; divergence is retained evidence."}
def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest="cmd",required=True)
    v=sub.add_parser("validate");v.add_argument("ledger")
    c=sub.add_parser("compare");c.add_argument("ledger");c.add_argument("event_id")
    a=p.parse_args()
    ledger=json.loads(Path(a.ledger).read_text(encoding="utf-8"))["records"]
    errors=validate(ledger)
    output={"status":"PASS" if not errors else "FAIL","errors":errors,"count":len(ledger)} if a.cmd=="validate" else compare(ledger,a.event_id)
    print(json.dumps(output,indent=2))
    return 2 if output.get("status") in ("FAIL","INVALID") else 0
if __name__=="__main__":sys.exit(main())
