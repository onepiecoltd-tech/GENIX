"""
Block Registry v5 — mô hình đúng yêu cầu của chủ dự án:
  * KHÔNG dữ liệu ảo: mọi gene đều là gene thật từ NCBI Gene (bulk gene_info).
  * 1 mã gen = 1 block: mỗi gene chuẩn (canonical gene) được định danh bằng
    block_id = SHA-256(symbol chuẩn + loại gene) — bất biến, duy nhất toàn hệ thống.
  * Gene TRÙNG nhau giữa các loài = block DÙNG CHUNG: heo và gà cùng có gene
    IGF1 thì cả hai cùng trỏ tới đúng 1 block IGF1, không nhân đôi.
    (Đã đo thật: heo ∩ gà = 13.399 block chung — xem data/shared_genes_report.json)
  * Mỗi bản ghi gene thật trong 1 loài (occurrences) trỏ tới đúng 1 block;
    SpeciesBlock của loài = Merkle root trên tập block_id phân biệt của loài đó.

Lưu trữ: SQLite (data/genechain_blocks.db) — 52,3 triệu occurrences không thể
lưu thành từng file JSON. Build streaming từ 4 file bulk NCBI, có checkpoint
theo từng file (bảng meta), chạy lại sẽ bỏ qua file đã xong.

Định nghĩa 'trùng nhau': cùng symbol chuẩn của cơ quan danh pháp
(Symbol_from_nomenclature_authority trong gene_info, fallback về Symbol),
không phân biệt hoa/thường + cùng loại gene. Đây là định danh gene tương đồng
(ortholog) theo danh pháp chuẩn — trình tự ADN cụ thể từng loài vẫn khác nhau
và nằm ở occurrences (GeneID, nhiễm sắc thể, vị trí riêng của từng loài).
"""
from __future__ import annotations
import gzip, hashlib, json, os, sqlite3, time
from .merkle import merkle_root

GROUP_FILES = [
    ("All_Mammalia.gene_info.gz", "animal"),
    ("All_Plants.gene_info.gz", "plant"),
    ("All_Invertebrates.gene_info.gz", "animal"),
    ("All_Non-mammalian_vertebrates.gene_info.gz", "animal"),
]
BATCH = 50000


def block_id_of(symbol_canonical: str, gene_type: str) -> str:
    raw = f"{symbol_canonical.upper()}|{gene_type}".encode("utf-8")
    return "bafy" + hashlib.sha256(raw).hexdigest()[:52]


def _canonical(c) -> str:
    sym = c[10] if len(c) > 10 and c[10] not in ("-", "") else c[2]
    return sym.strip()


