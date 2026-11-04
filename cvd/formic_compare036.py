#!/usr/bin/env python3
"""Jane's non-voting comparison view of six append-only FORMIC witness channels."""
import argparse,hashlib,json,sys
from pathlib import Path
from collect031 import history
ROLES=("ff","fr","cf","cr","rf","rr")
def fingerprint(state):
    return hashlib.sha256(json.dumps(state,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def compare(root):
    by_repo={};count=0;active=[]
    for role in ROLES:
        rows=history(root,role)
        if rows:active.append(role)
        count+=len(rows)
        for r in rows:by_repo.setdefault(r["github_repository_id"],{})[role]=r
    states=[]
    for rid,by_role in sorted(by_repo.items()):
        snapshots=[{"observer":role,"commit":r["commit"],"repository":r["repository"],
          "observed_utc":r["observed_utc"],"witness_sha256":r["record_sha256"]}
          for role,r in sorted(by_role.items())]
        heads={s["commit"] for s in snapshots}
        status="SINGLE_CHANNEL" if len(snapshots)==1 else "HEADS_DIFFER" if len(heads)>1 else "HEADS_MATCH"
        states.append({"github_repository_id":rid,"status":status,
                       "witnesses":snapshots,"decision":None})
    state={"schema":"CVD-FORMIC-COMPARISON-036-v1","active_channels":active,
           "total_observations":count,"repositories":states,"quorum":None,
           "warning":"Different heads can reflect different observation times; no voting or title claim."}
    state["snapshot_sha256"]=fingerprint(state)
    return state
def publish(root,view):
    path=Path(root)/"cvd"/"reports"/("formic-"+view["snapshot_sha256"]+".json")
    if path.exists():
        if json.loads(path.read_text(encoding="utf-8"))!=view:
            raise ValueError("Report integrity mismatch")
        return None
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("x",encoding="utf-8") as f:json.dump(view,f,indent=2);f.write("\n")
    return str(path)
def main():
    p=argparse.ArgumentParser();p.add_argument("--root",default=".");p.add_argument("--apply",action="store_true");a=p.parse_args()
    try:
        state=compare(a.root);path=publish(a.root,state) if a.apply else None
        print(json.dumps({"status":"PASS","active_channels":state["active_channels"],
            "total_observations":state["total_observations"],
            "snapshot_sha256":state["snapshot_sha256"],"written_file":path},indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError) as e:
        print(json.dumps({"status":"HOLD","error":str(e)}),file=sys.stderr);return 2
if __name__=="__main__":sys.exit(main())
