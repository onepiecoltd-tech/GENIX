#!/usr/bin/env python3
"""Sinh ten Viet / Han Viet cho toan bo 31.189 loai trong game (khong dung ten Latin/tieng Anh).

  - 78 loai noi bat: giu ten Viet that (data/game_data.json, PORTRAITS, server_names.json) + sua vai ten con tu nuoc ngoai
  - Con lai: "<ten nhom tieng Viet> <hieu Han Viet>", vi du "Co Xich Van", "Chuot Bich Long".
    Ten nhom lay theo ho > bo > lop sinh hoc (bang tay ben duoi); hieu Han Viet sinh co dinh tu taxid (khong ngau nhien giua cac lan chay).
    DAY LA TEN TRONG GAME, khong phai ten dan gian that cua loai.
Dau ra: data/ten_viet.json  {taxid: ten}
"""
import json
import random
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ---- ten that cua loai noi bat bi lan tu nuoc ngoai -> thay bang tu Viet ----
FIX = {39947: "Lúa Nhật Bản", 28377: "Thằn lằn cổ quạt xanh", 8090: "Cá lúa Nhật Bản", 6239: "Giun tròn nhỏ",
       3702: "Cải tai chuột", 38626: "Gấu túi", 9317: "Chuột túi xám"}

FAMILY = {
 # thuc vat
 "Poaceae": "Cỏ", "Asteraceae": "Cúc", "Rosaceae": "Tường vi", "Fabaceae": "Đậu", "Orchidaceae": "Lan", "Brassicaceae": "Cải",
 "Lamiaceae": "Bạc hà", "Apiaceae": "Ngò", "Solanaceae": "Cà", "Ranunculaceae": "Mao lương", "Scrophulariaceae": "Huyền sâm",
 "Bromeliaceae": "Dứa dại", "Arecaceae": "Cọ", "Lauraceae": "Long não", "Asparagaceae": "Thiên môn", "Theaceae": "Trà",
 "Saxifragaceae": "Tai hùm", "Primulaceae": "Anh thảo", "Amaryllidaceae": "Hành", "Magnoliaceae": "Mộc lan",
 "Campanulaceae": "Chuông", "Malvaceae": "Cẩm quỳ", "Rutaceae": "Cam quýt", "Polygonaceae": "Rau răm", "Fagaceae": "Sồi",
 "Oleaceae": "Nhài", "Sapindaceae": "Vải", "Myrtaceae": "Sim", "Liliaceae": "Bách hợp", "Papaveraceae": "Anh túc",
 "Apocynaceae": "Trúc đào", "Urticaceae": "Tầm ma", "Salicaceae": "Liễu", "Euphorbiaceae": "Đại kích",
 "Berberidaceae": "Hoàng liên", "Vitaceae": "Nho", "Pinaceae": "Thông", "Crassulaceae": "Sen đá", "Gesneriaceae": "Tai voi",
 "Cucurbitaceae": "Bầu bí", "Caryophyllaceae": "Cẩm chướng", "Orobanchaceae": "Cỏ ký sinh", "Aquifoliaceae": "Nhựa ruồi",
 "Caprifoliaceae": "Kim ngân", "Melastomataceae": "Mua", "Amaranthaceae": "Rau dền", "Zingiberaceae": "Gừng",
 "Plantaginaceae": "Mã đề", "Iridaceae": "Diên vĩ", "Araceae": "Ráy", "Lythraceae": "Tử vi", "Celastraceae": "Dây gối",
 "Rubiaceae": "Cà phê", "Gentianaceae": "Long đởm", "Convolvulaceae": "Khoai lang", "Moraceae": "Dâu tằm",
 "Betulaceae": "Bạch dương", "Araliaceae": "Nhân sâm", "Rhamnaceae": "Táo ta", "Cupressaceae": "Bách",
 "Cactaceae": "Xương rồng", "Juglandaceae": "Óc chó", "Bignoniaceae": "Chùm ớt", "Loranthaceae": "Tầm gửi",
 "Acanthaceae": "Ô rô", "Passifloraceae": "Lạc tiên", "Anacardiaceae": "Xoài", "Musaceae": "Chuối", "Begoniaceae": "Thu hải đường",
 "Thymelaeaceae": "Trầm", "Boraginaceae": "Vòi voi",
 # con trung
 "Nymphalidae": "Bướm nâu", "Papilionidae": "Bướm phượng", "Pieridae": "Bướm trắng", "Hesperiidae": "Bướm đêm nhỏ",
 "Erebidae": "Ngài", "Noctuidae": "Ngài", "Sphingidae": "Ngài diều", "Crambidae": "Ngài",
 "Cicadellidae": "Rầy", "Aphididae": "Rệp", "Pentatomidae": "Bọ xít", "Gerridae": "Bọ nước",
 "Culicidae": "Muỗi", "Chironomidae": "Muỗi nhỏ", "Syrphidae": "Ruồi hoa", "Sarcophagidae": "Ruồi xám", "Tephritidae": "Ruồi đục quả",
 "Drosophilidae": "Ruồi giấm", "Curculionidae": "Mọt", "Cerambycidae": "Bọ sừng dài", "Chrysomelidae": "Bọ lá",
 "Formicidae": "Kiến", "Acrididae": "Châu chấu", "Tettigoniidae": "Muỗm", "Termitidae": "Mối",
 # ca / thu / chim / bo sat / luong cu
 "Cyprinidae": "Cá chép", "Leuciscidae": "Cá tuế", "Gobionidae": "Cá đục", "Gobiidae": "Cá bống", "Nemacheilidae": "Cá chạch",
 "Cichlidae": "Cá rô phi", "Salmonidae": "Cá hồi", "Serranidae": "Cá mú", "Tetraodontidae": "Cá nóc", "Clupeidae": "Cá trích",
 "Syngnathidae": "Cá ngựa", "Sebastidae": "Cá mù làn", "Cottidae": "Cá sơn", "Xenocyprididae": "Cá mè", "Danionidae": "Cá cơm nước ngọt",
 "Bovidae": "Linh dương", "Cervidae": "Hươu", "Muridae": "Chuột", "Cricetidae": "Chuột đồng", "Sciuridae": "Sóc",
 "Cercopithecidae": "Khỉ", "Vespertilionidae": "Dơi", "Soricidae": "Chuột chù",
 "Psittacidae": "Vẹt", "Phasianidae": "Trĩ", "Fringillidae": "Chim sẻ", "Lacertidae": "Thằn lằn", "Ranidae": "Ếch",
 "Ixodidae": "Ve", "Argasidae": "Ve mềm", "Unionidae": "Trai",
}
ORDER = {
 # thuc vat
 "Poales": "Cỏ", "Lamiales": "Hoa môi", "Asparagales": "Thiên môn", "Rosales": "Tường vi", "Asterales": "Cúc", "Fabales": "Đậu",
 "Ericales": "Đỗ quyên", "Ranunculales": "Mao lương", "Caryophyllales": "Cẩm chướng", "Malpighiales": "Mộc", "Brassicales": "Cải",
 "Apiales": "Ngò", "Saxifragales": "Tai hùm", "Solanales": "Cà", "Sapindales": "Bồ hòn", "Myrtales": "Sim", "Gentianales": "Long đởm",
 "Fagales": "Sồi", "Liliales": "Bách hợp", "Malvales": "Cẩm quỳ", "Arecales": "Cọ", "Laurales": "Long não", "Magnoliales": "Mộc lan",
 "Polypodiales": "Dương xỉ", "Cucurbitales": "Bầu bí", "Zingiberales": "Gừng", "Alismatales": "Thủy thảo", "Dipsacales": "Kim ngân",
 "Vitales": "Nho", "Pinales": "Thông", "Cupressales": "Bách", "Cornales": "Giổi", "Aquifoliales": "Nhựa ruồi", "Santalales": "Tầm gửi",
 "Celastrales": "Dây gối", "Piperales": "Tiêu", "Boraginales": "Vòi voi", "Dioscoreales": "Củ mài", "Geraniales": "Phong lữ",
 "Nymphaeales": "Súng", "Ephedrales": "Ma hoàng", "Isoetales": "Thạch tùng nước", "Cycadales": "Tuế", "Commelinales": "Thài lài",
 "Araucariales": "Tùng khổng lồ", "Proteales": "Sen cạn", "Oxalidales": "Chua me", "Zygophyllales": "Gai dầu", "Pandanales": "Dứa thơm",
 "Austrobaileyales": "Hồi", "Jungermanniales": "Rêu tản", "Hypnales": "Rêu", "Orthotrichales": "Rêu",
 # con trung va chan khop
 "Lepidoptera": "Bướm", "Hemiptera": "Bọ xít", "Diptera": "Ruồi", "Coleoptera": "Cánh cứng", "Hymenoptera": "Ong",
 "Orthoptera": "Châu chấu", "Blattodea": "Gián", "Trichoptera": "Cánh lông", "Mantodea": "Bọ ngựa", "Neuroptera": "Cánh lưới",
 "Odonata": "Chuồn chuồn", "Plecoptera": "Phù du đá", "Ephemeroptera": "Phù du", "Psocodea": "Rận sách", "Thysanoptera": "Bọ trĩ",
 "Phasmatodea": "Bọ que", "Mecoptera": "Bọ cạp bay", "Siphonaptera": "Bọ chét", "Raphidioptera": "Cánh lưới",
 "Ixodida": "Ve", "Araneae": "Nhện", "Trombidiformes": "Mạt", "Mesostigmata": "Mạt", "Sarcoptiformes": "Mạt",
 "Decapoda": "Tôm cua", "Amphipoda": "Bọ biển", "Stomatopoda": "Tôm tít", "Balanomorpha": "Hà biển", "Diplostraca": "Bọ nước ngọt",
 # ca
 "Cypriniformes": "Cá chép", "Perciformes": "Cá rô", "Siluriformes": "Cá trê", "Gobiiformes": "Cá bống", "Tetraodontiformes": "Cá nóc",
 "Cichliformes": "Cá rô phi", "Pleuronectiformes": "Cá bơn", "Syngnathiformes": "Cá ngựa", "Scombriformes": "Cá thu", "Clupeiformes": "Cá trích",
 "Anguilliformes": "Cá chình", "Cyprinodontiformes": "Cá bảy màu", "Salmoniformes": "Cá hồi", "Centrarchiformes": "Cá vược",
 "Characiformes": "Cá răng nhọn", "Carangiformes": "Cá khế", "Gadiformes": "Cá tuyết", "Lutjaniformes": "Cá hồng", "Spariformes": "Cá tráp",
 "Labriformes": "Cá bàng chài", "Beloniformes": "Cá nhái", "Anabantiformes": "Cá rô đồng", "Acipenseriformes": "Cá tầm", "Lophiiformes": "Cá cần câu",
 "Atheriniformes": "Cá suốt", "Osteoglossiformes": "Cá thát lát", "Aulopiformes": "Cá mối", "Blenniiformes": "Cá mào gà", "Mugiliformes": "Cá đối",
 "Myctophiformes": "Cá đèn lồng", "Beryciformes": "Cá lông", "Chaetodontiformes": "Cá bướm", "Acropomatiformes": "Cá biển sâu",
 "Alepocephaliformes": "Cá biển sâu", "Osmeriformes": "Cá bạc", "Carcharhiniformes": "Cá mập", "Rajiformes": "Cá đuối", "Myliobatiformes": "Cá đuối",
 "Petromyzontiformes": "Cá mút đá",
 # thu
 "Rodentia": "Chuột", "Artiodactyla": "Thú móng guốc", "Primates": "Khỉ", "Carnivora": "Thú dữ", "Chiroptera": "Dơi", "Eulipotyphla": "Chuột chù",
 "Lagomorpha": "Thỏ", "Perissodactyla": "Ngựa rừng", "Diprotodontia": "Thú có túi", "Cingulata": "Thú giáp", "Macroscelidea": "Chuột voi", "Pilosa": "Thú lười",
 # chim
 "Passeriformes": "Chim sẻ", "Psittaciformes": "Vẹt", "Charadriiformes": "Chim biển", "Galliformes": "Gà rừng", "Anseriformes": "Vịt trời",
 "Gruiformes": "Sếu", "Accipitriformes": "Diều hâu", "Columbiformes": "Bồ câu", "Pelecaniformes": "Cò", "Piciformes": "Gõ kiến",
 "Apodiformes": "Yến", "Procellariiformes": "Hải âu", "Strigiformes": "Cú", "Falconiformes": "Chim cắt",
 # bo sat / luong cu
 "Squamata": "Thằn lằn", "Testudines": "Rùa", "Crocodylia": "Cá sấu", "Anura": "Ếch", "Caudata": "Sa giông", "Gymnophiona": "Ếch không chân",
 # than mem, giun, da gai...
 "Neogastropoda": "Ốc", "Littorinimorpha": "Ốc", "Nudibranchia": "Hải sên", "Stylommatophora": "Ốc sên", "Architaenioglossa": "Ốc", "Trochida": "Ốc",
 "Unionida": "Trai", "Venerida": "Nghêu", "Mytilida": "Vẹm", "Ostreida": "Hàu", "Cardiida": "Sò", "Myida": "Ngao",
 "Octopoda": "Bạch tuộc", "Sepiida": "Mực nang", "Oegopsida": "Mực ống", "Chitonida": "Ốc mai",
 "Scleractinia": "San hô", "Malacalcyonacea": "San hô mềm", "Scleralcyonacea": "San hô mềm", "Zoantharia": "San hô", "Actiniaria": "Hải quỳ",
 "Siphonophorae": "Sứa ống", "Rhabditida": "Giun tròn", "Cyclophyllidea": "Sán dây", "Plagiorchiida": "Sán lá", "Phyllodocida": "Giun biển",
 "Sabellida": "Giun biển", "Crassiclitellata": "Giun đất", "Hirudinida": "Đỉa", "Amphilepidida": "Đuôi rắn biển", "Aspidochirotida": "Hải sâm",
 "Camarodonta": "Nhím biển", "Pantopoda": "Nhện biển",
}
CLASS = {
 "Magnoliopsida": "Hoa", "Liliopsida": "Hoa", "Polypodiopsida": "Dương xỉ", "Pinopsida": "Tùng", "Bryopsida": "Rêu", "Lycopodiopsida": "Thạch tùng",
 "Jungermanniopsida": "Rêu tản", "Gnetopsida": "Ma hoàng", "Cycadopsida": "Tuế", "Marchantiopsida": "Rêu gan", "Anthocerotopsida": "Rêu sừng",
 "Sphagnopsida": "Rêu than bùn", "Ginkgoopsida": "Bạch quả",
 "Insecta": "Côn trùng", "Actinopteri": "Cá", "Mammalia": "Thú", "Aves": "Chim", "Malacostraca": "Giáp xác", "Gastropoda": "Ốc",
 "Amphibia": "Lưỡng cư", "Lepidosauria": "Bò sát", "Arachnida": "Nhện", "Anthozoa": "San hô", "Bivalvia": "Sò", "Chondrichthyes": "Cá sụn",
 "Chromadorea": "Giun tròn", "Cephalopoda": "Mực", "Polychaeta": "Giun biển", "Cestoda": "Sán dây", "Trematoda": "Sán lá", "Clitellata": "Giun đất",
 "Thecostraca": "Hà biển", "Echinoidea": "Nhím biển", "Demospongiae": "Bọt biển", "Branchiopoda": "Bọ nước ngọt", "Hydrozoa": "Thủy tức",
 "Monogenea": "Sán lá", "Collembola": "Bọ đuôi bật", "Asteroidea": "Sao biển", "Ascidiacea": "Bao biển", "Holothuroidea": "Hải sâm",
 "Ophiuroidea": "Đuôi rắn biển", "Enoplea": "Giun tròn", "Diplopoda": "Cuốn chiếu", "Polyplacophora": "Ốc mai", "Copepoda": "Giáp xác nhỏ",
 "Hyperoartia": "Cá mút đá", "Pycnogonida": "Nhện biển", "Crinoidea": "Huệ biển", "Scyphozoa": "Sứa", "Cladistia": "Cá vây tay",
 "Chilopoda": "Rết", "Myxini": "Cá nhớt", "Leptocardii": "Cá bao", "Ostracoda": "Giáp xác nhỏ", "Merostomata": "Cua móng ngựa",
}
BUCKET = {"mammal": "Thú", "vertebrate": "Linh vật", "invertebrate": "Trùng", "plant": "Thảo mộc", "fungi": "Nấm"}

