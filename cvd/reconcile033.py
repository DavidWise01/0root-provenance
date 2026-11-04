#!/usr/bin/env python3
"""CVD 033: append-only temporal overlay for FORMIC 031. No GitHub writes."""
import argparse,datetime as dt,hashlib,json,re,sys
from pathlib import Path
ROLES=('ff','fr','cf','cr','rf','rr')
def digest(r):
 return hashlib.sha256(json.dumps({k:v for k,v in r.items() if k!='record_sha256'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def instant(t):
 if not isinstance(t,str) or not t.endswith('Z'):raise ValueError('UTC timestamp required')
 return dt.datetime.fromisoformat(t[:-1]+'+00:00')
def read(root,w,temporal=False):
 if w not in ROLES:raise ValueError('bad observer')
 folder=Path(root)/'cvd'/('temporal' if temporal else 'observations')/w
 rows=[]
 for file in sorted(folder.glob('*.json')) if folder.exists() else []:
  r=json.loads(file.read_text())
  schema='CVD-TEMPORAL-032-v1' if temporal else 'CVD-WITNESS-030-v1'
  prev=rows[-1]['record_sha256'] if rows else None
  if r.get('schema')!=schema or r.get('witness_id')!=w or type(r.get('sequence'))!=int or r['sequence']!=len(rows) or r.get('previous_record_sha256')!=prev:raise ValueError('broken chain: '+file.name)
  h=r.get('record_sha256')
  if not isinstance(h,str) or not re.fullmatch('[0-9a-f]{64}',h) or h!=digest(r) or file.name!=f"{len(rows):09d}-{h}.json":raise ValueError('tampered record: '+file.name)
  if type(r.get('github_repository_id'))!=int or r['github_repository_id']<=0 or not isinstance(r.get('repository'),str) or not re.fullmatch('[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',r['repository']) or not isinstance(r.get('commit'),str) or not re.fullmatch('[0-9a-f]{40}',r['commit']):raise ValueError('bad Git identity')
  instant(r.get('observed_at_utc') if temporal else r.get('observed_utc'))
  if temporal:
   instant(r.get('appended_at_utc'))
   if instant(r['appended_at_utc'])<instant(r['observed_at_utc']):raise ValueError('early append')
   if rows and instant(r['appended_at_utc'])<instant(rows[-1]['appended_at_utc']):raise ValueError('append time regression')
   if not re.fullmatch('[0-9a-f]{64}',r.get('source_witness_sha256','')):raise ValueError('bad source reference')
  rows.append(r)
 return rows
def plan(root,w,clock=None):
 sources=read(root,w)
 old=read(root,w,True)
 mapping={r['source_witness_sha256']:r for r in old}
 source_map={r['record_sha256']:r for r in sources}
 if len(mapping)!=len(old) or not set(mapping).issubset(source_map):raise ValueError('source lineage inconsistent')
 for h,r in mapping.items():
  s=source_map[h]
  if (r['github_repository_id'],r['repository'],r['commit'],r['observed_at_utc'])!=(s['github_repository_id'],s['repository'],s['commit'],s['observed_utc']):raise ValueError('overlay differs from source')
 clock=clock or dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z')
 tick=instant(clock)
 if old and tick<instant(old[-1]['appended_at_utc']):raise ValueError('append clock moved back')
 result=[];seq=len(old);previous=old[-1]['record_sha256'] if old else None
 for s in sources:
  if s['record_sha256'] in mapping:continue
  if instant(s['observed_utc'])>tick:raise ValueError('future observation')
  r=dict(schema='CVD-TEMPORAL-032-v1',witness_id=w,sequence=seq,previous_record_sha256=previous,source_witness_sha256=s['record_sha256'],github_repository_id=s['github_repository_id'],repository=s['repository'],commit=s['commit'],observed_at_utc=s['observed_utc'],appended_at_utc=clock,event_at_utc=None,outcome=s.get('outcome','OBSERVED'))
  r['record_sha256']=digest(r)
  result.append(r);seq+=1;previous=r['record_sha256']
 return result
def append(root,w,records):
 dest=Path(root)/'cvd'/'temporal'/w;paths=[]
 for r in records:
  dest.mkdir(parents=True,exist_ok=True)
  path=dest/f"{r['sequence']:09d}-{r['record_sha256']}.json"
  with path.open('x') as file:json.dump(r,file,indent=2);file.write('\n')
  paths.append(str(path))
 return paths
def timeline(root,repo_id):
 rows=[r for w in ROLES for r in read(root,w,True) if r['github_repository_id']==repo_id]
 rows.sort(key=lambda r:(instant(r['observed_at_utc']),r['witness_id'],r['sequence']))
 bytime={}
 for r in rows:bytime.setdefault(r['observed_at_utc'],set()).add((r['commit'],r['outcome']))
 state='NO_OBSERVATIONS' if not rows else 'SAME_TIME_DIVERGENCE' if any(len(x)>1 for x in bytime.values()) else 'TEMPORAL_VARIATION' if len({(r['commit'],r['outcome']) for r in rows})>1 else 'CONSISTENT_OBSERVATIONS'
 return dict(schema='CVD-TIMELINE-033-v1',state=state,repository_id=repo_id,observations=rows,decision=None,quorum=None)
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--observer',choices=ROLES,default='ff');p.add_argument('--apply',action='store_true');p.add_argument('--timeline-repo-id',type=int);a=p.parse_args()
 try:
  if a.timeline_repo_id is not None:out=timeline(a.root,a.timeline_repo_id)
  else:
   pending=plan(a.root,a.observer)
   paths=append(a.root,a.observer,pending) if a.apply else []
   out=dict(status='PASS',mode='apply' if a.apply else 'dry_run',observer=a.observer,new_temporal_records=len(pending),written_files=paths)
  print(json.dumps(out,indent=2));return 0
 except (ValueError,OSError,KeyError,TypeError) as e:print(json.dumps(dict(status='HOLD',reason=str(e))),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
