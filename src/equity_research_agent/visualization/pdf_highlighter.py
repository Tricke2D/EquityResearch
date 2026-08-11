"""
Render halaman PDF sumber dengan kotak highlight di lokasi baris data
yang menjadi sumber sebuah citation. Dipakai demo (Streamlit) untuk fitur
'klik angka di memo -> lihat highlight di PDF asli'.
"""
import fitz  # PyMuPDF
from dataclasses import dataclass
from typing import Optional, List, Tuple
import base64
import io
from PIL import Image


@dataclass
class HighlightedPage:
    """Hasil render satu halaman PDF dengan highlight."""
    page_number: int
    image_bytes: bytes
    highlight_found: bool
    highlight_count: int = 0


@dataclass
class CitationHighlight:
    """Informasi highlight untuk satu citation."""
    citation_id: int
    page_number: int
    search_text: str
    statement_id: int


def highlight_source_in_pdf(pdf_path: str, page_number: int, search_text: str) -> HighlightedPage:
    """
    Buka PDF, cari teks di halaman tertentu, gambar kotak kuning transparan
    di sekitarnya, lalu render halaman jadi gambar PNG.
    """
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]  # PyMuPDF pakai index 0-based

    text_instances = page.search_for(search_text)
    highlight_found = len(text_instances) > 0
    highlight_count = len(text_instances)

    for rect in text_instances:
        # Buat highlight dengan warna kuning transparan
        highlight = page.add_highlight_annot(rect)
        highlight.set_colors(stroke=(1, 0.85, 0))  # kuning
        highlight.set_opacity(0.5)
        highlight.update()

    # Render halaman sebagai gambar
    pixmap = page.get_pixmap(dpi=150)
    image_bytes = pixmap.tobytes("png")

    doc.close()
    
    return HighlightedPage(
        page_number=page_number,
        image_bytes=image_bytes,
        highlight_found=highlight_found,
        highlight_count=highlight_count,
    )


def highlight_multiple_pages(pdf_path: str, highlights: List[CitationHighlight]) -> dict:
    """
    Highlight multiple citations dalam satu PDF.
    Return dict dengan page_number sebagai key.
    """
    results = {}
    doc = fitz.open(pdf_path)
    
    try:
        for highlight in highlights:
            page = doc[highlight.page_number - 1]
            text_instances = page.search_for(highlight.search_text)
            
            if text_instances:
                for rect in text_instances:
                    highlight_annot = page.add_highlight_annot(rect)
                    highlight_annot.set_colors(stroke=(1, 0.85, 0))
                    highlight_annot.set_opacity(0.5)
                    highlight_annot.update()
        
        # Render semua halaman yang di-highlight
        unique_pages = set(h.page_number for h in highlights)
        for page_num in unique_pages:
            page = doc[page_num - 1]
            pixmap = page.get_pixmap(dpi=150)
            results[page_num] = {
                "image_bytes": pixmap.tobytes("png"),
                "page_number": page_num,
            }
    finally:
        doc.close()
    
    return results


def get_page_image(pdf_path: str, page_number: int, dpi: int = 150) -> bytes:
    """Render satu halaman PDF tanpa highlight."""
    doc = fitz.open(pdf_path)
    page = doc[page_number - 1]
    pixmap = page.get_pixmap(dpi=dpi)
    image_bytes = pixmap.tobytes("png")
    doc.close()
    return image_bytes


def image_bytes_to_base64(image_bytes: bytes) -> str:
    """Konversi gambar bytes ke base64 untuk Streamlit."""
    return base64.b64encode(image_bytes).decode('utf-8')


def search_text_in_pdf(pdf_path: str, search_text: str) -> List[Tuple[int, List]]:
    """
    Cari teks di seluruh PDF dan return daftar halaman + posisi.
    """
    results = []
    doc = fitz.open(pdf_path)
    
    try:
        for page_num, page in enumerate(doc, start=1):
            text_instances = page.search_for(search_text)
            if text_instances:
                results.append((page_num, text_instances))
    finally:
        doc.close()
    
    return results