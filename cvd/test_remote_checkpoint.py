import unittest
from remote_checkpoint import verify
SRC="DavidWise01/0root-provenance"
SHA="a"*40
BLOB="b"*40
W={"schema":"CVD-REMOTE-CHECKPOINT-v1","checkpoint_id":"test","witness_repository":"DavidWise01/attribution-standard","source":{"repository":SRC,"github_repository_id":42,"commit":SHA,"path":"cvd/data.json","git_blob_sha":BLOB}}
def mock(path):
    if path=="/repos/"+SRC:return {"id":42}
    if path=="/repos/"+SRC+"/contents/cvd/data.json?ref="+SHA:return {"sha":BLOB,"type":"file"}
    if path=="/repos/"+SRC+"/contents/cvd/data.json":return {"sha":BLOB,"type":"file"}
    raise RuntimeError("not found")
class RemoteCheckpointTests(unittest.TestCase):
    def test_verified(self):self.assertEqual(verify(W,mock)["status"],"VERIFIED")
    def test_current_verified(self):self.assertEqual(verify(W,mock,current=True)["status"],"VERIFIED")
    def test_changed_source_identity(self):
        a={**W,"source":{**W["source"],"github_repository_id":99}}
        self.assertEqual(verify(a,mock)["status"],"REJECT")
    def test_changed_blob(self):
        a={**W,"source":{**W["source"],"git_blob_sha":"c"*40}}
        self.assertEqual(verify(a,mock)["status"],"REJECT")
    def test_witness_same_repo(self):
        self.assertEqual(verify({**W,"witness_repository":SRC},mock)["status"],"REJECT")
    def test_bad_sha(self):
        self.assertEqual(verify({**W,"source":{**W["source"],"commit":"fake"}},mock)["status"],"REJECT")
    def test_unavailable(self):
        def fail(path):raise RuntimeError("offline")
        self.assertEqual(verify(W,fail)["status"],"HOLD")
    def test_current_divergence(self):
        def changed(path):
            if path=="/repos/"+SRC+"/contents/cvd/data.json":return {"sha":"d"*40,"type":"file"}
            return mock(path)
        self.assertEqual(verify(W,changed,current=True)["status"],"REJECT")
if __name__=="__main__":unittest.main()
