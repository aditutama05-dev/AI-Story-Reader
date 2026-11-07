from __future__ import annotations

import ipaddress
import socket
import zipfile
import posixpath
import xml.etree.ElementTree as ET
from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlparse

import httpx
from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader

from .source_adapters import extract_generic_html, resolve_source_adapter


MAX_UPLOAD_BYTES = 40 * 1024 * 1024
MAX_URL_BYTES = 8 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 5000
MAX_ARCHIVE_MEMBER_BYTES = 25 * 1024 * 1024
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_PDF_PAGES = 500
MAX_EXTRACTED_TEXT_CHARS = 20_000_000


def _validate_archive_limits(book: zipfile.ZipFile) -> None:
    members = book.infolist()
    if len(members) > MAX_ARCHIVE_ENTRIES:
        raise HTTPException(status_code=413, detail="Arsip berisi terlalu banyak file.")
    total_size = 0
    for member in members:
        name = member.filename.replace("\\", "/")
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise HTTPException(status_code=400, detail="Arsip berisi jalur file yang tidak aman.")
        if member.file_size > MAX_ARCHIVE_MEMBER_BYTES:
            raise HTTPException(status_code=413, detail="Salah satu file di dalam arsip terlalu besar.")
        total_size += member.file_size
        if total_size > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
            raise HTTPException(status_code=413, detail="Ukuran hasil ekstraksi arsip melebihi batas 100 MB.")
def _parse_html(raw: bytes, encoding: str | None = None) -> tuple[str, str, int, str]:
    result = extract_generic_html(raw, encoding)
    return result.title, result.text, result.paragraph_count, result.container


def _clean_html(raw: bytes, encoding: str | None = None) -> tuple[str, str]:
    result = extract_generic_html(raw, encoding)
    return result.title, result.text


def extract_document(filename: str, content: bytes) -> tuple[str, str]:
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File terlalu besar. Batas ukuran 40 MB.")
    suffix = PurePosixPath(filename.lower()).suffix
    try:
        if suffix in {".txt", ".md", ".text"}:
            return PurePosixPath(filename).stem, content.decode("utf-8-sig", errors="replace").strip()
        if suffix in {".html", ".htm"}:
            return _clean_html(content)
        if suffix == ".pdf":
            reader = PdfReader(BytesIO(content))
            if len(reader.pages) > MAX_PDF_PAGES:
                raise HTTPException(status_code=413, detail="PDF teks dibatasi maksimal 500 halaman.")
            pieces = []
            total_characters = 0
            for page in reader.pages:
                page_text = page.extract_text() or ""
                total_characters += len(page_text)
                if total_characters > MAX_EXTRACTED_TEXT_CHARS:
                    raise HTTPException(status_code=413, detail="Hasil ekstraksi PDF melebihi batas 20 juta karakter.")
                pieces.append(page_text)
            return PurePosixPath(filename).stem, "\n\n".join(pieces).strip()
        if suffix == ".docx":
            with zipfile.ZipFile(BytesIO(content)) as archive:
                _validate_archive_limits(archive)
            document = Document(BytesIO(content))
            text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
            return PurePosixPath(filename).stem, text.strip()
        if suffix == ".epub":
            pieces = []
            with zipfile.ZipFile(BytesIO(content)) as book:
                _validate_archive_limits(book)
                container = ET.fromstring(book.read("META-INF/container.xml"))
                rootfile = next(node for node in container.iter() if node.tag.endswith("rootfile") and node.attrib.get("full-path"))
                package_path = rootfile.attrib["full-path"]
                package = ET.fromstring(book.read(package_path))
                manifest = {}
                for item in package.iter():
                    if item.tag.endswith("item"):
                        manifest[item.attrib.get("id", "")] = item.attrib.get("href", "")
                spine_ids = [item.attrib.get("idref", "") for item in package.iter() if item.tag.endswith("itemref")]
                for item_id in spine_ids:
                    href = manifest.get(item_id)
                    if not href:
                        continue
                    chapter_path = posixpath.normpath(posixpath.join(posixpath.dirname(package_path), href))
                    _, chapter_text = _clean_html(book.read(chapter_path))
                    if chapter_text:
                        pieces.append(chapter_text)
            if not pieces:
                raise ValueError("EPUB tidak memiliki dokumen teks pada urutan spine.")
            return PurePosixPath(filename).stem, "\n\n".join(pieces).strip()

    except (zipfile.BadZipFile, KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail="File tidak valid atau rusak.") from exc
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=400, detail=f"Gagal membaca file: {type(exc).__name__}.") from exc
    raise HTTPException(
        status_code=415,
        detail="Format belum didukung. Gunakan EPUB, PDF, TXT, MD, HTML, atau DOCX.",
    )