HV_A = ["Xích", "Thanh", "Hoàng", "Bạch", "Huyền", "Tử", "Kim", "Ngân", "Bích", "Lam", "Hồng", "Mặc", "Thương", "Ngọc", "Đan", "Lục",
        "Châu", "Hàn", "Viêm", "Huyết", "Tinh", "Thiên", "Địa", "Vân", "Phong", "Lôi", "Linh", "Thần", "Dạ", "Nguyệt", "Nhật", "Sương",
        "Tuyết", "Băng", "Hỏa", "Mộc", "Thổ", "Thủy", "Cổ", "Nguyên"]
HV_B = ["Vân", "Phong", "Lôi", "Hỏa", "Sương", "Tuyết", "Nguyệt", "Tinh", "Hà", "Hải", "Lâm", "Thạch", "Băng", "Viêm", "Liên", "Mai",
        "Trúc", "Tùng", "Cúc", "Lan", "Diệp", "Thảo", "Hương", "Linh", "Ảnh", "Quang", "Dạ", "Nhật", "Long", "Phượng", "Lân", "Hạc",
        "Ưng", "Lộc", "Ngưu", "Xà", "Quy", "Sơn", "Cốc", "Nhai", "Khê", "Tuyền", "Đảo", "Nguyên", "Lĩnh", "Điểu", "Vũ", "Dực", "Ngạc",
        "Thiền", "Hồ", "Châu", "Ngọc", "Kim", "Bích", "Tước"]
