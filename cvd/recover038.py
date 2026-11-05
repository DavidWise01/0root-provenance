#!/usr/bin/env python3
"""CVD 038: fail-closed recovery from interrupted FORMIC publication.
No witness votes; existing records never overwritten or silently deleted.
"""
import argparse,datetime as dt,json,os,re,sys,tempfile
from pathlib import Path
from collect031 import history
from reconcile033 import read as temporal_read, plan as temporal_plan
from formic036 import ROLES,inspect_existing,evidence_path,causal_evidence
from closure035 import GitHubReader
SHA64=re.compile(r"^[0-9a-f]{64}$")
ANCHOR="CVD-RECOVERY-ANCHOR-038-v1"

def check_anchor(chains, anchor):
    if anchor is None:return
    if not isinstance(anchor,dict) or anchor.get("schema")!=ANCHOR or not isinstance(anchor.get("channels"),dict):
        raise ValueError("Invalid recovery anchor")
    for role, pin in anchor["channels"].items():
        if role not in ROLES or not isinstance(pin,dict):raise ValueError("Invalid checkpoint channel")
        count=pin.get("count");head=pin.get("head_record_sha256")
        if type(count)!=int or count<0 or (count and (not isinstance(head,str) or not SHA64.fullmatch(head))) or (not count and head is not None):
            raise ValueError("Invalid checkpoint fields")
        items=chains[role]
        if count>len(items) or (count and items[count-1]["record_sha256"]!=head):
            raise ValueError("Trusted checkpoint divergence for "+role)

def preflight(root,anchor=None):
    chains={};needs_temporal={};needs_causal={};counts={}
    for role in ROLES:
        rows=history(root,role)
        existing=temporal_read(root,role,True)
        # Validates overlay-to-source references and append ordering without writing.
        source={r["record_sha256"]:r for r in rows}
        linked=set()
        for entry in existing:
            h=entry["source_witness_sha256"]
            if h in linked or h not in source:raise ValueError("Temporal source mismatch for "+role)
            linked.add(h);s=source[h]
            if (entry["commit"],entry["github_repository_id"],entry["repository"],entry["observed_at_utc"]) != (s["commit"],s["github_repository_id"],s["repository"],s["observed_utc"]):
                raise ValueError("Temporal source identity mismatch for "+role)
        inspect_existing(root,rows,role)
        chains[role]=rows
        needs_temporal[role]=[r for r in rows if r["record_sha256"] not in linked]
        needs_causal[role]=[r for r in rows if not evidence_path(root,r).exists()]
        counts[role]={"observations":len(rows),"temporal_missing":len(needs_temporal[role]),"causal_missing":len(needs_causal[role])}
    check_anchor(chains,anchor)
    return chains,needs_temporal,needs_causal,counts

def atomic_create(path,data):
    """Write complete JSON to a temp file then hard-link exclusively into final path."""
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp_path=None
    try:
        with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",dir=path.parent,prefix=".cvd038-",suffix=".tmp",delete=False) as f:
            temp_path=Path(f.name)
            json.dump(data,f,indent=2,ensure_ascii=False);f.write("\n");f.flush();os.fsync(f.fileno())
        os.link(temp_path,path)  # EEXIST prevents overwriting any prior record.
    finally:
        if temp_path is not None:temp_path.unlink(missing_ok=True)
    return str(path)

def recover(root,reader=None,*,apply=False,max_closures=12,anchor=None,clock=None):
    if type(max_closures)!=int or max_closures<0:raise ValueError("Invalid causal budget")
    chains,missing_temporal,missing_causal,counts=preflight(root,anchor)
    total_temporal=sum(map(len,missing_temporal.values()))
    total_causal=sum(map(len,missing_causal.values()))
    if not apply:
        return {"status":"RECOVERABLE" if total_temporal or total_causal else "CLEAN",
                "mode":"dry_run","channels":counts,"temporal_pending":total_temporal,
                "causal_pending":total_causal,"written_files":[]}
    stamp=clock or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    # Complete preflight before modifying any channel.
    temporal_plans={}
    for role in ROLES:temporal_plans[role]=temporal_plan(root,role,stamp)
    written=[]
    for role in ROLES:
        for record in temporal_plans[role]:
            path=Path(root)/"cvd"/"temporal"/role/(f"{record['sequence']:09d}-{record['record_sha256']}.json")
            written.append(atomic_create(path,record))
    remaining=max_closures
    reader=reader or GitHubReader()
    for role in ROLES:
        for row in missing_causal[role]:
            if not remaining:break
            target=evidence_path(root,row)
            written.append(atomic_create(target,causal_evidence(row,reader,max_nodes=12,max_depth=5,clock=stamp)))
            remaining-=1
    # Detect and refuse a post-repair mismatch before claiming completion.
    _,_,_,after=preflight(root,anchor)
    backlog=sum(v["causal_missing"] for v in after.values())
    return {"status":"RECOVERABLE" if backlog else "CLEAN","mode":"apply",
            "channels":after,"temporal_pending":sum(v["temporal_missing"] for v in after.values()),
            "causal_pending":backlog,"written_files":written,
            "checkpoint_provided":anchor is not None}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--checkpoint",help="Separately retained trusted checkpoint JSON")
    p.add_argument("--max-closures",type=int,default=12)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    try:
        anchor=json.loads(Path(a.checkpoint).read_text(encoding="utf-8")) if a.checkpoint else None
        result=recover(a.root,apply=a.apply,max_closures=a.max_closures,anchor=anchor)
        print(json.dumps(result,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as error:
        print(json.dumps({"status":"HOLD","error":str(error)}),file=sys.stderr)
        return 2
if __name__=="__main__":sys.exit(main())
