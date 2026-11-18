"""Chạy: PYTHONPATH=src python3 -m pytest tests/ -q  (hoặc python3 -m unittest discover -s tests)"""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from genechain.ipfs_sim import IPFSStore, cid_of
from genechain.dag import PedigreeDAG
from genechain.chain import GeneChain

G = lambda code, trait, score: {"code": code, "name": code, "trait": trait, "score": score, "description": ""}


class TestGeneChain(unittest.TestCase):
    def setUp(self):
        self.chain = GeneChain(IPFSStore(tempfile.mkdtemp()), PedigreeDAG())
        self.a = self.chain.mint_genesis("A", "Alice", [G("DRT-09", "drought", 92), G("YLD-09", "yield", 90)])
        self.b = self.chain.mint_genesis("B", "Bob", [G("SAL-07", "salinity", 85), G("YLD-07", "yield", 70)])

    def test_cid_bat_bien(self):
        self.assertEqual(cid_of(G("X", "t", 1)), cid_of(G("X", "t", 1)))
        self.assertNotEqual(cid_of(G("X", "t", 1)), cid_of(G("X", "t", 2)))

    def test_lai_tao_tat_dinh_va_tai_to_hop(self):
        c1 = self.chain.breed(self.a.token_id, self.b.token_id, "C", "Dave")
        # Gen của con phải là tập con của gen cha+mẹ (chỉ tái tổ hợp, không sinh gen lạ)
        self.assertTrue(set(c1.gene_cids) <= set(self.a.gene_cids + self.b.gene_cids))
        self.assertEqual(c1.generation, 1)

    def test_truy_xuat_nguoc_va_dong_gop(self):
        c = self.chain.breed(self.a.token_id, self.b.token_id, "C", "Dave")
        d = self.chain.breed(c.token_id, self.a.token_id, "D", "Dave")
        contrib = self.chain.dag.genesis_contributions(d.token_id)
        self.assertAlmostEqual(sum(contrib.values()), 1.0)
        self.assertAlmostEqual(contrib[self.a.token_id], 0.75)  # 0.5 qua C + 0.5 trực tiếp
        self.assertAlmostEqual(contrib[self.b.token_id], 0.25)
        self.assertEqual(set(self.chain.dag.ancestors(d.token_id)), {self.a.token_id, self.b.token_id, c.token_id})

    def test_royalty_va_verify(self):
        c = self.chain.breed(self.a.token_id, self.b.token_id, "C", "Dave")
        r = self.chain.trace_and_split(c.token_id, 100_000)
        self.assertTrue(r["verified"])
        self.assertEqual(r["payouts"], {"Alice": 5000.0, "Bob": 5000.0})
        # Giả mạo hash -> verify phải fail
        self.chain.dag.get(c.token_id).block_hash = "tampered"
        self.assertFalse(self.chain.dag.verify(c.token_id))


if __name__ == "__main__":
    unittest.main()