class BlockRegistry:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=OFF")   # build hàng loạt: tốc độ > an toàn giao dịch
        self.conn.execute("PRAGMA cache_size=-64000")
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS blocks(
                block_id TEXT PRIMARY KEY, symbol TEXT, gene_type TEXT, full_name TEXT);
            CREATE TABLE IF NOT EXISTS occurrences(
                taxid INTEGER, gene_id TEXT, block_id TEXT, chromosome TEXT, map_location TEXT);
            -- occurrences cố ý KHÔNG khoá chính khi nạp (nạp nối tiếp cho nhanh);
            -- index được dựng sau khi nạp xong, trước pha tính Merkle root.
            CREATE TABLE IF NOT EXISTS species(
                taxid INTEGER PRIMARY KEY, kingdom TEXT, gene_records INTEGER,
                distinct_blocks INTEGER, merkle_root TEXT);
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
        """)
        self.conn.commit()

    # ---------- BUILD ----------
    def _file_done(self, fname):
        cur = self.conn.execute("SELECT value FROM meta WHERE key=?", (f"done:{fname}",))
        return cur.fetchone() is not None

    def _cleanup_partial(self, path):
        """Nếu file chưa done nhưng đã có dữ liệu dở (bị ngắt giữa chừng), xoá
        occurrences của các taxon thuộc file này để nạp lại không bị trùng.
        Các taxon của 4 file nhóm là rời nhau nên xoá theo taxid là an toàn."""
        taxids = set()
        with gzip.open(path, "rb") as f:
            f.readline()
            for raw in f:
                taxids.add(int(raw.split(b"\t", 1)[0]))
        sample = next(iter(taxids))
        exists = self.conn.execute("SELECT 1 FROM occurrences WHERE taxid=? LIMIT 1",
                                   (sample,)).fetchone()
        if exists:
            print(f"[blocks] Dọn dữ liệu dở của {len(taxids):,} taxon trước khi nạp lại", flush=True)
            tids = list(taxids)
            for i in range(0, len(tids), 500):
                self.conn.executemany("DELETE FROM occurrences WHERE taxid=?",
                                      [(t,) for t in tids[i:i + 500]])
                self.conn.commit()

    def _meta_get(self, key):
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def _meta_set(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO meta VALUES(?,?)", (key, str(value)))

    def _cleanup_gap(self, path, progress):
        """Xoá occurrences của MỌI taxon thuộc file này có taxid > progress
        (taxon dở + taxon trọn chưa kịp checkpoint) trong 1 lần quét bảng,
        để nạp lại không trùng (occurrences không có khoá duy nhất)."""
        taxids = set()
        with gzip.open(path, "rb") as f:
            f.readline()
            for raw in f:
                t = int(raw.split(b"\t", 1)[0])
                if t > progress:
                    taxids.add(t)
        if not taxids:
            return
        print(f"[blocks] Dọn {len(taxids):,} taxon sau checkpoint {progress} để nạp lại sạch", flush=True)
        self.conn.execute("CREATE TEMP TABLE IF NOT EXISTS gap_taxa(taxid INTEGER PRIMARY KEY)")
        self.conn.execute("DELETE FROM gap_taxa")
        self.conn.executemany("INSERT OR IGNORE INTO gap_taxa VALUES(?)", [(t,) for t in taxids])
        self.conn.execute("DELETE FROM occurrences WHERE taxid IN (SELECT taxid FROM gap_taxa)")
        self.conn.execute("DROP TABLE gap_taxa")
        self.conn.commit()

    def dedupe_occurrences(self):
        """Khử trùng lặp toàn cục theo khoá tự nhiên (taxid, gene_id) — mỗi gene
        của NCBI xuất hiện đúng 1 lần cho 1 loài. Chạy 1 lần trước pha Merkle
        root (cờ meta deduped:1), sửa mọi trùng lặp do các lần nạp lại cũ."""
        if self._meta_get("deduped:1"):
            print("[blocks] Đã khử trùng lặp trước đó, bỏ qua", flush=True)
            return
        t0 = time.time()
        before = self.conn.execute("SELECT COUNT(*) FROM occurrences").fetchone()[0]
        self.conn.execute("""DELETE FROM occurrences WHERE rowid NOT IN
                             (SELECT MIN(rowid) FROM occurrences GROUP BY taxid, gene_id)""")
        self.conn.commit()
        after = self.conn.execute("SELECT COUNT(*) FROM occurrences").fetchone()[0]
        self._meta_set("deduped:1", "1")
        self.conn.commit()
        print(f"[blocks] Khử trùng lặp: {before:,} -> {after:,} dòng "
              f"(bỏ {before-after:,}) trong {time.time()-t0:.0f}s", flush=True)

    def build_file(self, bulk_dir, fname, kingdom):
        """Nạp 1 file theo ranh giới taxon (file NCBI đã sắp xếp theo tax_id):
        - meta progress:<file> = taxid cuối cùng đã commit; chạy lại bỏ qua mọi
          taxon <= progress, nên bị ngắt chỉ mất tối đa 200 taxon chưa commit.
        - Taxon khổng lồ bị flush giữa chừng được ghi meta partial:<file>;
          chạy lại xoá riêng taxon đó rồi nạp lại — không bao giờ trùng.
        - Dữ liệu dở từ cơ chế cũ (chưa có progress) được dọn 1 lần duy nhất.
        """
        if self._file_done(fname):
            print(f"[blocks] Bỏ qua (đã xong): {fname}", flush=True)
            return
        path = os.path.join(bulk_dir, fname)
        prog_key, part_key = f"progress:{fname}", f"partial:{fname}"
        progress = int(self._meta_get(prog_key) or 0)
        if progress == 0 and self._meta_get(part_key) is None:
            self._cleanup_partial(path)  # dọn dở dang của cơ chế batch cũ, chỉ 1 lần
        elif self._meta_get(part_key) is not None or progress > 0:
            # occurrences KHÔNG có khoá duy nhất: mọi dòng đã commit của các taxon
            # > progress (gồm taxon dở và các taxon trọn bị flush giữa chừng commit
            # kèm) phải xoá sạch trước khi nạp lại, nếu không sẽ trùng lặp.
            self._cleanup_gap(path, progress)
            self.conn.execute("DELETE FROM meta WHERE key=?", (part_key,))
            self.conn.commit()

        t0, n = time.time(), 0
        blocks_batch, occ_batch = [], []
        cache = {}
        cur_taxid, taxa_done = None, 0
        last_complete = progress  # taxon trọn cuối cùng đã nằm trong batch/commit

        def commit_progress(upto_taxid, mid_taxon=None):
            nonlocal progress
            self._flush(blocks_batch, occ_batch)
            blocks_batch.clear(); occ_batch.clear()
            if upto_taxid and upto_taxid > progress:
                progress = upto_taxid
                self._meta_set(prog_key, upto_taxid)
                # taxon trước đã nạp trọn: xoá cờ partial của nó để lần chạy lại
                # không xoá nhầm dữ liệu đã hoàn chỉnh (xung đột progress/partial)
                self.conn.execute("DELETE FROM meta WHERE key=?", (part_key,))
            if mid_taxon:
                self._meta_set(part_key, mid_taxon)
            self.conn.commit()

        with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
            f.readline()
            for line in f:
                c = line.rstrip("\n").split("\t")
                if len(c) < 11:
                    continue
                taxid = int(c[0])
                if taxid <= progress:
                    continue
                if cur_taxid is None:
                    cur_taxid = taxid
                elif taxid != cur_taxid:
                    last_complete = cur_taxid
                    taxa_done += 1
                    if taxa_done % 200 == 0:
                        commit_progress(cur_taxid)
                    cur_taxid = taxid
                sym = _canonical(c)
                if not sym or sym == "-":
                    continue
                key = (sym, c[9])
                bid = cache.get(key)
                if bid is None:
                    bid = block_id_of(sym, c[9])
                    cache[key] = bid
                    full_name = c[11] if len(c) > 11 and c[11] not in ("-", "") else c[8]
                    blocks_batch.append((bid, sym, c[9], full_name))
                occ_batch.append((taxid, c[1], bid, c[6], c[7]))
                n += 1
                if len(occ_batch) >= BATCH:
                    # flush giữa taxon: tiến progress tới taxon trọn cuối cùng
                    # trong batch (chúng đã được commit kèm) + ghi partial
                    commit_progress(last_complete, mid_taxon=cur_taxid)
        commit_progress(cur_taxid)
        self.conn.execute("DELETE FROM meta WHERE key IN (?,?)", (prog_key, part_key))
        self._meta_set(f"done:{fname}", "1")
        self.conn.commit()
        print(f"[blocks] Xong {fname}: {n:,} gene trong {time.time()-t0:.0f}s", flush=True)

    def _flush(self, blocks_batch, occ_batch):
        # KHÔNG commit ở đây: commit_progress commit dữ liệu + meta trong CÙNG
        # 1 giao dịch, để checkpoint không bao giờ lệch với dữ liệu khi bị ngắt.
        self.conn.executemany("INSERT OR IGNORE INTO blocks VALUES(?,?,?,?)", blocks_batch)
        self.conn.executemany("INSERT OR IGNORE INTO occurrences VALUES(?,?,?,?,?)", occ_batch)

    def build_species_roots(self, names: dict = None):
        """Tính Merkle root cho từng loài trên tập block phân biệt của loài."""
        print("[blocks] Dựng index occurrences(taxid, block_id)…", flush=True)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_occ_taxid ON occurrences(taxid, block_id)")
        self.conn.commit()
        taxids = [r[0] for r in self.conn.execute("SELECT DISTINCT taxid FROM occurrences")]
        done_species = {r[0] for r in self.conn.execute("SELECT taxid FROM species")}
        for i, taxid in enumerate(taxids):
            if taxid in done_species:
                continue
            rows = self.conn.execute(
                "SELECT COUNT(*), COUNT(DISTINCT block_id) FROM occurrences WHERE taxid=?",
                (taxid,)).fetchone()
            block_ids = [r[0] for r in self.conn.execute(
                "SELECT DISTINCT block_id FROM occurrences WHERE taxid=? ORDER BY block_id", (taxid,))]
            kingdom = self.conn.execute(
                "SELECT value FROM meta WHERE key=?", (f"kingdom:{taxid}",)).fetchone()
            self.conn.execute(
                "INSERT OR REPLACE INTO species VALUES(?,?,?,?,?)",
                (taxid, kingdom[0] if kingdom else "", rows[0], rows[1], merkle_root(block_ids)))
            if i % 1000 == 999:
                self.conn.commit()  # checkpoint từng 1.000 loài, ngắt giữa chừng chạy tiếp được
        self.conn.commit()
        print(f"[blocks] Đã tính Merkle root cho {len(taxids):,} loài", flush=True)

    def build_all(self, root):
        bulk_dir = os.path.join(root, "data", "bulk")
        # ghi kingdom theo taxid từ catalog có sẵn (nếu có)
        cat_path = os.path.join(root, "data", "catalog_all_species.json")
        if os.path.exists(cat_path):
            catalog = json.load(open(cat_path, encoding="utf-8"))
            self.conn.executemany("INSERT OR REPLACE INTO meta VALUES(?,?)",
                                  [(f"kingdom:{t}", v["kingdom"]) for t, v in catalog.items()])
            self.conn.commit()
        for fname, _k in GROUP_FILES:
            self.build_file(bulk_dir, fname, _k)
        self.dedupe_occurrences()
        self.build_species_roots()
        nb = self.conn.execute("SELECT COUNT(*) FROM blocks").fetchone()[0]
        no = self.conn.execute("SELECT COUNT(*) FROM occurrences").fetchone()[0]
        print(f"[blocks] HOÀN TẤT: {nb:,} block gene chuẩn | {no:,} occurrences (gene thật)", flush=True)

    # ---------- TRUY VẤN ----------
    def shared_blocks(self, taxid_a: int, taxid_b: int):
        """Số block dùng chung giữa 2 loài + mẫu. Đây là phép INTERSECT trên block_id."""
        cnt = self.conn.execute("""
            SELECT COUNT(*) FROM (SELECT DISTINCT block_id FROM occurrences WHERE taxid=?
            INTERSECT SELECT DISTINCT block_id FROM occurrences WHERE taxid=?)""",
            (taxid_a, taxid_b)).fetchone()[0]
        sample = [r[0] for r in self.conn.execute("""
            SELECT b.symbol FROM blocks b WHERE b.block_id IN (
              SELECT DISTINCT block_id FROM occurrences WHERE taxid=?
              INTERSECT SELECT DISTINCT block_id FROM occurrences WHERE taxid=?)
            ORDER BY b.symbol LIMIT 15""", (taxid_a, taxid_b))]
        return cnt, sample

    def species_info(self, taxid: int):
        return self.conn.execute("SELECT * FROM species WHERE taxid=?", (taxid,)).fetchone()

    def block_info(self, symbol: str):
        return self.conn.execute(
            "SELECT * FROM blocks WHERE symbol=? COLLATE NOCASE", (symbol,)).fetchall()
