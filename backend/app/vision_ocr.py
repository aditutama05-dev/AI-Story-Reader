from __future__ import annotations

import json
from io import BytesIO

from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_IMAGE_EDGE = 1800
MAX_IMAGE_PIXELS = 40_000_000
MAX_COMIC_OCR_RESPONSE_CHARS = 250_000
MAX_COMIC_PANELS = 100
MAX_COMIC_ITEMS = 1_000
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
GENERIC_BINARY_TYPES = {"application/octet-stream", "binary/octet-stream"}

_KIND_LABELS = {
    "dialogue": "Dialog",
    "thought": "Pikiran",
    "caption": "Caption",
    "sfx": "SFX",
    "other": "Teks",
}


def normalize_page_image(content: bytes, content_type: str) -> bytes:
    if not content:
        raise HTTPException(status_code=400, detail="File gambar kosong.")
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Ukuran tiap gambar maksimal 15 MB.")
    declared_type = (content_type or "").split(";", 1)[0].strip().lower()
    if declared_type == "image/jpg":
        declared_type = "image/jpeg"
    if declared_type and declared_type not in ALLOWED_IMAGE_TYPES | GENERIC_BINARY_TYPES:
        raise HTTPException(status_code=415, detail="Gunakan gambar JPG, PNG, atau WEBP.")
    try:
        with Image.open(BytesIO(content)) as source:
            detected_type = Image.MIME.get(source.format)
            if detected_type not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(status_code=415, detail="Isi file bukan gambar JPG, PNG, atau WEBP.")
            if declared_type in ALLOWED_IMAGE_TYPES and declared_type != detected_type:
                raise HTTPException(status_code=415, detail="Tipe gambar tidak cocok dengan isi file.")
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Resolusi gambar terlalu besar. Batas 40 megapiksel per halaman.")
            image = ImageOps.exif_transpose(source).convert("RGB")
            image.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE), Image.Resampling.LANCZOS)
            output = BytesIO()
            image.save(output, format="JPEG", quality=88, optimize=True)
            return output.getvalue()
    except HTTPException:
        raise
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="Gambar tidak dapat dibaca atau rusak.") from exc


def build_ocr_prompt(page_number: int, total_pages: int, direction: str) -> str:
    directions = {
        "rtl": "Manga Jepang: urutan panel dari kanan ke kiri, lalu dari atas ke bawah. Di dalam panel, baca gelembung dari kanan ke kiri sesuai alur visual.",
        "ltr": "Komik kiri-ke-kanan: urutkan panel dari kiri ke kanan, lalu dari atas ke bawah. Di dalam panel, ikuti urutan gelembung yang terlihat.",
        "vertical": "Webtoon/manhwa vertikal: ikuti alur panel dari bagian paling atas ke bawah halaman; di dalam panel baca gelembung sesuai urutan visual.",
    }
    return f"""Analisis halaman komik ini untuk mengekstrak teks yang benar-benar terlihat.

Halaman {page_number} dari {total_pages}. Aturan urutan baca: {directions[direction]}

Keluarkan HANYA satu objek JSON valid tanpa markdown atau teks pembuka/penutup, dengan bentuk:
{{
  "panels": [
    {{
      "order_confidence": "high",
      "items": [
        {{"kind": "dialogue", "balloon": 1, "text": "teks yang terlihat"}},
        {{"kind": "thought", "balloon": 2, "text": "teks pikiran"}},
        {{"kind": "caption", "balloon": null, "text": "teks kotak narasi"}},
        {{"kind": "sfx", "balloon": null, "text": "efek suara"}}
      ]
    }}
  ],
  "warnings": []
}}

Ketentuan:
- Urutkan objek panels menurut urutan baca yang diminta. Urutkan items di dalam setiap panel menurut urutan gelembung/teks yang benar-benar terlihat.
- Satu item mewakili satu gelembung dialog/pikiran atau satu blok teks/caption/SFX. Nomori balloon mulai dari 1 di dalam setiap panel untuk dialog/pikiran; gunakan null untuk caption, SFX, atau teks lain.
- kind hanya boleh dialogue, thought, caption, sfx, atau other. Jangan menebak identitas pembicara.
- order_confidence adalah perkiraan model: high, medium, atau low. Jika tata letak membuat urutan ambigu, gunakan medium/low dan jelaskan singkat di warnings.
- Pertahankan bahasa dan aksara asli. Jangan menerjemahkan, meringkas, memperbaiki, atau menulis ulang.
- Pertahankan ejaan, nama, angka, tanda baca, dan efek suara. Teks yang sebagian tidak terbaca ditandai [tidak terbaca] pada posisi yang tepat; jangan menebak.
- Masukkan semua teks yang terlihat. Jika halaman benar-benar tidak memiliki teks, gunakan "panels": [] dan jelaskan di warnings.
- Jangan mendeskripsikan karakter/latar atau menambahkan peristiwa yang tidak tertulis.
"""


