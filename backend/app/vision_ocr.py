from __future__ import annotations

from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_EDGE = 1800
MAX_IMAGE_PIXELS = 40_000_000
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


def normalize_page_image(content: bytes, content_type: str) -> bytes:
    if not content:
        raise HTTPException(status_code=400, detail="File gambar kosong.")
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Ukuran tiap gambar maksimal 15 MB.")
    if content_type.lower() not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=415, detail="Gunakan gambar JPG, PNG, atau WEBP.")
    try:
        with Image.open(BytesIO(content)) as source:
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Resolusi gambar terlalu besar. Batas 40 megapiksel per halaman.")
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Gambar tidak dapat dibaca atau rusak.") from exc


def build_ocr_prompt(page_number: int, total_pages: int, direction: str) -> str:
    directions = {
        "rtl": "Manga Jepang: urutan panel dari kanan ke kiri, lalu dari atas ke bawah. Di dalam panel, baca kolom teks vertikal dari kanan ke kiri.",
        "ltr": "Komik kiri-ke-kanan: urutkan panel dari kiri ke kanan, lalu dari atas ke bawah.",
        "vertical": "Webtoon/manhwa vertikal: ikuti alur dari bagian paling atas ke bawah halaman; di dalam panel baca gelembung sesuai urutan visual.",
    }
    return f"""Transkripsikan semua teks yang benar-benar terlihat pada halaman komik ini untuk diproses lebih lanjut oleh pembaca cerita AI.

Halaman {page_number} dari {total_pages}. Aturan urutan baca: {directions[direction]}

Ketentuan wajib:
- Pertahankan teks dalam bahasa dan aksara aslinya sejauh terbaca. Jangan menerjemahkan, meringkas, atau menulis ulang.
- Ikuti urutan panel dan urutan gelembung sesuai arahan di atas.
- Pisahkan panel dengan label [Panel 1], [Panel 2], dan seterusnya.
- Dalam tiap panel, pisahkan dialog tiap gelembung/baris teks. Tandai narasi/kotak caption, dialog, pikiran, dan efek suara (SFX) bila dapat dikenali.
- Pertahankan nama, angka, tanda baca, dan efek suara. Jangan menambahkan dialog yang tidak terlihat.
- Jika sebagian teks tidak terbaca, tulis [tidak terbaca] pada posisi tersebut. Jangan menebak.
- Jangan mendeskripsikan gambar, karakter, atau latar. Keluarkan hanya transkripsi terstruktur.
"""


def build_document_page_prompt(page_number: int, total_pages: int) -> str:
    return f"""Transkripsikan seluruh teks yang benar-benar terlihat pada halaman buku/dokumen hasil scan ini.

Halaman {page_number} dari {total_pages}.

Ketentuan:
- Pertahankan bahasa, aksara, ejaan, nama, angka, tanda baca, dan istilah seperti pada sumber.
- Baca urutan teks sesuai tata letak halaman: kolom dari kiri ke kanan dan atas ke bawah, kecuali tata letak bahasa menunjukkan arah lain.
- Pertahankan pemisahan paragraf, judul, subjudul, daftar, dialog, catatan kaki, dan nomor halaman jika terbaca.
- Jangan meringkas, menerjemahkan, memperbaiki gaya, atau menambahkan penjelasan.
- Jangan mengarang kata yang tidak terlihat. Tandai bagian yang tidak terbaca dengan [tidak terbaca].
- Keluarkan hanya teks hasil transkripsi dengan struktur paragraf yang masuk akal.
"""


def make_openai_vision_content(prompt: str, jpeg_bytes: bytes) -> list[dict]:
    import base64

    encoded = base64.b64encode(jpeg_bytes).decode("ascii")
    return [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}", "detail": "high"}},
    ]


def make_gemini_vision_parts(prompt: str, jpeg_bytes: bytes) -> list[dict]:
    import base64

    encoded = base64.b64encode(jpeg_bytes).decode("ascii")
    return [{"text": prompt}, {"inline_data": {"mime_type": "image/jpeg", "data": encoded}}]
