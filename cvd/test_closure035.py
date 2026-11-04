import unittest
from closure035 import closure,payload_digest
A,B,C,D=("a"*40,"b"*40,"c"*40,"d"*40)
class Reader:
 def __init__(self,parents,offline=(),bad=()):
  self.parents=parents;self.offline=set(offline);self.bad=set(bad)
 def commit(self,repo,sha):
  if sha in self.offline:raise RuntimeError("offline")
  if sha in self.bad:return {"sha":D,"parents":[]}
  return {"sha":sha,"parents":[{"sha":s} for s in self.parents[sha]]}
def run(parents,head,**kwargs):return closure("Owner/repo",head,Reader(parents),observed_utc="2026-11-04T00:00:00Z",**kwargs)
class CausalClosureTests(unittest.TestCase):
 def test_root(self):self.assertEqual(run({A:[]},A)["status"],"VERIFIED")
 def test_linear(self):self.assertEqual(len(run({C:[B],B:[A],A:[]},C)["nodes"]),3)
 def test_merge(self):self.assertEqual(len(run({D:[B,C],B:[A],C:[A],A:[]},D)["nodes"]),4)
 def test_missing(self):self.assertEqual(closure("Owner/repo",B,Reader({B:[A]},offline={A}))["status"],"HOLD")
 def test_depth(self):self.assertEqual(run({C:[B],B:[A],A:[]},C,max_depth=1)["status"],"HOLD")
 def test_budget(self):self.assertEqual(run({C:[B],B:[A],A:[]},C,max_nodes=2)["status"],"HOLD")
 def test_mismatch(self):self.assertEqual(closure("Owner/repo",A,Reader({A:[]},bad={A}))["status"],"HOLD")
 def test_cycle(self):self.assertEqual(run({A:[B],B:[A]},A)["status"],"REJECT")
 def test_self_parent(self):self.assertEqual(run({A:[A]},A)["status"],"HOLD")
 def test_no_quorum(self):self.assertIsNone(run({A:[]},A)["quorum"])
 def test_no_title_proof(self):self.assertIn("not proof",run({A:[]},A)["meaning"])
 def test_hash(self):
  r=run({A:[]},A);self.assertEqual(r["record_sha256"],payload_digest({k:v for k,v in r.items() if k!="record_sha256"}))
 def test_bad_sha(self):
  with self.assertRaises(ValueError):closure("Owner/repo","no",Reader({}))
 def test_bad_repo(self):
  with self.assertRaises(ValueError):closure("../bad",A,Reader({}))
 def test_bool_budget(self):
  with self.assertRaises(ValueError):closure("Owner/repo",A,Reader({A:[]}),max_nodes=True)
 def test_duplicate_parent(self):self.assertEqual(run({A:[B,B],B:[]},A)["status"],"HOLD")
if __name__=="__main__":unittest.main()
