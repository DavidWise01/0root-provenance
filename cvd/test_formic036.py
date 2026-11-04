import json,tempfile,unittest
from pathlib import Path
from formic036 import execute,inspect_existing
from collect031 import history
from reconcile033 import read as temporal_read
A="a"*40;B="b"*40;T="2026-11-04T19:00:00Z"
class API:
 def __init__(self,sha=A,offline=False,private=False):
  self.sha=sha;self.offline=offline;self.private=private
 def get(self,path):
  if "/users/" in path:
   if path.endswith("page=1"):
    rows=[{"full_name":"Owner/demo","id":42,"default_branch":"main","owner":{"login":"Owner"},"private":False,"visibility":"public"}]
    if self.private:rows.append({"full_name":"Owner/secret","id":43,"default_branch":"main","owner":{"login":"Owner"},"private":True,"visibility":"private"})
    return rows
   return []
  if self.offline:raise RuntimeError("offline")
  if path=="/repos/Owner/demo/commits/main":return {"sha":self.sha}
  raise RuntimeError("unexpected")
class Reader:
 def __init__(self,offline=False):self.offline=offline
 def commit(self,repo,sha):
  if self.offline:raise RuntimeError("unavailable")
  return {"sha":sha,"parents":[]}
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def go(self,api=None,reader=None,**kwargs):
  return execute(self.root,"Owner","ff",api or API(),reader or Reader(),clock=T,**kwargs)
 def test_dry_run(self):
  x=self.go();self.assertEqual(x["pending_observations"],1);self.assertFalse((self.root/"cvd").exists())
 def test_initial(self):
  r=self.go(apply=True);self.assertEqual(tuple(len(r[x]) for x in ("observation_files","temporal_files","causal_files")),(1,1,1))
 def test_idempotent(self):
  self.go(apply=True);r=self.go(apply=True);self.assertFalse(r["observation_files"]+r["temporal_files"]+r["causal_files"])
 def test_changed_head(self):
  self.go(apply=True);r=self.go(API(B),apply=True);self.assertEqual(len(r["observation_files"]),1)
 def test_separate_witness(self):
  self.go(apply=True);execute(self.root,"Owner","cf",API(),Reader(),clock=T,apply=True)
  self.assertEqual(len(history(self.root,"cf")),1);self.assertEqual(history(self.root,"fr"),[])
 def test_private_excluded(self):
  self.go(API(private=True),apply=True);self.assertEqual(len(history(self.root,"ff")),1)
 def test_collection_hold(self):
  r=self.go(API(offline=True),apply=True);self.assertEqual(r["status"],"HOLD");self.assertEqual(r["written"],0)
 def test_causal_hold(self):
  r=self.go(reader=Reader(offline=True),apply=True)
  self.assertEqual(json.loads(Path(r["causal_files"][0]).read_text())["causal_status"],"HOLD")
 def test_backfill(self):
  self.go(apply=True);next((self.root/"cvd"/"causal"/"ff").glob("*.json")).unlink()
  r=self.go(apply=True);self.assertEqual(len(r["causal_files"]),1);self.assertEqual(r["observation_files"],[])
 def test_causal_budget(self):
  self.go(apply=True,max_closures=0);r=self.go(apply=True,max_closures=1)
  self.assertEqual(len(r["causal_files"]),1)
 def test_tampered_causal(self):
  self.go(apply=True);f=next((self.root/"cvd"/"causal"/"ff").glob("*.json"));x=json.loads(f.read_text());x["commit"]=B;f.write_text(json.dumps(x))
  with self.assertRaises(ValueError):self.go(apply=True)
 def test_temporal_link(self):
  self.go(apply=True);self.assertEqual(len(temporal_read(self.root,"ff",True)),1)
 def test_invalid_channel(self):
  with self.assertRaises(ValueError):execute(self.root,"Owner","xx",API(),Reader())
 def test_existing_evidence(self):
  self.go(apply=True);self.assertEqual(inspect_existing(self.root,history(self.root,"ff")),1)
if __name__=="__main__":unittest.main()
