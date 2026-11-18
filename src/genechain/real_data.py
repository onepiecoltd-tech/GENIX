"""
Loader dữ liệu gen THẬT từ NCBI Gene (E-utilities API — miễn phí, không cần API key,
giới hạn 3 request/giây khi không có key; có key miễn phí thì 10/giây).

Kênh này đã được kiểm chứng trực tiếp khi phát triển:
  heo (taxid 9823): 89.841 bản ghi gene · gà (9031): 58.600 · lúa (4530): 102.125

Mỗi gene thật -> 1 gene-block trong GeneChain:
  code  = "NCBI:<GeneID>"   (GeneID là định danh bất biến toàn cầu của NCBI)
  + symbol chính thức, mô tả, nhiễm sắc thể, vị trí start/end trên genome, độ dài bp
Sau khi kéo về, gene được đóng băng vào IPFS (CID) — từ đó bất biến trong hệ thống
kể cả khi NCBI cập nhật cơ sở dữ liệu về sau.

Các kênh thật khác dùng được cùng loader-pattern này (xem README):
  Ensembl REST (rest.ensembl.org / rest.ensemblgenomes.org) — genome + gene + ortholog,
  UniProt REST — protein, NCBI Datasets API — tải cả bộ genome FASTA/GFF,
  RAP-DB / IRGSP (lúa), Animal QTLdb (heo/gà), KEGG, Gene Ontology.
"""
from __future__ import annotations
import json, os, time, urllib.parse, urllib.request

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TAXID = {"heo": 9823, "ga": 9031, "lua": 4530}
TOOL_PARAMS = {"tool": "genechain", "email": "genechain@example.local"}


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "GeneChain/0.2"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_gene_ids(taxid: int, count: int = 300) -> list:
    q = urllib.parse.urlencode({"db": "gene", "term": f"txid{taxid}[Organism]",
                                "retmax": count, "retmode": "json", **TOOL_PARAMS})
    return _get(f"{EUTILS}/esearch.fcgi?{q}")["esearchresult"]["idlist"]


def fetch_summaries(ids: list, chunk: int = 100) -> dict:
    out = {}
    for i in range(0, len(ids), chunk):
        q = urllib.parse.urlencode({"db": "gene", "id": ",".join(ids[i:i + chunk]),
                                    "retmode": "json", **TOOL_PARAMS})
        res = _get(f"{EUTILS}/esummary.fcgi?{q}")["result"]
        for gid in res.get("uids", []):
            out[gid] = res[gid]
        time.sleep(0.4)  # tôn trọng rate limit NCBI
    return out


def to_gene_block(gid: str, s: dict, species_key: str) -> dict:
    genomic = (s.get("genomicinfo") or [{}])[0]
    start, end = genomic.get("chrstart"), genomic.get("chrstop")
    length = abs(end - start) + 1 if isinstance(start, int) and isinstance(end, int) else None
    return {
        "code": f"NCBI:{gid}",
        "name": s.get("name") or s.get("description") or f"Gene {gid}",
        "trait": s.get("genetype") or "gene",
        "chromosome": genomic.get("chrloc") or s.get("chromosome") or "",
        "start": start, "end": end, "length_bp": length,
        "description": s.get("description") or "",
        "origin": species_key,
        "source": "NCBI Gene via E-utilities",
        "taxid": TAXID[species_key],
    }


def load_real_genes(species_key: str, count: int = 300, cache_dir: str = None) -> list:
    """Kéo `count` gene thật của 1 loài (có cache file để không kéo lại)."""
    cache = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache = os.path.join(cache_dir, f"ncbi_{species_key}_{count}.json")
        if os.path.exists(cache):
            with open(cache, encoding="utf-8") as f:
                return json.load(f)
    ids = fetch_gene_ids(TAXID[species_key], count)
    summaries = fetch_summaries(ids)
    genes = [to_gene_block(gid, summaries[gid], species_key) for gid in ids if gid in summaries]
    if cache:
        with open(cache, "w", encoding="utf-8") as f:
            json.dump(genes, f, ensure_ascii=False, indent=1)
    return genes
