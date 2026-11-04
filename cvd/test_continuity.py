import copy,unittest
from continuity import check,hash_record
A="a"*40
B="b"*40
C="c"*40
def event(seq,kind,rid,name,sha,prior=None,**kw):
    e={"schema":"CVD-CONTINUITY-v1","sequence":seq,"event":kind,
       "github_repository_id":rid,"repository_full_name":name,
       "observed_commit":sha,"previous_record_sha256":prior,**kw}
    e["record_sha256"]=hash_record(e)
    return e
def chain():
    a=event(0,"anchor",12,"Ada/source",A)
    b=event(1,"rename",12,"Ada/renamed",A,a["record_sha256"],previous_repository_full_name="Ada/source")
    c=event(2,"fork",13,"Bea/fork",B,b["record_sha256"],parent_github_repository_id=12,parent_commit=A)
    d=event(3,"derive",14,"Cal/derived",C,c["record_sha256"],parent_github_repository_id=13,parent_commit=B)
    return [a,b,c,d]
class ContinuityTests(unittest.TestCase):
    def test_valid(self): self.assertEqual(check(chain()),[])
    def test_identity_tamper(self):
        e=chain();e[1]["github_repository_id"]=99;self.assertTrue(check(e))
    def test_claim_tamper(self):
        e=chain();e[2]["claim"]="new owner";self.assertTrue(check(e))
    def test_missing_parent(self):
        e=chain();e[2]["parent_github_repository_id"]=999;self.assertTrue(check(e))
    def test_self_fork(self):
        e=chain();e[2]["parent_github_repository_id"]=13;self.assertTrue(check(e))
    def test_bad_link(self):
        e=chain();e[2]["previous_record_sha256"]=None;self.assertTrue(check(e))
    def test_reorder(self):
        e=chain();e[1],e[2]=e[2],e[1];self.assertTrue(check(e))
    def test_invalid_commit(self):
        e=chain();e[0]["observed_commit"]="bad";self.assertTrue(check(e))
    def test_duplicate_anchor(self):
        e=chain();e.append(event(4,"anchor",12,"Ada/renamed",A,e[-1]["record_sha256"]));self.assertTrue(check(e))
    def test_undeclared_name(self):
        e=chain();e[3]["repository_full_name"]="Other/name";self.assertTrue(check(e))
    def test_fork_has_distinct_id(self):
        e=chain();self.assertNotEqual(e[0]["github_repository_id"],e[2]["github_repository_id"])
if __name__=="__main__":unittest.main()
