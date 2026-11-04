import unittest
from temporal032 import make,validate,compare,digest
A="a"*40;B="b"*40;S="c"*64
T1="2026-11-04T10:00:00Z";T2="2026-11-04T11:00:00Z";T3="2026-11-04T12:00:00Z"
def obs(w="ff",n=0,prior=None,when=T1,app=T2,commit=A):
 return make(w,n,prior,S,123,"Owner/Repo",commit,when,app)
class TemporalTests(unittest.TestCase):
 def test_valid(self):self.assertEqual(validate([obs()]),[])
 def test_two_witnesses(self):self.assertEqual(validate([obs(),obs("cf")]),[])
 def test_later_commit(self):self.assertEqual(compare([obs(),obs("cf",when=T2,app=T3,commit=B)],123)["status"],"TEMPORAL_VARIATION")
 def test_same_time_divergence(self):self.assertEqual(compare([obs(),obs("cf",commit=B)],123)["status"],"SAME_TIME_DIVERGENCE")
 def test_delayed_observation(self):
  a=obs();b=obs(n=1,prior=a["record_sha256"],when="2026-11-04T09:00:00Z",app=T3);self.assertEqual(validate([a,b]),[])
 def test_append_clock_regression(self):
  a=obs();b=obs(n=1,prior=a["record_sha256"],app=T1);self.assertTrue(validate([a,b]))
 def test_append_before_observed(self):self.assertTrue(validate([obs(when=T3)]))
 def test_tamper(self):
  a=obs();a["commit"]=B;self.assertTrue(validate([a]))
 def test_duplicate(self):
  a=obs();self.assertTrue(validate([a,a]))
 def test_no_quorum(self):self.assertIsNone(compare([obs()],123)["quorum"])
 def test_unknown_repository(self):self.assertEqual(compare([obs()],999)["status"],"NO_OBSERVATIONS")
 def test_bad_timestamp(self):
  a=obs();a["observed_at_utc"]="yesterday";a["record_sha256"]=digest(a);self.assertTrue(validate([a]))
if __name__=="__main__":unittest.main()
