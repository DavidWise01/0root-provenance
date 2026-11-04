import unittest
from causal034 import audit
A="a"*40;B="b"*40;C="c"*40
T1="2026-11-04T08:00:00Z";T2="2026-11-04T09:00:00Z";T3="2026-11-04T10:00:00Z"
def c(sha,parents,at=T2):return {"repo_id":42,"sha":sha,"parents":parents,"committer_at_utc":at}
def o(sha,seen=T1,app=T3):return {"repo_id":42,"sha":sha,"observed_at_utc":seen,"appended_at_utc":app}
class Tests(unittest.TestCase):
 def kinds(self,x):return [f["type"] for f in x["findings"]]
 def test_parent(self):self.assertEqual(self.kinds(audit([c(A,[]),c(B,[A],T3)],[])),[])
 def test_observation_reversal(self):self.assertIn("OBSERVATION_ORDER_DIFFERS_FROM_PARENTAGE",self.kinds(audit([c(A,[]),c(B,[A])],[o(A,T2),o(B,T1)])))
 def test_observation_forward(self):self.assertNotIn("OBSERVATION_ORDER_DIFFERS_FROM_PARENTAGE",self.kinds(audit([c(A,[]),c(B,[A])],[o(A,T1),o(B,T2)])))
 def test_git_clock(self):self.assertIn("GIT_CLOCK_INVERSION",self.kinds(audit([c(A,[],T3),c(B,[A],T1)],[])))
 def test_missing_parent(self):self.assertIn("UNRESOLVED_PARENT",self.kinds(audit([c(B,[A])],[])))
 def test_cycle(self):self.assertEqual(audit([c(A,[B]),c(B,[A])],[])["status"],"INVALID")
 def test_invalid_sha(self):self.assertEqual(audit([c("x",[])],[])["status"],"INVALID")
 def test_duplicate(self):self.assertEqual(audit([c(A,[]),c(A,[])],[])["status"],"INVALID")
 def test_append_before_observe(self):self.assertEqual(audit([], [o(A,T3,T1)])["status"],"INVALID")
 def test_no_quorum(self):self.assertIsNone(audit([],[])["quorum"])
 def test_unrelated_not_ordered(self):self.assertEqual(self.kinds(audit([c(A,[],T3),c(B,[],T1)],[])),[])
 def test_cross_repo(self):
  x=c(B,[A]);x["repo_id"]=43
  self.assertIn("UNRESOLVED_PARENT",self.kinds(audit([c(A,[]),x],[])))
 def test_merge(self):self.assertEqual(audit([c(A,[]),c(B,[]),c(C,[A,B])],[])["status"],"PASS")
 def test_author_clock(self):
  a=c(A,[],T1);a["author_at_utc"]=T3
  b=c(B,[A],T2);b["author_at_utc"]=T1
  self.assertIn("GIT_CLOCK_INVERSION",self.kinds(audit([a,b],[])))
if __name__=="__main__":unittest.main()
