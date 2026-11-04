#!/usr/bin/env python3
"""CVD-027 continuity verifier. Claims are not independently authenticated GitHub evidence."""
import hashlib,json,re,sys
from pathlib import Path
SHA=re.compile(r"^[0-9a-f]{40}$")
NAME=re.compile(r"^[\w.-]+/[\w.-]+$")
TYPES={"anchor","rename","transfer","fork","derive","archive","restore","delete_observed"}
def hash_record(e):
    data={k:v for k,v in e.items() if k!="record_sha256"}
    return hashlib.sha256(json.dumps(data,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def check(events):
    errors=[];identity={};seen=set()
    for i,e in enumerate(events):
        p=f"event[{i}]";kind=e.get("event");rid=e.get("github_repository_id")
        name=e.get("repository_full_name");commit=e.get("observed_commit")
        if e.get("schema")!="CVD-CONTINUITY-v1" or e.get("sequence")!=i: errors.append(p+": schema/sequence")
        if kind not in TYPES: errors.append(p+": event type")
        if type(rid)!=int or rid<=0: errors.append(p+": repository ID")
        if not isinstance(name,str) or not NAME.fullmatch(name): errors.append(p+": name")
        if not isinstance(commit,str) or not SHA.fullmatch(commit): errors.append(p+": commit")
        if e.get("previous_record_sha256")!=(events[i-1].get("record_sha256") if i else None): errors.append(p+": hash link")
        if e.get("record_sha256")!=hash_record(e) or e.get("record_sha256") in seen: errors.append(p+": integrity")
        seen.add(e.get("record_sha256"))
        if type(rid)!=int: continue
        old=identity.get(rid)
        if kind=="anchor":
            if old is not None: errors.append(p+": duplicate anchor")
            identity[rid]=name
        elif kind in ("fork","derive"):
            parent=e.get("parent_github_repository_id");psha=e.get("parent_commit")
            if parent not in identity or parent==rid: errors.append(p+": invalid parent")
            if not isinstance(psha,str) or not SHA.fullmatch(psha): errors.append(p+": parent commit")
            if rid in identity: errors.append(p+": already anchored")
            identity[rid]=name
        elif old is None: errors.append(p+": not anchored")
        elif kind in ("rename","transfer"):
            if old==name or e.get("previous_repository_full_name")!=old: errors.append(p+": rename history")
            identity[rid]=name
        elif old!=name: errors.append(p+": undeclared name change")
    return errors
if __name__=="__main__":
    events=json.loads(Path(sys.argv[1]).read_text())["events"]
    errors=check(events)
    print(json.dumps({"status":"PASS" if not errors else "FAIL","events":len(events),"errors":errors},indent=2))
    sys.exit(bool(errors))
