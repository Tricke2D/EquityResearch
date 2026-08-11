"""
Definisi ORM models untuk seluruh skema database.
Skema ini adalah fondasi citation tracking: setiap angka finansial
WAJIB bisa ditelusuri balik ke source_page_ref / source_line.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Text, DateTime, Numeric
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class Company(Base):
    """Merepresentasikan satu perusahaan yang laporannya dianalisis."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    ticker = Column(String(20), nullable=False, unique=True)

    statements = relationship("FinancialStatement", back_populates="company")


class FinancialStatement(Base):
    """
    Satu laporan keuangan (balance sheet / income statement) untuk satu periode.
    raw_extracted_data menyimpan hasil ekstraksi pdfplumber APA ADANYA (JSONB),
    sebelum dihitung rasio apapun -- ini adalah 'source of truth' untuk citation.
    """
    __tablename__ = "financial_statements"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    period = Column(String(20), nullable=False)          # contoh: "2024-Q1"
    statement_type = Column(String(50), nullable=False)  # "balance_sheet" | "income_statement"
    raw_extracted_data = Column(JSON, nullable=False)     # hasil parsing pdfplumber
    source_page_ref = Column(Integer, nullable=False)     # halaman PDF asal tabel ini
    embedding = Column(Vector(384), nullable=True)         # utk pgvector similarity (Fase 2)
    created_at = Column(DateTime, server_default=func.now())

    company = relationship("Company", back_populates="statements")
    ratios = relationship("CalculatedRatio", back_populates="statement")


class CalculatedRatio(Base):
    """
    Hasil kalkulasi rasio finansial. computed_by WAJIB 'TOOL' bukan 'LLM' --
    kolom ini jadi bukti audit bahwa angka dihitung Python, bukan dikarang LLM.
    """
    __tablename__ = "calculated_ratios"

    id = Column(Integer, primary_key=True)
    statement_id = Column(Integer, ForeignKey("financial_statements.id"), nullable=False)
    ratio_name = Column(String(50), nullable=False)        # "ROE", "DER", dst
    value = Column(Numeric(12, 4), nullable=False)
    calculation_formula = Column(Text, nullable=False)     # dokumentasi rumus yang dipakai
    computed_by = Column(String(10), nullable=False)       # "TOOL" | "LLM" (harus selalu TOOL)

    statement = relationship("FinancialStatement", back_populates="ratios")


class Citation(Base):
    """
    Menghubungkan setiap klaim angka di memo investasi ke sumber persisnya.
    Ini adalah mekanisme anti-halusinasi utama proyek (dipakai penuh di Fase 2).
    """
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True)
    memo_section_id = Column(Integer, nullable=True)  # FK ke investment_memos, diaktifkan Fase 2
    claim_text = Column(Text, nullable=False)
    source_statement_id = Column(Integer, ForeignKey("financial_statements.id"), nullable=False)
    source_page = Column(Integer, nullable=False)
    source_line = Column(Integer, nullable=True)


class InvestmentMemo(Base):
    """Memo investasi final yang dihasilkan LLM (dipakai penuh di Fase 3)."""
    __tablename__ = "investment_memos"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    thesis = Column(Text, nullable=True)
    generated_at = Column(DateTime, server_default=func.now())