import json,tempfile,unittest
from pathlib import Path
from operations037 import receipt,plan,apply,canonical_hash
A="a"*40
def run(run_id=123,conclusion="success",status="completed",attempt=1):
 return {"id":run_id,"run_attempt":attempt,"name":"FORMIC CVD - Six Witness Git Perimeter",
         "head_sha":A,"repository":{"full_name":"DavidWise01/0root-provenance"},
         "event":"schedule","status":status,"conclusion":conclusion,
         "html_url":f"https://github.com/DavidWise01/0root-provenance/actions/runs/{run_id}",
         "created_at":"2026-11-04T12:00:00Z","updated_at":"2026-11-04T13:00:00Z"}
class OperationalTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def test_success(self):self.assertEqual(receipt(run())["result"],"REPORTED_SUCCESS")
 def test_failure(self):self.assertEqual(receipt(run(conclusion="failure"))["result"],"REPORTED_NON_SUCCESS")
 def test_cancelled(self):self.assertEqual(receipt(run(conclusion="cancelled"))["conclusion"],"cancelled")
 def test_in_progress(self):self.assertIsNone(receipt(run(status="in_progress",conclusion=None)))
 def test_invalid_repo(self):
  v=run();v["repository"]["full_name"]="Other/Repo"
  with self.assertRaises(ValueError):receipt(v)
 def test_invalid_head(self):
  v=run();v["head_sha"]="no"
  with self.assertRaises(ValueError):receipt(v)
 def test_bad_url(self):
  v=run();v["html_url"]="https://example.org"
  with self.assertRaises(ValueError):receipt(v)
 def test_plan_no_side_effect(self):
  new,counts=plan(self.root,[run()])
  self.assertEqual(counts["new"],1);self.assertFalse((self.root/"cvd").exists())
 def test_written_once(self):
  new,_=plan(self.root,[run()]);apply(new)
  pending,counts=plan(self.root,[run()])
  self.assertEqual(pending,[]);self.assertEqual(counts["already_recorded"],1)
 def test_no_overwrite(self):
  new,_=plan(self.root,[run()]);apply(new)
  with self.assertRaises(FileExistsError):apply(new)
 def test_tamper(self):
  new,_=plan(self.root,[run()]);paths=apply(new);x=json.loads(Path(paths[0]).read_text());x["conclusion"]="failure";Path(paths[0]).write_text(json.dumps(x))
  with self.assertRaises(ValueError):plan(self.root,[run()])
 def test_skip_current(self):
  _,counts=plan(self.root,[run()],current_run_id=123)
  self.assertEqual(counts["new"],0)
 def test_attempt_distinction(self):
  rows,counts=plan(self.root,[run(attempt=1),run(attempt=2)])
  self.assertEqual(len(rows),2)
 def test_duplicate_listing(self):
  rows,_=plan(self.root,[run(),run()]);self.assertEqual(len(rows),1)
 def test_invalid_id(self):
  with self.assertRaises(ValueError):plan(self.root,[],current_run_id=True)
 def test_hash(self):
  r=receipt(run());self.assertEqual(r["record_sha256"],canonical_hash({k:v for k,v in r.items() if k!="record_sha256"}))
 def test_excluded_current_not_success(self):
  rows,_=plan(self.root,[run(),run(run_id=124)],current_run_id=124)
  self.assertEqual(len(rows),1)
if __name__=="__main__":unittest.main()
