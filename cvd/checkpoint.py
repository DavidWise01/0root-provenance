#!/usr/bin/env python3
"""Verify CVD chain against an independently retained checkpoint."""
import argparse,json,sys
from pathlib import Path
from continuity import check

def create_checkpoint(events):
    errors=check(events)
    if errors: raise ValueError("Invalid chain: "+str(errors[:3]))
    return {"schema":"CVD-CHECKPOINT-v1","event_count":len(events),
            "head_record_sha256":events[-1]["record_sha256"] if events else None}

def verify_checkpoint(events,checkpoint):
    errors=check(events)
    if checkpoint.get("schema")!="CVD-CHECKPOINT-v1":errors.append("invalid checkpoint schema")
    if checkpoint.get("event_count")!=len(events):errors.append("checkpoint length mismatch")
    if checkpoint.get("head_record_sha256")!=(events[-1]["record_sha256"] if events else None):
        errors.append("checkpoint tip mismatch")
    return errors

def main():
    p=argparse.ArgumentParser()
    p.add_argument("ledger",help="JSON with events[]")
    p.add_argument("--checkpoint")
    p.add_argument("--write-checkpoint")
    args=p.parse_args()
    events=json.loads(Path(args.ledger).read_text())["events"]
    if args.checkpoint:
        errors=verify_checkpoint(events,json.loads(Path(args.checkpoint).read_text()))
        print(json.dumps({"status":"PASS" if not errors else "FAIL","errors":errors},indent=2))
        return int(bool(errors))
    if args.write_checkpoint:
        cp=create_checkpoint(events)
        Path(args.write_checkpoint).write_text(json.dumps(cp,indent=2)+"\n")
        print("Checkpoint written. Retain independently to make future rewrites detectable.")
        return 0
    p.error("Supply --checkpoint or --write-checkpoint")
if __name__=="__main__":sys.exit(main())