def _validate_public_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Format URL atau nomor port tidak valid.") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL harus menggunakan http:// atau https://.")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="URL dengan kredensial tidak diizinkan.")
    if port is not None and not 1 <= port <= 65535:
        raise HTTPException(status_code=400, detail="Nomor port URL tidak valid.")
    host = parsed.hostname
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            addresses = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(host, port or (443 if parsed.scheme == "https" else 80))
            ]
        except OSError as exc:
            raise HTTPException(status_code=400, detail="Domain tidak dapat ditemukan.") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise HTTPException(status_code=400, detail="URL menuju alamat jaringan privat tidak diizinkan.")
    return url


async def extract_webpage_report(url: str) -> dict:
    safe_url = _validate_public_url(url)
    parsed = urlparse(safe_url)
    try:
        async with httpx.AsyncClient(
            timeout=25,
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": "AIStoryReader/0.2 (+chapter text extraction)"},
        ) as client:
            async with client.stream("GET", safe_url) as response:
                if response.is_redirect:
                    raise HTTPException(
                        status_code=400,
                        detail="Halaman mengalihkan URL. Buka URL tujuan langsung, lalu coba lagi.",
                    )
                response.raise_for_status()
                content_length = response.headers.get("content-length")
                if content_length:
                    try:
                        if int(content_length) > MAX_URL_BYTES:
                            raise HTTPException(status_code=413, detail="Halaman terlalu besar untuk diimpor (batas 8 MB).")
                    except ValueError:
                        pass
                content_type = response.headers.get("content-type", "").lower()
                if "html" not in content_type and "text/plain" not in content_type:
                    raise HTTPException(status_code=415, detail="URL bukan halaman HTML atau teks biasa.")
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_URL_BYTES:
                        raise HTTPException(status_code=413, detail="Halaman terlalu besar untuk diimpor (batas 8 MB).")
                raw_content = bytes(body)
                if "text/plain" in content_type:
                    encoding = response.encoding or "utf-8"
                    page_text = raw_content.decode(encoding, errors="replace").strip()
                    title, text = parsed.path.rsplit("/", 1)[-1] or parsed.hostname, page_text
                    paragraph_count = len([part for part in text.splitlines() if part.strip()])
                    container = "plain-text"
                else:
                    adapter = resolve_source_adapter(safe_url)
                    extracted = adapter.extract(raw_content, response.encoding)
                    title, text, paragraph_count, container = extracted.title, extracted.text, extracted.paragraph_count, extracted.container
            if not text:
                raise HTTPException(status_code=422, detail="Teks utama tidak ditemukan di halaman tersebut.")

            warnings = [
                "Kelengkapan chapter belum dapat dipastikan hanya dari satu halaman yang berhasil diambil.",
                "Halaman lanjutan belum digabung otomatis; periksa apakah sumber membagi chapter menjadi beberapa URL.",
            ]
            if paragraph_count <= 1:
                warnings.append("Struktur paragraf tidak terdeteksi dengan jelas; periksa hasil ekstraksi.")
            return {
                "title": title or safe_url,
                "text": text,
                "characters": len(text),
                "source_url": safe_url,
                "source_domain": parsed.hostname,
                "source_type": "html" if "html" in content_type else "text",
                "adapter": {"id": adapter.adapter_id if "html" in content_type else "plain-text", "version": adapter.version if "html" in content_type else "1"},
                "segments": [{
                    "index": 1,
                    "url": safe_url,
                    "container": container,
                    "paragraphs": paragraph_count,
                    "characters": len(text),
                }],
                "verification": {
                    "status": "review_required",
                    "page_count": 1,
                    "paragraph_count": paragraph_count,
                    "warnings": warnings,
                },
            }
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Website sumber mengembalikan HTTP {exc.response.status_code}.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tidak dapat mengambil halaman dari URL tersebut.") from exc


async def extract_webpage(url: str) -> tuple[str, str]:
    """Compatibility wrapper retained for existing callers."""
    result = await extract_webpage_report(url)
    return result["title"], result["text"]
