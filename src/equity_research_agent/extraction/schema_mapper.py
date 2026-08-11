"""
Mapping tabel mentah dari PDF ke struktur data standar (Balance Sheet, Income Statement).
Dioptimalkan untuk format laporan keuangan bank Indonesia.
"""
from typing import List, Optional, Dict, Any
from .validators import BalanceSheetData, IncomeStatementData
from .pdf_table_extractor import ExtractedTable


def map_to_balance_sheet(table: ExtractedTable) -> Optional[BalanceSheetData]:
    """
    Mencoba memetakan tabel mentah ke struktur Balance Sheet.
    """
    data: Dict[str, Any] = {}
    found_assets = False
    found_liabilities = False
    found_equity = False
    
    for row_idx, row in enumerate(table.rows):
        if not row or len(row) < 2:
            continue
        
        row_text = " ".join([str(cell).upper().strip() if cell else "" for cell in row])
        
        # Cari TOTAL ASET
        if "TOTAL ASET" in row_text:
            value = _extract_number_from_row(row)
            if value is not None and value > 1000:
                data["total_assets"] = value
                data["source_line"] = row_idx
                found_assets = True
                print(f"  ✅ Found TOTAL ASET: {value:,.0f}")
        
        # Cari TOTAL EKUITAS
        elif "TOTAL EKUITAS" in row_text:
            value = _extract_number_from_row(row)
            if value is not None and value > 1000 and value < 1e15:
                data["total_equity"] = value
                found_equity = True
                print(f"  ✅ Found TOTAL EKUITAS: {value:,.0f}")
        
        # Alternatif: TOTAL LIABILITAS DAN EKUITAS
        elif "TOTAL LIABILITAS DAN EKUITAS" in row_text:
            value = _extract_number_from_row(row)
            if value is not None and value > 1000 and value < 1e15:
                if not found_assets:
                    data["total_assets"] = value
                    found_assets = True
                    print(f"  ✅ Found TOTAL LIABILITAS DAN EKUITAS (as Assets): {value:,.0f}")
    
    # Kalau sudah punya Assets dan Equity, hitung Liabilities
    if found_assets and found_equity:
        data["total_liabilities"] = data["total_assets"] - data["total_equity"]
        found_liabilities = True
        print(f"  ✅ Calculated TOTAL LIABILITAS: {data['total_liabilities']:,.0f}")
    
    # Kalau semua ditemukan, return BalanceSheetData
    if found_assets and found_liabilities and found_equity:
        data["source_page"] = table.page_number
        try:
            return BalanceSheetData(**data)
        except Exception as e:
            print(f"  ⚠️ Validasi gagal: {e}")
            return None
    
    return None


def map_to_income_statement(table: ExtractedTable) -> Optional[IncomeStatementData]:
    """
    Mencoba memetakan tabel mentah ke struktur Income Statement.
    """
    data: Dict[str, Any] = {}
    found_revenue = False
    found_income = False
    
    for row_idx, row in enumerate(table.rows):
        if not row or len(row) < 2:
            continue
        
        row_text = " ".join([str(cell).upper().strip() if cell else "" for cell in row])
        all_numbers = _extract_all_numbers_from_row(row)
        
        # 1. Cari PENDAPATAN BUNGA - ambil angka pertama
        # Cari baris yang mengandung "PENDAPATAN BUNGA" 
        # dan juga mengandung "BEBAN BUNGA" (ini adalah baris pendapatan + beban)
        if "PENDAPATAN BUNGA" in row_text and "BEBAN BUNGA" in row_text:
            if all_numbers and len(all_numbers) >= 1:
                value = all_numbers[0]  # Angka pertama = Pendapatan Bunga
                if value > 0:
                    data["total_revenue"] = value
                    data["source_line"] = row_idx
                    found_revenue = True
                    print(f"  ✅ Found PENDAPATAN BUNGA: {value:,.0f}")
                    print(f"     (all numbers: {all_numbers})")
        
        # 2. Cari LABA (RUGI) BERSIH PERIODE BERJALAN - ambil angka terakhir
        if "LABA (RUGI) BERSIH PERIODE BERJALAN" in row_text:
            if all_numbers and len(all_numbers) >= 1:
                # Ambil angka terakhir (LABA BERSIH)
                value = all_numbers[-1]
                if value != 0:
                    data["net_income"] = value
                    data["source_line"] = row_idx
                    found_income = True
                    print(f"  ✅ Found LABA (RUGI) BERSIH PERIODE BERJALAN: {value:,.0f}")
                    print(f"     (all numbers: {all_numbers})")
    
    if found_revenue and found_income:
        data["source_page"] = table.page_number
        try:
            return IncomeStatementData(**data)
        except Exception as e:
            print(f"  ⚠️ Validasi gagal: {e}")
            return None
    
    return None