def parse_comic_ocr_response(raw_response: str) -> dict:
    if not isinstance(raw_response, str):
        raise ValueError("Respons OCR harus berupa teks.")
    raw = raw_response.strip()
    if len(raw) > MAX_COMIC_OCR_RESPONSE_CHARS:
        raise ValueError("Respons OCR terlalu besar untuk diproses dengan aman.")
    candidate = raw
    fence = chr(96) * 3
    if candidate.startswith(fence):
        candidate = candidate.split("\n", 1)[-1].rstrip()
        if candidate.endswith(fence):
            candidate = candidate[:-3].rstrip()
    first_brace, last_brace = candidate.find("{"), candidate.rfind("}")
    if first_brace >= 0 and last_brace > first_brace:
        candidate = candidate[first_brace:last_brace + 1]
    try:
        payload = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return {"text": raw, "panels": [], "warnings": ["Respons vision tidak mengikuti struktur JSON; teks dipertahankan tanpa pemetaan panel atau balon dialog."], "structured": False}
    if not isinstance(payload, dict) or not isinstance(payload.get("panels"), list):
        return {"text": raw, "panels": [], "warnings": ["Respons vision tidak memiliki daftar panel yang valid; teks dipertahankan tanpa pemetaan panel atau balon dialog."], "structured": False}

    warnings = []
    raw_warnings = payload.get("warnings", [])
    if isinstance(raw_warnings, list):
        warnings.extend(item.strip()[:300] for item in raw_warnings if isinstance(item, str) and item.strip())
    if len(payload["panels"]) > MAX_COMIC_PANELS:
        warnings.append(f"Respons berisi lebih dari {MAX_COMIC_PANELS} panel; panel tambahan tidak disertakan.")

    blocks, panels = [], []
    cursor = 0
    total_items = 0
    uncertain_panels = []
    for panel_value in payload["panels"][:MAX_COMIC_PANELS]:
        if not isinstance(panel_value, dict):
            continue
        raw_items = panel_value.get("items", [])
        if not isinstance(raw_items, list):
            continue
        normalized_items = []
        for item_value in raw_items:
            if total_items >= MAX_COMIC_ITEMS:
                warnings.append(f"Respons mencapai batas {MAX_COMIC_ITEMS} blok teks; blok tambahan tidak disertakan.")
                break
            if not isinstance(item_value, dict):
                continue
            item_text = item_value.get("text")
            if not isinstance(item_text, str) or not item_text.strip():
                continue
            kind = str(item_value.get("kind", item_value.get("type", "other"))).strip().lower()
            if kind not in _KIND_LABELS:
                kind = "other"
            balloon_value = item_value.get("balloon")
            balloon = None
            if isinstance(balloon_value, int) and not isinstance(balloon_value, bool) and balloon_value > 0:
                balloon = balloon_value
            elif isinstance(balloon_value, str) and balloon_value.strip().isdigit():
                parsed_balloon = int(balloon_value.strip())
                balloon = parsed_balloon if parsed_balloon > 0 else None
            normalized_items.append({"kind": kind, "balloon": balloon, "text": item_text.strip()})
            total_items += 1
        if not normalized_items:
            continue

        confidence = str(panel_value.get("order_confidence", "unspecified")).strip().lower()
        if confidence not in {"high", "medium", "low"}:
            confidence = "unspecified"
        panel_number = len(panels) + 1
        panel_label = f"[Panel {panel_number}]"
        panel_lines = [panel_label]
        panel_cursor = len(panel_label)
        item_records = []
        for sequence, item in enumerate(normalized_items, start=1):
            label = _KIND_LABELS[item["kind"]]
            item_label = f"[{label} {sequence}"
            if item["balloon"] is not None:
                item_label += f" · Balon {item['balloon']}"
            item_label += "] "
            item_start = panel_cursor + 1 + len(item_label)
            item_end = item_start + len(item["text"])
            item_records.append({"sequence": sequence, "kind": item["kind"], "balloon": item["balloon"], "text": item["text"], "source_start": item_start, "source_end": item_end})
            panel_lines.append(item_label + item["text"])
            panel_cursor += 1 + len(item_label) + len(item["text"])

        panel_block = "\n".join(panel_lines)
        if blocks:
            cursor += 1
        panel_start = cursor
        panel_end = panel_start + len(panel_block)
        for item in item_records:
            item["source_start"] += panel_start
            item["source_end"] += panel_start
        panels.append({"panel": panel_number, "order_confidence": confidence, "source_start": panel_start, "source_end": panel_end, "items": item_records})
        blocks.append(panel_block)
        cursor = panel_end
        if confidence in {"medium", "low"}:
            uncertain_panels.append(panel_number)

    if uncertain_panels:
        warnings.append("Urutan baca panel perlu ditinjau pada panel: " + ", ".join(str(number) for number in uncertain_panels) + ".")
    if not panels:
        warnings.append("Model tidak mengembalikan blok teks panel yang dapat digunakan; periksa gambar asli untuk memastikan halaman memang tidak berisi teks.")
    return {"text": "\n".join(blocks), "panels": panels, "warnings": warnings[:20], "structured": True}


def build_comic_source(pages: list[dict]) -> tuple[str, list[dict]]:
    combined_parts, segments = [], []
    cursor = 0
    for index, page in enumerate(pages):
        if index:
            cursor += 2
        prefix = f"[Halaman {page['page']}]\n"
        content_start = cursor + len(prefix)
        page_text = page.get("text", "")
        page["source_start"] = content_start
        page["source_end"] = content_start + len(page_text)
        mapped_panels = []
        for panel in page.get("panels", []):
            panel["source_start"] += content_start
            panel["source_end"] += content_start
            mapped_items = []
            for item in panel.get("items", []):
                item["source_start"] += content_start
                item["source_end"] += content_start
                mapped_items.append({"sequence": item["sequence"], "kind": item["kind"], "balloon": item["balloon"], "source_start": item["source_start"], "source_end": item["source_end"]})
            mapped_panels.append({"panel": panel["panel"], "order_confidence": panel["order_confidence"], "source_start": panel["source_start"], "source_end": panel["source_end"], "items": mapped_items})
        segments.append({"index": page["page"], "filename": page["filename"], "characters": len(page_text), "source_start": page["source_start"], "source_end": page["source_end"], "panels": mapped_panels})
        combined_parts.append(prefix + page_text)
        cursor += len(prefix) + len(page_text)
    return "\n\n".join(combined_parts), segments


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
