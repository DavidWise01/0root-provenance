import copy,unittest
from checkpoint import create_checkpoint,verify_checkpoint
from continuity import hash_record,check
from test_continuity import chain
class CheckpointTests(unittest.TestCase):
    def test_known_chain(self):
        events=chain();cp=create_checkpoint(events)
        self.assertEqual(verify_checkpoint(events,cp),[])
    def test_wholesale_rehash_rejected(self):
        events=chain();cp=create_checkpoint(events)
        rewritten=copy.deepcopy(events);rewritten[0]["observed_commit"]="d"*40
        previous=None
        for item in rewritten:
            item["previous_record_sha256"]=previous
            item["record_sha256"]=hash_record(item)
            previous=item["record_sha256"]
        self.assertEqual(check(rewritten),[])
        self.assertIn("checkpoint tip mismatch",verify_checkpoint(rewritten,cp))
    def test_truncation_rejected(self):
        events=chain();cp=create_checkpoint(events)
        self.assertTrue(verify_checkpoint(events[:-1],cp))
    def test_checkpoint_schema_rejected(self):
        events=chain();cp=create_checkpoint(events);cp["schema"]="other"
        self.assertIn("invalid checkpoint schema",verify_checkpoint(events,cp))
if __name__=="__main__":unittest.main()