HV_C = ["Tiểu", "Đại", "Trung", "Thượng", "Hạ", "Nam", "Bắc", "Đông", "Tây", "Cổ"]


def group_noun(r):
    taxid, _sci, bucket, _g, _b, cls, order, fam, snake = r
    if snake:
        return "Rắn"
    return FAMILY.get(fam) or ORDER.get(order) or CLASS.get(cls) or BUCKET.get(bucket, "Linh vật")


def epithets(noun):
    """Day hieu Han Viet xao tron co dinh theo ten nhom (crc32) — du cho vai chuc nghin loai moi nhom."""
    rng = random.Random(zlib.crc32(noun.encode("utf-8")))
    two = [a + " " + b for a in HV_A for b in HV_B if a != b]
    rng.shuffle(two)
    three = [c + " " + t for c in HV_C for t in two[:600]]
    rng.shuffle(three)
    return two + three


def main():
    rows = json.loads((ROOT / "data" / "game_species_all.json").read_text(encoding="utf-8"))["species"]
    real = {}
    for k, v in json.loads((ROOT / "data" / "server_names.json").read_text(encoding="utf-8")).items():
        real[int(k)] = v["vn"]
    for sp in json.loads((ROOT / "data" / "game_data.json").read_text(encoding="utf-8"))["species"]:
        real[sp["taxid"]] = sp["vn"]
    sys.path.insert(0, str(ROOT / "examples"))
    import build_shk_game as bg
    for t, vn, _g in bg.PORTRAITS:
        real[t] = vn
    real.update(FIX)
    used = set(real.values())
    out = {str(t): v for t, v in real.items()}
    pools, pos = {}, {}
    for r in sorted(rows, key=lambda r: r[0]):
        if r[0] in real:
            continue
        noun = group_noun(r)
        pool = pools.setdefault(noun, epithets(noun))
        i = pos.get(noun, 0)
        while True:
            name = noun + " " + pool[i]
            i += 1
            if name not in used:
                break
        pos[noun] = i
        used.add(name)
        out[str(r[0])] = name
    (ROOT / "data" / "ten_viet.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Da ghi data/ten_viet.json: {len(out)} ten ({len(real)} ten that, {len(out) - len(real)} ten sinh)")
    big = sorted(pos.items(), key=lambda kv: -kv[1])[:5]
    print("Nhom lon nhat:", big)


if __name__ == "__main__":
    main()
