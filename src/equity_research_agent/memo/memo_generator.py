"""
Orkestrasi penuh: dari pertanyaan user sampai investment memo final.
Menyatukan ratio_planner, tool-calling calculator, citation_tracker,
period_comparator, dan verification_pass dalam satu alur berurutan.
"""
import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from equity_research_agent.llm.planning.ratio_planner import plan_relevant_ratios
from equity_research_agent.verification.verification_pass import (
    verify_memo_draft, block_if_unverified, VerificationReport, get_verification_summary
)
from equity_research_agent.memo.footnote_formatter import attach_footnotes

# Gunakan model yang sudah kita punya
MODEL_NAME = "llama3.2:3b"


@dataclass
class MemoResult:
    """Hasil lengkap dari generation memo."""
    memo_text: str
    verification_report: VerificationReport
    is_verified: bool


def generate_investment_memo(
    company_id: int,
    user_question: str,
    calculated_ratios: List[Dict[str, Any]],
    statement_ids: List[int],
    enforce_verification: bool = True,
    model_name: str = MODEL_NAME,
) -> MemoResult:
    """
    Hasilkan draft memo dari hasil rasio yang SUDAH dihitung tool,
    lalu jalankan verification pass.
    """
    import ollama
    
    # Siapkan system prompt
    system_prompt = """
Kamu adalah equity research analyst profesional. Susun investment memo singkat (3-5 paragraf)
berdasarkan HASIL KALKULASI RASIO yang diberikan.

ATURAN PENTING:
1. JANGAN menghitung ulang atau mengarang angka baru — gunakan angka persis dari data.
2. Setiap angka yang kamu sebut HARUS berasal dari data yang diberikan.
3. Jangan menambahkan analisis yang membutuhkan data tambahan di luar yang diberikan.
4. Gunakan bahasa profesional dan objektif.

Format output: narasi yang mengalir, bukan bullet points.
"""
    
    # Siapkan data rasio untuk prompt
    ratios_summary = []
    for r in calculated_ratios:
        ratio_name = r.get('ratio_name', 'Unknown')
        value = r.get('value', 0)
        formula = r.get('formula', 'N/A')
        ratios_summary.append(f"- {ratio_name}: {value:.4f} (formula: {formula})")
    
    ratios_text = "\n".join(ratios_summary)
    
    user_prompt = f"""
Pertanyaan: {user_question}

Data rasio yang tersedia:
{ratios_text}

Berdasarkan data di atas, buat investment memo yang menjawab pertanyaan tersebut.
"""

    try:
        response = ollama.chat(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        draft_memo = response["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")

    # Split menjadi kalimat untuk verifikasi
    sentences = [s.strip() for s in draft_memo.split(". ") if s.strip()]
    
    # Jalankan verifikasi
    report = verify_memo_draft(sentences, statement_ids)
    
    # Block jika diperlukan
    if enforce_verification:
        block_if_unverified(report, strict=True)
    
    # Tambahkan footnote
    final_memo = attach_footnotes(draft_memo, report)
    
    return MemoResult(
        memo_text=final_memo,
        verification_report=report,
        is_verified=report.is_verified,
    )


def generate_memo_from_plan(
    company_id: int,
    user_question: str,
    plan,
    calculated_ratios: List[Dict[str, Any]],
    statement_ids: List[int],
    enforce_verification: bool = True,
) -> MemoResult:
    """
    Generate memo dari plan yang sudah dibuat.
    """
    # Tambahkan informasi plan ke prompt
    plan_info = f"Rasio yang dianalisis: {plan.relevant_ratios}\nAlasan: {plan.reasoning}"
    
    return generate_investment_memo(
        company_id=company_id,
        user_question=f"{user_question}\n\n{plan_info}",
        calculated_ratios=calculated_ratios,
        statement_ids=statement_ids,
        enforce_verification=enforce_verification,
    )