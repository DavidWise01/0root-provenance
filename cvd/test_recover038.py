"""CVD 038 regression tests: no remote GitHub dependency."""
import json,tempfile,unittest
from pathlib import Path
from collect031 import append as append_observations, digest
from recover038 import recover,preflight,atomic_create,ANCHOR
A="a"*40;B="b"*40;T="2026-11-04T19:00:00Z"
class Reader:
 def __init__(self,offline=False):self.offline=offline
 def commit(self,repo,sha):
  if self.offline:raise RuntimeError("offline")
  return {"sha":sha,"parents":[]}
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def source(self,sha=A,witness="ff"):
  from collect031 import history
  before=history(self.root,witness)
  entry={"schema":"CVD-WITNESS-030-v1","event_id":"ev-"+sha,"witness_id":witness,
    "sequence":len(before),"previous_record_sha256":before[-1]["record_sha256"] if before else None,
    "github_repository_id":42,"repository":"Owner/demo","commit":sha,"observed_utc":T,
    "outcome":"VERIFIED","details":{}}
  entry["record_sha256"]=digest(entry)
  append_observations(self.root,[entry])
  return entry
 def test_empty_clean(self):self.assertEqual(recover(self.root)["status"],"CLEAN")
 def test_missing_both(self):
  self.source();r=recover(self.root);self.assertEqual((r["temporal_pending"],r["causal_pending"]),(1,1))
 def test_dry_run_unchanged(self):
  self.source();recover(self.root);self.assertFalse((self.root/"cvd"/"temporal").exists())
 def test_repair(self):
  self.source();r=recover(self.root,Reader(),apply=True,clock="2026-11-04T20:00:00Z")
  self.assertEqual(r["status"],"CLEAN");self.assertEqual(len(r["written_files"]),2)
 def test_idempotent(self):
  self.source();recover(self.root,Reader(),apply=True,clock="2026-11-04T20:00:00Z")
  self.assertEqual(recover(self.root,Reader(),apply=True,clock="2026-11-04T20:00:00Z")["written_files"],[])
 def test_causal_backlog(self):
  self.source();r=recover(self.root,Reader(),apply=True,max_closures=0,clock="2026-11-04T20:00:00Z")
  self.assertEqual((r["causal_pending"],r["temporal_pending"]),(1,0))
  self.assertEqual(recover(self.root,Reader(),apply=True,clock="2026-11-04T21:00:00Z")["status"],"CLEAN")
 def test_causal_hold_is_preserved(self):
  self.source();recover(self.root,Reader(offline=True),apply=True,clock="2026-11-04T20:00:00Z")
  sidecar=next((self.root/"cvd"/"causal"/"ff").glob("*.json"))
  self.assertEqual(json.loads(sidecar.read_text())["causal_status"],"HOLD")
 def test_corrupt_source(self):
  a=self.source();f=next((self.root/"cvd"/"observations"/"ff").glob("*.json"))
  a["commit"]=B;f.write_text(json.dumps(a))
  with self.assertRaises(ValueError):recover(self.root,Reader(),apply=True)
 def test_corrupt_temporal(self):
  self.source();recover(self.root,Reader(),apply=True,clock="2026-11-04T20:00:00Z")
  f=next((self.root/"cvd"/"temporal"/"ff").glob("*.json"))
  f.write_text("{}")
  with self.assertRaises(ValueError):recover(self.root,Reader(),apply=True,clock="2026-11-04T21:00:00Z")
 def test_pinned_checkpoint(self):
  a=self.source();pin={"schema":ANCHOR,"channels":{"ff":{"count":1,"head_record_sha256":a["record_sha256"]}}}
  self.assertEqual(recover(self.root,anchor=pin)["status"],"RECOVERABLE")
 def test_checkpoint_divergence(self):
  self.source();pin={"schema":ANCHOR,"channels":{"ff":{"count":1,"head_record_sha256":"c"*64}}}
  with self.assertRaises(ValueError):recover(self.root,anchor=pin)
 def test_multiple_channels(self):
  self.source(witness="ff");self.source(witness="cf")
  r=recover(self.root,Reader(),apply=True,max_closures=2,clock="2026-11-04T20:00:00Z")
  self.assertEqual(len(r["written_files"]),4)
 def test_atomic_no_overwrite(self):
  path=self.root/"test.json";atomic_create(path,{"value":1})
  with self.assertRaises(FileExistsError):atomic_create(path,{"value":2})
  self.assertEqual(json.loads(path.read_text())["value"],1)
 def test_no_synthetic_witnesses(self):
  self.source();recover(self.root,Reader(),apply=True,clock="2026-11-04T20:00:00Z")
  self.assertFalse((self.root/"cvd"/"temporal"/"cf").exists())
 def test_corrupt_causal(self):
  self.source();recover(self.root,Reader(),apply=True,clock="2026-11-04T20:00:00Z")
  f=next((self.root/"cvd"/"causal"/"ff").glob("*.json"));f.write_text("{}")
  with self.assertRaises(ValueError):preflight(self.root)
if __name__=="__main__":unittest.main()
