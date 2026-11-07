from __future__ import annotations

import ipaddress
import socket
import zipfile
from io import BytesIO
from pathlib import PurePosixPath
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader


MAX_UPLOAD_BYTES = 40 * 1024 * 1024
MAX_URL_BYTES = 8 * 1024 * 1024


def _clean_html(raw: bytes, encoding: str | None = None) -> tuple[str, str]:
    soup = BeautifulSoup(raw, "html.parser", from_encoding=encoding)
    for node in soup(["script", "style", "noscript", "svg", "nav", "footer", "header", "form"]):
        node.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    main = soup.find("article") or soup.find("main") or soup.body or soup
    lines = [line.strip() for line in main.get_text("\n").splitlines()]
    text = "\n".join(line for line in lines if line)
    return title, text


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
            text = "\n\n".join((page.extract_text() or "") for page in reader.pages)
            return PurePosixPath(filename).stem, text.strip()
        if suffix == ".docx":
            document = Document(BytesIO(content))
            text = "\n".join(p.text for p in document.paragraphs if p.text.strip())
            return PurePosixPath(filename).stem, text.strip()
        if suffix == ".epub":
            pieces = []
            with zipfile.ZipFile(BytesIO(content)) as book:
                names = sorted(
                    name for name in book.namelist()
                    if name.lower().endswith((".xhtml", ".html", ".htm"))
                )
                for name in names:
                    _, chapter_text = _clean_html(book.read(name))
                    if chapter_text:
                        pieces.append(chapter_text)
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
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise HTTPException(status_code=400, detail="URL harus menggunakan http:// atau https://.")
    if parsed.username or parsed.password:
        raise HTTPException(status_code=400, detail="URL dengan kredensial tidak diizinkan.")
    host = parsed.hostname
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            addresses = [
                ipaddress.ip_address(item[4][0])
                for item in socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80))
            ]
        except OSError as exc:
            raise HTTPException(status_code=400, detail="Domain tidak dapat ditemukan.") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise HTTPException(status_code=400, detail="URL menuju alamat jaringan privat tidak diizinkan.")
    return url


async def extract_webpage(url: str) -> tuple[str, str]:
    safe_url = _validate_public_url(url)
    try:
        async with httpx.AsyncClient(
            timeout=25,
            follow_redirects=False,
            headers={"User-Agent": "AIStoryReader/0.1 (+chapter text extraction)"},
        ) as client:
            response = await client.get(safe_url)
            if response.is_redirect:
                raise HTTPException(
                    status_code=400,
                    detail="Halaman mengalihkan URL. Buka URL tujuan langsung, lalu coba lagi.",
                )
            response.raise_for_status()
            if len(response.content) > MAX_URL_BYTES:
                raise HTTPException(status_code=413, detail="Halaman terlalu besar untuk diimpor (batas 8 MB).")
            content_type = response.headers.get("content-type", "").lower()
            if "html" not in content_type and "text/plain" not in content_type:
                raise HTTPException(status_code=415, detail="URL bukan halaman HTML atau teks biasa.")
            title, text = _clean_html(response.content, response.encoding)
            if not text:
                raise HTTPException(status_code=422, detail="Teks utama tidak ditemukan di halaman tersebut.")
            return title or safe_url, text
    except HTTPException:
        raise
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"Website sumber mengembalikan HTTP {exc.response.status_code}.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Tidak dapat mengambil halaman dari URL tersebut.") from exc
