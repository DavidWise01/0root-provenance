import tempfile,unittest,json
from pathlib import Path
from formic_compare036 import compare,publish
from formic036 import execute
class API:
 def __init__(self,sha="a"*40):self.sha=sha
 def get(self,p):
  if "/users/" in p:
   return [{"full_name":"Owner/demo","id":42,"default_branch":"main","private":False,"visibility":"public","owner":{"login":"Owner"}}] if p.endswith("page=1") else []
  return {"sha":self.sha}
class Reader:
 def commit(self,r,s):return {"sha":s,"parents":[]}
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def add(self,w,sha="a"*40):execute(self.root,"Owner",w,API(sha),Reader(),clock="2026-11-04T20:00:00Z",apply=True)
 def test_empty(self):self.assertEqual(compare(self.root)["repositories"],[])
 def test_single(self):self.add("ff");self.assertEqual(compare(self.root)["repositories"][0]["status"],"SINGLE_CHANNEL")
 def test_match(self):self.add("ff");self.add("cf");self.assertEqual(compare(self.root)["repositories"][0]["status"],"HEADS_MATCH")
 def test_different(self):self.add("ff");self.add("cf","b"*40);self.assertEqual(compare(self.root)["repositories"][0]["status"],"HEADS_DIFFER")
 def test_no_quorum(self):self.assertIsNone(compare(self.root)["quorum"])
 def test_publish_once(self):
  self.add("ff");state=compare(self.root);self.assertTrue(publish(self.root,state));self.assertIsNone(publish(self.root,state))
 def test_no_mutation(self):
  self.add("ff");self.assertEqual(compare(self.root),compare(self.root))
 def test_corrupt_report(self):
  self.add("ff");view=compare(self.root);path=Path(publish(self.root,view));path.write_text("{}")
  with self.assertRaises(ValueError):publish(self.root,view)
if __name__=="__main__":unittest.main()
