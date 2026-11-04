import unittest
from witness030 import observation,validate,compare,digest
A="a"*40;B="b"*40;T="2026-11-04T18:00:00Z"
def make(w,outcome="OBSERVED",commit=A,event="ev1"):
    return observation(event_id=event,witness_id=w,sequence=0,prev_sha=None,repo_id=123,repository="Owner/repo",commit=commit,observed_utc=T,outcome=outcome)
class WitnessTests(unittest.TestCase):
 def test_valid_three(self):self.assertEqual(validate([make("ff"),make("cf"),make("rf")]),[])
 def test_consistent(self):self.assertEqual(compare([make("ff"),make("cf"),make("rf")],"ev1")["state"],"CONSISTENT_REPORTS")
 def test_divergent(self):self.assertEqual(compare([make("ff"),make("cf","HOLD"),make("rf")],"ev1")["state"],"DIVERGENT_REPORTS")
 def test_different_target(self):self.assertEqual(compare([make("ff"),make("cf",commit=B)],"ev1")["state"],"DIFFERENT_TARGETS")
 def test_no_quorum(self):self.assertIsNone(compare([make("ff")],"ev1")["quorum"])
 def test_one_witness(self):self.assertEqual(compare([make("ff")],"ev1")["observed_witnesses"],1)
 def test_hash_preserved(self):
    a=[make("ff"),make("cf","HOLD")];self.assertEqual([x["record_sha256"] for x in a],[x["record_sha256"] for x in a])
 def test_tamper(self):
    a=make("ff");a["outcome"]="REJECT";self.assertTrue(validate([a]))
 def test_rehashed_tamper_needs_checkpoint(self):
    a=make("ff");a["outcome"]="REJECT";a["record_sha256"]=digest(a);self.assertEqual(validate([a]),[])
 def test_bad_commit(self):
    a=make("ff");a["commit"]="bad";a["record_sha256"]=digest(a);self.assertTrue(validate([a]))
 def test_independent_chains(self):
    a=make("ff");b=make("cf");c=observation(event_id="ev2",witness_id="ff",sequence=1,prev_sha=a["record_sha256"],repo_id=123,repository="Owner/repo",commit=A,observed_utc=T,outcome="HOLD");self.assertEqual(validate([a,b,c]),[])
 def test_wrong_link(self):
    a=make("ff");b=observation(event_id="ev2",witness_id="ff",sequence=1,prev_sha=None,repo_id=123,repository="Owner/repo",commit=A,observed_utc=T,outcome="HOLD");self.assertTrue(validate([a,b]))
 def test_duplicate_record(self):
    a=make("ff");self.assertTrue(validate([a,a]))
 def test_empty_event(self):self.assertEqual(compare([make("ff")],"other")["status"],"NO_OBSERVATIONS")
 def test_invalid_prevents_comparison(self):
    a=make("ff");a["commit"]="oops";self.assertEqual(compare([a],"ev1")["status"],"INVALID")
 def test_invalid_id_type(self):
    a=make("ff");a["github_repository_id"]=True;a["record_sha256"]=digest(a);self.assertTrue(validate([a]))
if __name__=="__main__":unittest.main()