def _extract_number_from_row(row: List) -> Optional[float]:
    """
    Ekstrak satu angka terbesar dari row.
    """
    all_numbers = _extract_all_numbers_from_row(row)
    if all_numbers:
        positive = [n for n in all_numbers if n > 0]
        if positive:
            return max(positive)
    return None


def _extract_all_numbers_from_row(row: List) -> List[float]:
    """
    Ekstrak SEMUA angka dari row tabel.
    """
    import re
    
    all_numbers = []
    
    for cell in row:
        if cell is None:
            continue
        
        cell_str = str(cell).strip()
        
        # Preprocess cell
        cleaned_cell = _preprocess_cell(cell_str)
        
        # Cari semua pola angka
        number_patterns = re.findall(r'[\d.,]+', cleaned_cell)
        
        for num_str in number_patterns:
            cleaned = _clean_number(num_str)
            if cleaned:
                try:
                    val = float(cleaned)
                    if 1000 < val < 1e15 or -1e15 < val < -1000:
                        all_numbers.append(val)
                except ValueError:
                    continue
    
    return all_numbers


def _preprocess_cell(cell_str: str) -> str:
    """
    Preprocess cell string sebelum ekstraksi angka.
    """
    import re
    
    cell_str = re.sub(r'(\d)\s+\.\s*(\d)', r'\1.\2', cell_str)
    cell_str = re.sub(r'\.\s+(\d)', r'.\1', cell_str)
    cell_str = re.sub(r'(\d)\s+\.', r'\1.', cell_str)
    cell_str = cell_str.replace(' ', '')
    
    return cell_str


def _clean_number(num_str: str) -> Optional[str]:
    """
    Bersihkan format angka Indonesia.
    """
    import re
    
    cleaned = num_str.strip()
    
    is_negative = False
    if cleaned.startswith('(') and cleaned.endswith(')'):
        is_negative = True
        cleaned = cleaned[1:-1]
    
    if '.' in cleaned and ',' not in cleaned:
        cleaned = cleaned.replace('.', '')
    elif ',' in cleaned and '.' not in cleaned:
        cleaned = cleaned.replace(',', '')
    elif ',' in cleaned and '.' in cleaned:
        if cleaned.count('.') > cleaned.count(','):
            cleaned = cleaned.replace('.', '').replace(',', '.')
        else:
            cleaned = cleaned.replace(',', '')
    
    cleaned = re.sub(r'[^\d\-.]', '', cleaned)
    
    if is_negative and cleaned and not cleaned.startswith('-'):
        cleaned = '-' + cleaned
    
    return cleaned if cleaned else None


def find_balance_sheet(tables: List[ExtractedTable]) -> Optional[BalanceSheetData]:
    """Cari balance sheet di antara semua tabel yang diekstrak."""
    print("\n🔍 Mencari Balance Sheet...")
    for i, table in enumerate(tables):
        print(f"\n📊 Table {i+1} (Page {table.page_number}):")
        result = map_to_balance_sheet(table)
        if result:
            print("  ✅ BALANCE SHEET DITEMUKAN!")
            return result
    print("\n❌ Balance Sheet tidak ditemukan di semua tabel")
    return None


def find_income_statement(tables: List[ExtractedTable]) -> Optional[IncomeStatementData]:
    """Cari income statement di antara semua tabel yang diekstrak."""
    print("\n🔍 Mencari Income Statement...")
    for i, table in enumerate(tables):
        print(f"\n📊 Table {i+1} (Page {table.page_number}):")
        result = map_to_income_statement(table)
        if result:
            print("  ✅ INCOME STATEMENT DITEMUKAN!")
            return result
    print("\n❌ Income Statement tidak ditemukan di semua tabel")
    return None