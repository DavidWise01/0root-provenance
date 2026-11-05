#!/usr/bin/env python3
"""CVD 039 external recovery anchor: compare an independently pinned checkpoint.
No quorum. A hash anchored only in the same mutable repository is NOT independent.
"""
import argparse,hashlib,json,os,re,sys
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from recover038 import ANCHOR,preflight

SHA256=re.compile(r"^[0-9a-f]{64}$")
GITSHA=re.compile(r"^[0-9a-f]{40}$")
MAX_BYTES=262144

def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n").encode("utf-8")

def snapshot(root):
    """Construct a checkpoint from verified local witness chains, without writing."""
    chains,_,_,_=preflight(root)
    return {"schema":ANCHOR,"channels":{
        role:{"count":len(rows),"head_record_sha256":rows[-1]["record_sha256"] if rows else None}
        for role,rows in sorted(chains.items())}}

def verify(root,anchor_bytes,expected_sha256):
    """Pinned SHA is supplied separately from the remote contents."""
    if not isinstance(expected_sha256,str) or not SHA256.fullmatch(expected_sha256):
        raise ValueError("Missing or malformed independent SHA256 pin")
    if len(anchor_bytes)>MAX_BYTES:raise ValueError("Anchor too large")
    actual=hashlib.sha256(anchor_bytes).hexdigest()
    if actual!=expected_sha256:
        return {"status":"HOLD","reason":"independent_anchor_digest_mismatch"}
    try:
        anchor=json.loads(anchor_bytes)
        if canonical(anchor)!=anchor_bytes:
            raise ValueError("Anchor not canonical JSON")
        if anchor.get("schema")!=ANCHOR or set(anchor.get("channels",{}))!=set(snapshot(root)["channels"]):
            raise ValueError("Wrong schema or channel set")
        from recover038 import check_anchor
        chains,_,_,_=preflight(root)
        check_anchor(chains,anchor)
    except (ValueError,TypeError,KeyError,UnicodeError,json.JSONDecodeError) as error:
        return {"status":"HOLD","reason":"anchor_or_local_lineage_invalid"}
    return {"status":"VERIFIED","anchor_sha256":actual,"channels":anchor["channels"],
            "meaning":"Prior checkpoint prefix is retained; NOT verification of full future head or legal authorship"}

def fetch(url):
    """Immutable revision in a separate GitHub repo; content digest still required."""
    parts=urlsplit(url)
    if (parts.scheme!="https" or parts.hostname!="raw.githubusercontent.com"
        or parts.username or parts.password or parts.query or parts.fragment):
        raise ValueError("Anchor must be a pinned raw.githubusercontent.com URL")
    pieces=parts.path.strip("/").split("/")
    if (len(pieces)<5 or pieces[0]!="DavidWise01" or
        pieces[1]!="attribution-standard" or not GITSHA.fullmatch(pieces[2])
        or pieces[3]!="cvd" or pieces[4]!="anchors" or
        any(p in ("","..",".") for p in pieces)):
        raise ValueError("Invalid immutable external anchor path")
    try:
        with urlopen(Request(url,headers={"User-Agent":"FORMIC-CVD-039"}),timeout=25) as response:
            data=response.read(MAX_BYTES+1)
        if len(data)>MAX_BYTES:raise ValueError("Anchor too large")
        return data
    except (HTTPError,URLError,TimeoutError) as error:
        raise RuntimeError("External anchor unavailable") from error

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    commands=p.add_mutually_exclusive_group(required=True)
    commands.add_argument("--emit",help="Exclusive-create a local canonical checkpoint for OUT-OF-BAND publication")
    commands.add_argument("--verify-url",help="Fetch pinned immutable external checkpoint URL")
    p.add_argument("--expected-sha256",help="Independent trusted SHA256 pin; may use CVD_EXTERNAL_ANCHOR_SHA256 env")
    args=p.parse_args(argv)
    try:
        if args.emit:
            data=canonical(snapshot(args.root))
            path=Path(args.emit);path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("xb") as handle:handle.write(data)
            result={"status":"GENERATED_UNTRUSTED","file":str(path),"sha256":hashlib.sha256(data).hexdigest(),
                    "instruction":"Retain independently. Publishing solely inside source Git cannot create trust."}
        else:
            pin=args.expected_sha256 or os.getenv("CVD_EXTERNAL_ANCHOR_SHA256")
            result=verify(args.root,fetch(args.verify_url),pin)
        print(json.dumps(result,indent=2))
        return 0 if result["status"] in ("VERIFIED","GENERATED_UNTRUSTED") else 2
    except (RuntimeError,ValueError,OSError,TypeError) as error:
        print(json.dumps({"status":"HOLD","reason":str(error)}),file=sys.stderr)
        return 2
if __name__=="__main__":sys.exit(main())
