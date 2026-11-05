"""CVD 039 external checkpoint security and continuity regression tests."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from external_anchor039 import snapshot,canonical,verify,fetch
from recover038 import ANCHOR
from collect031 import append,digest
A="a"*40
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def anchor(self):
  b=canonical(snapshot(self.root))
  return b,hashlib.sha256(b).hexdigest()
 def source(self):
  item={"schema":"CVD-WITNESS-030-v1","event_id":"ev","witness_id":"ff","sequence":0,
    "previous_record_sha256":None,"github_repository_id":42,"repository":"Owner/repo",
    "commit":A,"observed_utc":"2026-11-04T20:00:00Z","outcome":"VERIFIED","details":{}}
  item["record_sha256"]=digest(item);append(self.root,[item]);return item
 def test_empty_snapshot(self):
  b,p=self.anchor();self.assertEqual(len(json.loads(b)["channels"]),6)
 def test_valid_empty(self):
  b,p=self.anchor();self.assertEqual(verify(self.root,b,p)["status"],"VERIFIED")
 def test_prefix_valid_after_append(self):
  b,p=self.anchor();self.source();self.assertEqual(verify(self.root,b,p)["status"],"VERIFIED")
 def test_digest_wrong(self):
  b,p=self.anchor();self.assertEqual(verify(self.root,b,"0"*64)["status"],"HOLD")
 def test_digest_missing(self):
  b,p=self.anchor()
  with self.assertRaises(ValueError):verify(self.root,b,None)
 def test_rewrite_of_pinned_prefix(self):
  item=self.source();b,p=self.anchor()
  f=next((self.root/"cvd"/"observations"/"ff").glob("*.json"));item["commit"]="b"*40;f.write_text(json.dumps(item))
  self.assertEqual(verify(self.root,b,p)["status"],"HOLD")
 def test_missing_pinned_record(self):
  self.source();b,p=self.anchor()
  next((self.root/"cvd"/"observations"/"ff").glob("*.json")).unlink()
  self.assertEqual(verify(self.root,b,p)["status"],"HOLD")
 def test_noncanonical(self):
  b,p=self.anchor();altered=json.dumps(json.loads(b)).encode()
  self.assertEqual(verify(self.root,altered,hashlib.sha256(altered).hexdigest())["status"],"HOLD")
 def test_schema_mismatch(self):
  b,p=self.anchor();v=json.loads(b);v["schema"]="invalid";bb=canonical(v)
  self.assertEqual(verify(self.root,bb,hashlib.sha256(bb).hexdigest())["status"],"HOLD")
 def test_reject_unpinned_branch(self):
  with self.assertRaises(ValueError):
   fetch("https://raw.githubusercontent.com/DavidWise01/attribution-standard/main/cvd/anchors/test.json")
 def test_reject_foreign_host(self):
  with self.assertRaises(ValueError):
   fetch("https://evil.example/a")
 def test_reject_external_owner(self):
  with self.assertRaises(ValueError):
   fetch("https://raw.githubusercontent.com/Foreign/repo/"+"a"*40+"/cvd/anchors/checkpoint.json")
 def test_oversized(self):
  data=b"x"*262145\n  with self.assertRaises(ValueError):verify(self.root,data,hashlib.sha256(data).hexdigest())
 def test_changed_unpinned_tail(self):
  self.source();b,p=self.anchor();self.assertEqual(verify(self.root,b,p)["status"],"VERIFIED")
if __name__=="__main__":unittest.main()
