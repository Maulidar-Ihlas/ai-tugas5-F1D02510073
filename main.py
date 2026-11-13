import json
import os


def muat_basis_pengetahuan(nama_file="kb_bencana.json"):
    lokasi = os.path.join(os.path.dirname(os.path.abspath(__file__)), nama_file)
    with open(lokasi, "r", encoding="utf-8") as f:
        return json.load(f)


def ambil_pertanyaan_awal(aturan_list):
    semua_hasil = {aturan["maka"] for aturan in aturan_list}
    pertanyaan = []
    for aturan in aturan_list:
        for premis in aturan["jika"]:
            if premis not in semua_hasil and premis not in pertanyaan:
                pertanyaan.append(premis)
    return pertanyaan


def syarat_terpenuhi(aturan, memori):
    if aturan["mode"] == "dan":
        return all(premis in memori for premis in aturan["jika"])
    elif aturan["mode"] == "atau":
        return any(premis in memori for premis in aturan["jika"])
    return False


def forward_chaining(aturan_list, fakta_awal):
    memori = set(fakta_awal)
    jejak_aturan = {}
    log_siklus = []
    siklus = 1

    while True:
        cocok = [
            r for r in aturan_list
            if syarat_terpenuhi(r, memori) and r["maka"] not in memori
        ]
        if not cocok:
            log_siklus.append(f"Siklus {siklus}: tidak ada aturan baru yang cocok, berhenti.")
            break

        aturan_terpilih = cocok[0]
        hasil_baru = aturan_terpilih["maka"]
        memori.add(hasil_baru)
        jejak_aturan[hasil_baru] = aturan_terpilih
        log_siklus.append(
            f"Siklus {siklus}: {aturan_terpilih['id']} -> {hasil_baru}"
        )
        siklus += 1

    return memori, jejak_aturan, log_siklus


def cetak_pohon_alasan(fakta, jejak_aturan, sumber_map, indent=2):
    spasi = " " * indent
    if fakta in jejak_aturan:
        aturan = jejak_aturan[fakta]
        premis_str = ", ".join(aturan["jika"])
        kode_sumber = aturan["sumber"]
        detail_sumber = sumber_map.get(kode_sumber, kode_sumber)
        print(
            f"{spasi}{fakta} <- {aturan['id']} ({premis_str}) [Mode: {aturan['mode']}]"
        )
        print(f"{spasi}   Sumber ({kode_sumber}): {detail_sumber}")
        for p in aturan["jika"]:
            if p in jejak_aturan:
                cetak_pohon_alasan(p, jejak_aturan, sumber_map, indent + 2)


def main():
    kb = muat_basis_pengetahuan()
    aturan_list = kb["aturan"]
    sumber_map = kb["sumber"]
    tindakan_map = kb.get("tindakan", {})

    print("=" * 72)
    print(kb["judul"])
    print("=" * 72)
    print("Jawab setiap kondisi yang teramati dengan 'y' (ya) atau 't' (tidak).\n")

    pertanyaan_awal = ambil_pertanyaan_awal(aturan_list)
    fakta_awal = []

    for idx, tanya in enumerate(pertanyaan_awal, start=1):
        while True:
            jawaban = input(f"{idx}. Apakah {tanya}? (y/t) > ").strip().lower()
            if jawaban in ("y", "ya"):
                fakta_awal.append(tanya)
                break
            elif jawaban in ("t", "tidak"):
                break
            else:
                print("   Input tidak valid. Masukkan 'y' atau 't'.")

    print("\n" + "-" * 72)
    print(
        "Fakta awal:",
        ", ".join(fakta_awal) if fakta_awal else "(tidak ada kondisi yang dipilih)"
    )
    print("-" * 72)

    _, jejak_aturan, log_siklus = forward_chaining(aturan_list, fakta_awal)

    for baris in log_siklus:
        print(baris)

    kesimpulan_akhir = [
        fakta for fakta, aturan in jejak_aturan.items()
        if aturan.get("jenis") == "kesimpulan"
    ]

    print("\n" + "=" * 72)
    if kesimpulan_akhir:
        print("Kesimpulan:", "; ".join(kesimpulan_akhir))
        print("\nAlasan (Jejak Inferensi & Rujukan Sumber):")
        for k in kesimpulan_akhir:
            cetak_pohon_alasan(k, jejak_aturan, sumber_map)

        print("\nSaran Tindakan Kesiapsiagaan:")
        for k in kesimpulan_akhir:
            if k in tindakan_map:
                print(f"  - [{k}]: {tindakan_map[k]}")
    else:
        print("Kesimpulan: Tidak terdeteksi kondisi darurat banjir/longsor berdasarkan input.")
        print("Alasan: Tidak ada kombinasi premis aturan yang terpenuhi sepenuhnya.")

    print("\nCatatan Batas Keberlakuan:")
    print(kb["batas"])
    print("=" * 72)


if __name__ == "__main__":
    main()