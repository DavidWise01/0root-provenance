#!/usr/bin/env python3
"""CVD 035: bounded read-only Git parent closure; not legal authorship proof."""
import argparse,hashlib,json,re,sys
from datetime import datetime,timezone
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
SHA=re.compile(r"^[0-9a-f]{40}$")
REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
def payload_digest(p):
 return hashlib.sha256(json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
class GitHubReader:
 def __init__(self,token=None):
  import os
  self.token=token if token is not None else (os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN"))
 def commit(self,repo,sha):
  headers={"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","User-Agent":"FORMIC-CVD-035"}
  if self.token:headers["Authorization"]="Bearer "+self.token
  try:
   with urlopen(Request(f"https://api.github.com/repos/{repo}/git/commits/{sha}",headers=headers),timeout=20) as response:return json.load(response)
  except (HTTPError,URLError,TimeoutError,ValueError) as error:raise RuntimeError(type(error).__name__) from error
def closure(repo,head,reader,max_nodes=200,max_depth=20,observed_utc=None):
 if not isinstance(repo,str) or not REPO.fullmatch(repo) or any(p in (".","..") for p in repo.split("/")):raise ValueError("Invalid repo")
 if not isinstance(head,str) or not SHA.fullmatch(head):raise ValueError("Invalid SHA")
 if type(max_nodes)!=int or max_nodes<1 or type(max_depth)!=int or max_depth<0:raise ValueError("Invalid bounds")
 pending=[(head,0)];nodes={};unresolved={};expanded=set()
 while pending:
  sha,depth=pending.pop(0)
  if sha in expanded:continue
  if depth>max_depth:unresolved[sha]="depth_limit";continue
  if len(nodes)>=max_nodes:unresolved[sha]="node_limit";continue
  try:
   data=reader.commit(repo,sha)
   if not isinstance(data,dict) or data.get("sha")!=sha:raise ValueError("commit mismatch")
   raw=data.get("parents")
   if not isinstance(raw,list):raise ValueError("missing parents")
   parents=[p.get("sha") if isinstance(p,dict) else None for p in raw]
   if any(not isinstance(p,str) or not SHA.fullmatch(p) for p in parents) or sha in parents or len(parents)!=len(set(parents)):raise ValueError("malformed ancestry")
  except (RuntimeError,ValueError,TypeError) as error:
   unresolved[sha]="unavailable" if isinstance(error,RuntimeError) else "malformed_or_mismatched";expanded.add(sha);continue
  nodes[sha]={"sha":sha,"parents":parents,"depth":depth};expanded.add(sha)
  for parent in parents:
   if parent not in expanded:pending.append((parent,depth+1))
 visited=set();visiting=set();cyclic=False
 for start in nodes:
  if start in visited:continue
  stack=[(start,False)]
  while stack:
   sha,finishing=stack.pop()
   if finishing:
    visiting.discard(sha);visited.add(sha);continue
   if sha in visiting:cyclic=True;break
   if sha in visited:continue
   visiting.add(sha);stack.append((sha,True))
   for p in reversed(nodes[sha]["parents"]):
    if p in nodes and p not in visited:stack.append((p,False))
  if cyclic:break
 status="REJECT" if cyclic else "HOLD" if unresolved else "VERIFIED"
 result={"schema":"CVD-CAUSAL-CLOSURE-035-v1","repository":repo,"head":head,"status":status,"max_nodes":max_nodes,"max_depth":max_depth,"observed_utc":observed_utc or datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"nodes":sorted(nodes.values(),key=lambda n:(n["depth"],n["sha"])),"unresolved":[{"sha":s,"reason":unresolved[s]} for s in sorted(unresolved)],"cycle_detected":cyclic,"decision":None,"quorum":None,"meaning":"GitHub-observed ancestry only; not proof of copyright ownership or historical originality"}
 result["record_sha256"]=payload_digest(result);return result
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("repository");p.add_argument("commit");p.add_argument("--max-nodes",type=int,default=200);p.add_argument("--max-depth",type=int,default=20);p.add_argument("--output");args=p.parse_args()
 r=closure(args.repository,args.commit,GitHubReader(),args.max_nodes,args.max_depth)
 data=json.dumps(r,indent=2)+"\n"
 if args.output:
  with open(args.output,"x") as f:f.write(data)
 else:print(data,end="")
 sys.exit(0 if r["status"]=="VERIFIED" else 2)
