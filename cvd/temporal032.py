#!/usr/bin/env python3
"""CVD 032: append-only temporal overlay; neither clock claims nor Git events are independently authenticated."""
from datetime import datetime
import hashlib,json,re,sys
from pathlib import Path
SCHEMA="CVD-TEMPORAL-032-v1"
ROLES={"ff","fr","cf","cr","rf","rr"}
def utc(s):
    if not isinstance(s,str) or not s.endswith("Z"): raise ValueError("UTC timestamp required")
    return datetime.fromisoformat(s[:-1]+"+00:00")
def digest(r):
    return hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!="record_sha256"},sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def make(witness,sequence,prior,source,repo_id,repository,commit,observed_at,appended_at,outcome="OBSERVED",event_at=None):
    r=dict(schema=SCHEMA,witness_id=witness,sequence=sequence,previous_record_sha256=prior,source_witness_sha256=source,github_repository_id=repo_id,repository=repository,commit=commit,observed_at_utc=observed_at,appended_at_utc=appended_at,event_at_utc=event_at,outcome=outcome)
    r["record_sha256"]=digest(r);return r
def validate(records):
    errors=[];last={};seen=set()
    for i,r in enumerate(records):
        tag=f"record[{i}]";w=r.get("witness_id");prior=last.get(w)
        if r.get("schema")!=SCHEMA or w not in ROLES: errors.append(tag+":schema/witness")
        if type(r.get("sequence")) is not int or r["sequence"]!=(prior["sequence"]+1 if prior else 0):errors.append(tag+":sequence")
        if r.get("previous_record_sha256")!=(prior["record_sha256"] if prior else None):errors.append(tag+":link")
        if type(r.get("github_repository_id")) is not int or r["github_repository_id"]<=0:errors.append(tag+":repo_id")
        if not isinstance(r.get("repository"),str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",r["repository"]):errors.append(tag+":repository")
        if not isinstance(r.get("commit"),str) or not re.fullmatch(r"[0-9a-f]{40}",r["commit"]):errors.append(tag+":commit")
        if not isinstance(r.get("source_witness_sha256"),str) or not re.fullmatch(r"[0-9a-f]{64}",r["source_witness_sha256"]):errors.append(tag+":source")
        if r.get("outcome") not in ("OBSERVED","VERIFIED","HOLD","REJECT"):errors.append(tag+":outcome")
        try:
            observed=utc(r.get("observed_at_utc"));appended=utc(r.get("appended_at_utc"))
            if r.get("event_at_utc") is not None:utc(r["event_at_utc"])
            if appended<observed:errors.append(tag+":append_before_observe")
            if prior and appended<utc(prior["appended_at_utc"]):errors.append(tag+":append_regression")
        except (ValueError,TypeError):errors.append(tag+":timestamp")
        h=r.get("record_sha256")
        if h!=digest(r) or h in seen:errors.append(tag+":integrity")
        if isinstance(h,str):seen.add(h)
        if w in ROLES:last[w]=r
    return errors
def compare(records,repo_id):
    errors=validate(records)
    if errors:return {"status":"INVALID","errors":errors}
    rows=sorted((r for r in records if r["github_repository_id"]==repo_id),key=lambda r:(utc(r["observed_at_utc"]),r["witness_id"],r["sequence"]))
    if not rows:return {"status":"NO_OBSERVATIONS","repository_id":repo_id}
    by_time={}
    for r in rows:by_time.setdefault(r["observed_at_utc"],set()).add((r["commit"],r["outcome"]))
    conflicts=[t for t,states in by_time.items() if len(states)>1]
    all_states={(r["commit"],r["outcome"]) for r in rows}
    state="SAME_TIME_DIVERGENCE" if conflicts else "TEMPORAL_VARIATION" if len(all_states)>1 else "CONSISTENT_OBSERVATIONS"
    return {"schema":"CVD-TIMELINE-032-v1","status":state,"observations":rows,"same_timestamp_divergence":conflicts,"decision":"NONE","quorum":None}
if __name__=="__main__":
    rows=json.loads(Path(sys.argv[1]).read_text())["records"]
    result=compare(rows,int(sys.argv[2])) if len(sys.argv)>2 else {"errors":validate(rows)}
    print(json.dumps(result,indent=2));sys.exit(bool(result.get("errors") or result.get("status")=="INVALID"))
