"""
Mencatat jejak audit: setiap kalkulasi rasio yang dipakai dalam reasoning
agent HARUS tercatat ke tabel citations, menghubungkan claim ke
source_statement_id + source_page + source_line asalnya.
"""
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.orm import Session
from src.equity_research_agent.db.session import SessionLocal
from src.equity_research_agent.db.models import Citation


@dataclass
class SourceReference:
    """Referensi ke baris data sumber spesifik di financial_statements."""
    statement_id: int
    page: int
    line: int


def record_citation(
    claim_text: str,
    ratio_result_value: float,
    sources: List[SourceReference],
) -> List[int]:
    """
    Simpan record citation untuk satu hasil kalkulasi rasio.
    Satu rasio bisa punya lebih dari satu source (misal ROE butuh net_income
    DAN total_equity, dari baris berbeda) -- karena itu sources adalah list.
    Return list ID citation yang berhasil disimpan.
    """
    saved_ids = []
    db = SessionLocal()
    try:
        for source in sources:
            citation = Citation(
                claim_text=claim_text,
                source_statement_id=source.statement_id,
                source_page=source.page,
                source_line=source.line,
            )
            db.add(citation)
            db.flush()
            saved_ids.append(citation.id)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
    
    return saved_ids


def build_claim_text(ratio_name: str, value: float) -> str:
    """
    Bangun teks klaim standar dari hasil rasio, dipakai konsisten
    di seluruh sistem supaya claim_matcher.py bisa mencocokkan.
    """
    return f"{ratio_name} tercatat sebesar {value}"


def get_citations_by_statement(statement_id: int) -> List[Citation]:
    """Ambil semua citation untuk satu financial_statement."""
    db = SessionLocal()
    try:
        citations = db.query(Citation).filter(
            Citation.source_statement_id == statement_id
        ).all()
        return citations
    finally:
        db.close()