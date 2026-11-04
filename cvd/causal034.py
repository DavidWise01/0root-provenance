#!/usr/bin/env python3
"""CVD 034: offline Git parentage versus observation-time audit.
Input Git edges require independent GitHub verification; timestamps do not establish causality.
"""
import datetime as dt,json,re,sys
from pathlib import Path
from collections import defaultdict
SHA=re.compile(r"^[0-9a-f]{40}$")
def when(value):
 if not isinstance(value,str) or not value.endswith("Z"):raise ValueError("UTC Z required")
 return dt.datetime.fromisoformat(value[:-1]+"+00:00")
def audit(commits,observations):
 errors=[];graph=defaultdict(dict);obs=[]
 for c in commits:
  rid=c.get("repo_id");sha=c.get("sha");parents=c.get("parents")
  if type(rid)!=int or rid<=0 or not isinstance(sha,str) or not SHA.fullmatch(sha) or not isinstance(parents,list) or any(not isinstance(p,str) or not SHA.fullmatch(p) for p in parents):errors.append("invalid commit");continue
  if sha in graph[rid] or sha in parents:errors.append("duplicate/self-parent");continue
  try:
   for field in ("author_at_utc","committer_at_utc"):
    if c.get(field) is not None:when(c[field])
  except ValueError:errors.append("invalid Git timestamp")
  graph[rid][sha]=c
 for o in observations:
  try:
   if type(o.get("repo_id"))!=int or not isinstance(o.get("sha"),str) or not SHA.fullmatch(o["sha"]):raise ValueError("invalid observation identity")
   if when(o["appended_at_utc"])<when(o["observed_at_utc"]):raise ValueError("append before observation")
   obs.append(o)
  except (KeyError,ValueError):errors.append("invalid observation")
 if errors:return {"status":"INVALID","errors":errors}
 for rid,nodes in graph.items():
  mark={}
  def visit(sha):
   if mark.get(sha)==1:raise ValueError("cycle")
   if mark.get(sha)==2:return
   mark[sha]=1
   for parent in nodes[sha]["parents"]:
    if parent in nodes:visit(parent)
   mark[sha]=2
  try:
   for sha in nodes:visit(sha)
  except ValueError:return {"status":"INVALID","errors":["parent cycle"]}
 findings=[]
 for rid,nodes in graph.items():
  for sha,c in nodes.items():
   for psha in c["parents"]:
    p=nodes.get(psha)
    if not p:
     findings.append({"type":"UNRESOLVED_PARENT","repo_id":rid,"parent":psha,"child":sha});continue
    for key in ("author_at_utc","committer_at_utc"):
     if p.get(key) and c.get(key) and when(p[key])>when(c[key]):
      findings.append({"type":"GIT_CLOCK_INVERSION","repo_id":rid,"parent":psha,"child":sha,"clock":key})
    po=[o for o in obs if o["repo_id"]==rid and o["sha"]==psha]
    co=[o for o in obs if o["repo_id"]==rid and o["sha"]==sha]
    for a in po:
     for b in co:
      if when(a["observed_at_utc"])>when(b["observed_at_utc"]):
       findings.append({"type":"OBSERVATION_ORDER_DIFFERS_FROM_PARENTAGE","repo_id":rid,"parent":psha,"child":sha})
 return {"status":"PASS","commits":sum(map(len,graph.values())),"observations":len(obs),"findings":findings,"decision":None,"quorum":None,"warning":"Supplied ancestry is not independently authenticated."}
if __name__=="__main__":
 data=json.loads(Path(sys.argv[1]).read_text());print(json.dumps(audit(data["commits"],data["observations"]),indent=2))
