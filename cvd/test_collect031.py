"""CVD-031 observer unit tests: execute with python -m unittest discover -s cvd -p 'test_collect031.py'"""
import tempfile,unittest
from pathlib import Path
from collect031 import collect,append,history,digest
SHA_A="a"*40;SHA_B="b"*40
class Fake:
 def __init__(self,changed=False,private=False,offline=False):
  self.changed=changed;self.private=private;self.offline=offline;self.calls=[]
 def get(self,path):
  self.calls.append(path)
  if "/users/" in path:
   if path.endswith("page=1"):
    r=[{"full_name":"Owner/demo","id":42,"default_branch":"main","owner":{"login":"Owner"},"private":False,"visibility":"public"}]
    if self.private:r.append({"full_name":"Owner/secret","id":43,"default_branch":"main","owner":{"login":"Owner"},"private":True,"visibility":"private"})
    return r
   return []
  if self.offline:raise RuntimeError("offline")
  if path=="/repos/Owner/demo/commits/main":return {"sha":SHA_B if self.changed else SHA_A}
  raise RuntimeError("unexpected")
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def scan(self,api=None,who="ff"):
  return collect(api or Fake(),self.root,"Owner",who,clock="2026-11-04T00:00:00Z")
 def test_initial(self):self.assertEqual(len(self.scan()[0]),1)
 def test_unwritten_dry_run(self):self.scan();self.assertFalse((self.root/"cvd").exists())
 def test_append(self):
  a,_=self.scan();self.assertEqual(len(append(self.root,a)),1)
 def test_no_overwrite(self):
  a,_=self.scan();append(self.root,a)
  with self.assertRaises(FileExistsError):append(self.root,a)
 def test_idempotent(self):
  a,_=self.scan();append(self.root,a);b,c=self.scan();self.assertFalse(b);self.assertEqual(c["unchanged"],1)
 def test_change_appends(self):
  a,_=self.scan();append(self.root,a);b,_=self.scan(Fake(changed=True));self.assertEqual(b[0]["previous_record_sha256"],a[0]["record_sha256"])
 def test_private_is_not_scanned(self):
  f=Fake(private=True);self.scan(f);self.assertFalse(any("secret" in x for x in f.calls))
 def test_no_false_positive_on_failure(self):
  a,c=self.scan(Fake(offline=True));self.assertFalse(a);self.assertEqual(c["hold"],1)
 def test_separate_observers(self):
  a,_=self.scan(who="ff");append(self.root,a);b,_=self.scan(who="cf");self.assertEqual(b[0]["sequence"],0)
 def test_no_fabricated_observers(self):
  a,_=self.scan();append(self.root,a);self.assertEqual(history(self.root,"rf"),[])
 def test_detect_tamper(self):
  import json
  a,_=self.scan();p=Path(append(self.root,a)[0]);v=json.loads(p.read_text());v["commit"]=SHA_B;p.write_text(json.dumps(v))
  with self.assertRaises(ValueError):history(self.root,"ff")
 def test_invalid_owner(self):
  with self.assertRaises(ValueError):collect(Fake(),self.root,"../owner","ff")
if __name__=="__main__":unittest.main()
