"""
Ekstraksi tabel dari PDF laporan keuangan menggunakan pdfplumber sebagai
metode utama, dengan camelot sebagai fallback untuk tabel bergaris/kompleks.
PRINSIP UTAMA: LLM tidak pernah membaca angka langsung dari PDF di sini.
Semua ekstraksi bersifat deterministik dan bisa di-unit-test.
"""
from dataclasses import dataclass
from typing import List, Optional, Set
import pdfplumber
import camelot


@dataclass
class ExtractedTable:
    """Satu tabel hasil ekstraksi, lengkap dengan lokasi sumbernya di PDF."""
    rows: List[List[str]]
    page_number: int
    table_index_on_page: int
    extraction_method: str  # "pdfplumber" | "camelot"


def extract_tables_from_pdf(pdf_path: str) -> List[ExtractedTable]:
    """
    Ekstrak semua tabel dari file PDF, halaman demi halaman.
    Mengembalikan list ExtractedTable yang masih 'mentah' (belum dipetakan
    ke skema balance_sheet/income_statement -- itu tugas schema_mapper.py).
    """
    extracted: List[ExtractedTable] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table_idx, raw_table in enumerate(tables):
                if _is_valid_table(raw_table):
                    extracted.append(ExtractedTable(
                        rows=raw_table,
                        page_number=page_idx,
                        table_index_on_page=table_idx,
                        extraction_method="pdfplumber",
                    ))

    # Fallback: halaman yang pdfplumber gagal ekstrak tabelnya dicoba lagi
    # dengan camelot (lebih kuat untuk tabel bergaris tegas / lattice).
    pages_missed = _find_pages_without_tables(pdf_path, extracted)
    if pages_missed:
        extracted.extend(_extract_with_camelot(pdf_path, pages_missed))

    return extracted


def _is_valid_table(raw_table: List) -> bool:
    """Filter noise: tabel harus punya minimal 2 baris dan 2 kolom untuk dianggap valid."""
    if not raw_table:
        return False
    return len(raw_table) >= 2 and all(len(row) >= 2 for row in raw_table if row)


def _find_pages_without_tables(pdf_path: str, found: List[ExtractedTable]) -> List[int]:
    """Cari halaman yang belum menghasilkan tabel valid dari pdfplumber."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_pages = set(range(1, len(pdf.pages) + 1))
    except Exception:
        return []
    
    found_pages = {t.page_number for t in found}
    return sorted(all_pages - found_pages)


def _extract_with_camelot(pdf_path: str, page_numbers: List[int]) -> List[ExtractedTable]:
    """Ekstraksi fallback pakai camelot untuk halaman yang gagal di pdfplumber."""
    if not page_numbers:
        return []
    
    pages_str = ",".join(str(p) for p in page_numbers)
    result = []
    
    try:
        tables = camelot.read_pdf(pdf_path, pages=pages_str, flavor="lattice")
        for t in tables:
            result.append(ExtractedTable(
                rows=t.df.values.tolist(),
                page_number=int(t.page),
                table_index_on_page=0,
                extraction_method="camelot",
            ))
    except Exception as e:
        # camelot mungkin gagal untuk PDF tertentu
        print(f"Warning: camelot extraction failed for pages {page_numbers}: {e}")
    
    return result


def preview_tables(pdf_path: str, max_tables: int = 3):
    """Fungsi helper untuk preview tabel yang diekstrak dari PDF."""
    tables = extract_tables_from_pdf(pdf_path)
    
    print(f"Found {len(tables)} tables in {pdf_path}")
    print("-" * 50)
    
    for i, table in enumerate(tables[:max_tables]):
        print(f"\nTable {i+1}: Page {table.page_number} (method: {table.extraction_method})")
        print(f"Rows: {len(table.rows)}, Columns: {len(table.rows[0]) if table.rows else 0}")
        
        # Preview first 5 rows
        for row_idx, row in enumerate(table.rows[:5]):
            print(f"  Row {row_idx+1}: {row}")
        
        if len(table.rows) > 5:
            print(f"  ... and {len(table.rows) - 5} more rows")
        print("-" * 30)