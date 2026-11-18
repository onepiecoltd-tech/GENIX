"""Chạy cùng: PYTHONPATH=src python3 -m unittest discover -s tests -v"""
import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from genechain.ipfs_sim import IPFSStore
from genechain.dag import PedigreeDAG
from genechain.genome_registry import GenomeRegistry
from genechain.species_data import make_genes


class TestMultiSpecies(unittest.TestCase):
    def setUp(self):
        self.reg = GenomeRegistry(IPFSStore(tempfile.mkdtemp()), PedigreeDAG())
        self.heo = self.reg.mint_species("heo")
        self.ga = self.reg.mint_species("ga")
        self.lua = self.reg.mint_species("lua")

    def test_moi_loai_dung_300_gene_bat_bien(self):
        for blk in (self.heo, self.ga, self.lua):
            self.assertEqual(len(blk.gene_cids), 300)
            self.assertEqual(len(set(blk.gene_cids)), 300)  # không trùng CID
            self.assertTrue(self.reg.verify_block(blk.token_id))
        # Sinh lại phải ra đúng hệt (tất định) -> CID không đổi
        again = [self.reg.ipfs.put(g) for g in make_genes("heo")]
        self.assertEqual(sorted(again), self.heo.gene_cids)

    def test_ghep_heo_ga_ra_block_moi_300_gene_tu_cha_me(self):
        child = self.reg.synthesize(self.heo.token_id, self.ga.token_id, "HG", "Eve")
        self.assertEqual(len(child.gene_cids), 300)
        # Mọi gene của con đều là gene gốc bất biến của heo hoặc gà — không gene lạ, không sửa đổi
        self.assertTrue(set(child.gene_cids) <= set(self.heo.gene_cids + self.ga.gene_cids))
        comp = self.reg.composition_of(child.token_id)
        self.assertEqual(comp["heo"]["genes"] + comp["ga"]["genes"], 300)
        self.assertTrue(140 <= comp["heo"]["genes"] <= 160)  # xấp xỉ 50/50 theo từng trait

    def test_ghep_3_loai_truy_xuat_duoc_ca_3(self):
        hg = self.reg.synthesize(self.heo.token_id, self.ga.token_id, "HG", "Eve")
        tri = self.reg.synthesize(hg.token_id, self.lua.token_id, "HGL", "Eve")
        comp = self.reg.composition_of(tri.token_id)
        self.assertEqual(set(comp), {"heo", "ga", "lua"})
        self.assertEqual(sum(v["genes"] for v in comp.values()), 300)
        self.assertAlmostEqual(comp["lua"]["pct"], 50.0, delta=4)

    def test_merkle_proof(self):
        cid = self.heo.gene_cids[0]
        p = self.reg.prove_gene(self.heo.token_id, cid)
        self.assertTrue(p["verified"])
        self.assertLessEqual(len(p["proof"]), 9)  # ceil(log2(300)) = 9
        # Gene của gà không thuộc block heo
        self.assertFalse(self.reg.prove_gene(self.heo.token_id, self.ga.gene_cids[0])["in_block"])


if __name__ == "__main__":
    unittest.main()
