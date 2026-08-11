"""
Validasi Pydantic untuk data hasil ekstraksi sebelum disimpan ke database.
Ini adalah 'gate' kualitas: data yang tidak lolos validasi TIDAK BOLEH
masuk ke tabel financial_statements, karena akan meracuni semua kalkulasi
rasio di hilir.
"""
from pydantic import BaseModel, field_validator
from typing import Optional


class BalanceSheetData(BaseModel):
    """Struktur standar balance sheet setelah dipetakan dari tabel mentah."""
    total_assets: float
    total_liabilities: float
    total_equity: float
    source_page: int
    source_line: Optional[int] = None

    @field_validator("total_assets", "total_liabilities", "total_equity")
    @classmethod
    def must_be_reasonable(cls, v: float) -> float:
        """Tolak angka yang jelas hasil salah parse (misal 0 atau negatif ekstrem)."""
        if v == 0:
            raise ValueError("Nilai tidak boleh nol -- kemungkinan gagal parse")
        if v < -1e12 or v > 1e15:
            raise ValueError(f"Nilai {v} tidak masuk akal untuk laporan keuangan")
        return v

    def check_accounting_identity(self, tolerance: float = 0.01) -> bool:
        """
        Verifikasi identitas akuntansi dasar: Assets = Liabilities + Equity.
        Jika tidak seimbang (di luar toleransi), ini sinyal kuat ekstraksi salah.
        """
        diff = abs(self.total_assets - (self.total_liabilities + self.total_equity))
        if self.total_assets == 0:
            return False
        return diff <= (self.total_assets * tolerance)


class IncomeStatementData(BaseModel):
    """Struktur standar income statement setelah dipetakan dari tabel mentah."""
    net_income: float
    total_revenue: float
    source_page: int
    source_line: Optional[int] = None

    @field_validator("net_income", "total_revenue")
    @classmethod
    def must_be_reasonable(cls, v: float) -> float:
        """Tolak angka yang jelas hasil salah parse."""
        if v == 0:
            raise ValueError("Nilai tidak boleh nol -- kemungkinan gagal parse")
        if v < -1e12 or v > 1e15:
            raise ValueError(f"Nilai {v} tidak masuk akal untuk laporan keuangan")
        return v