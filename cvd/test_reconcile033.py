import json,tempfile,unittest
from pathlib import Path
from reconcile033 import append,plan,read,digest,timeline
A='a'*40;B='b'*40;T1='2026-11-04T08:00:00Z';T2='2026-11-04T09:00:00Z';T3='2026-11-04T10:00:00Z';T4='2026-11-04T11:00:00Z'
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def source(self,w='ff',when=T1,commit=A):
  d=self.root/'cvd'/'observations'/w;d.mkdir(parents=True,exist_ok=True);old=read(self.root,w)
  e=dict(schema='CVD-WITNESS-030-v1',event_id='e',witness_id=w,sequence=len(old),previous_record_sha256=old[-1]['record_sha256'] if old else None,github_repository_id=42,repository='Owner/source',commit=commit,observed_utc=when,outcome='VERIFIED',details={})
  e['record_sha256']=digest(e);(d/f"{e['sequence']:09d}-{e['record_sha256']}.json").write_text(json.dumps(e));return e
 def test_first(self):self.source();self.assertEqual(len(plan(self.root,'ff',T2)),1)
 def test_dry_run(self):self.source();plan(self.root,'ff',T2);self.assertFalse((self.root/'cvd'/'temporal').exists())
 def test_idempotent(self):self.source();append(self.root,'ff',plan(self.root,'ff',T2));self.assertEqual(plan(self.root,'ff',T3),[])
 def test_late(self):
  self.source(when=T2,commit=B);append(self.root,'ff',plan(self.root,'ff',T3))
  self.source(when=T1,commit=A);append(self.root,'ff',plan(self.root,'ff',T4))
  self.assertEqual([r['commit'] for r in timeline(self.root,42)['observations']],[A,B])
  self.assertEqual(timeline(self.root,42)['state'],'TEMPORAL_VARIATION')
 def test_same_time_conflict(self):
  self.source();self.source('cf',commit=B)
  for w in ('ff','cf'):append(self.root,w,plan(self.root,w,T2))
  self.assertEqual(timeline(self.root,42)['state'],'SAME_TIME_DIVERGENCE')
 def test_no_quorum(self):self.source();append(self.root,'ff',plan(self.root,'ff',T2));self.assertIsNone(timeline(self.root,42)['quorum'])
 def test_source_tamper(self):
  e=self.source();f=next((self.root/'cvd'/'observations'/'ff').glob('*.json'));e['commit']=B;f.write_text(json.dumps(e))
  with self.assertRaises(ValueError):plan(self.root,'ff',T2)
 def test_overlay_tamper(self):
  self.source();append(self.root,'ff',plan(self.root,'ff',T2))
  f=next((self.root/'cvd'/'temporal'/'ff').glob('*.json'));e=json.loads(f.read_text());e['commit']=B;f.write_text(json.dumps(e))
  with self.assertRaises(ValueError):plan(self.root,'ff',T3)
 def test_source_removed(self):
  self.source();append(self.root,'ff',plan(self.root,'ff',T2))
  next((self.root/'cvd'/'observations'/'ff').glob('*.json')).unlink()
  with self.assertRaises(ValueError):plan(self.root,'ff',T3)
 def test_future(self):
  self.source(when=T3)
  with self.assertRaises(ValueError):plan(self.root,'ff',T2)
 def test_clock_regression(self):
  self.source();append(self.root,'ff',plan(self.root,'ff',T3))
  with self.assertRaises(ValueError):plan(self.root,'ff',T2)
 def test_no_overwrite(self):
  self.source();rows=plan(self.root,'ff',T2);append(self.root,'ff',rows)
  with self.assertRaises(FileExistsError):append(self.root,'ff',rows)
 def test_separate_chains(self):
  self.source();self.source('cf')
  for w in ('ff','cf'):append(self.root,w,plan(self.root,w,T2))
  self.assertEqual(len(timeline(self.root,42)['observations']),2)
 def test_no_observations(self):self.assertEqual(timeline(self.root,42)['state'],'NO_OBSERVATIONS')
if __name__=='__main__':unittest.main()
