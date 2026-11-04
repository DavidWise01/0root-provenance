import unittest
from attest import attest,verify_events
SHA="a"*40
BASE={"repository_full_name":"Owner/repo","github_repository_id":123,"observed_commit":SHA}
META={"id":123,"full_name":"Owner/repo"}
COMMIT={"sha":SHA,"html_url":f"https://github.com/Owner/repo/commit/{SHA}"}
def fetch(p):return META if p=="/repos/Owner/repo" else COMMIT
class Tests(unittest.TestCase):
 def test_valid(self):self.assertEqual(attest(BASE,fetch)["status"],"VERIFIED")
 def test_identity_mismatch(self):self.assertEqual(attest({**BASE,"github_repository_id":999},fetch)["status"],"REJECT")
 def test_invalid_sha(self):self.assertEqual(attest({**BASE,"observed_commit":"bad"},fetch)["status"],"REJECT")
 def test_commit_mismatch(self):self.assertEqual(attest(BASE,lambda p:META if p=="/repos/Owner/repo" else {**COMMIT,"sha":"b"*40})["status"],"REJECT")
 def test_rename(self):self.assertEqual(attest(BASE,lambda p:{**META,"full_name":"Owner/renamed"} if p=="/repos/Owner/repo" else COMMIT)["status"],"HOLD")
 def test_unavailable(self):
  def fail(p):raise RuntimeError("offline")
  self.assertEqual(attest(BASE,fail)["status"],"HOLD")
 def test_invalid_repo(self):self.assertEqual(attest({**BASE,"repository_full_name":"../bad"},fetch)["status"],"REJECT")
 def test_unexpected_url(self):self.assertEqual(attest(BASE,lambda p:META if p=="/repos/Owner/repo" else {**COMMIT,"html_url":"other"})["status"],"HOLD")
 def test_mixed(self):self.assertEqual(verify_events([BASE,{**BASE,"github_repository_id":999}],fetch)["counts"],{"VERIFIED":1,"HOLD":0,"REJECT":1})
 def test_boolean_id(self):self.assertEqual(attest({**BASE,"github_repository_id":True},fetch)["status"],"REJECT")
if __name__=="__main__":unittest.main()
