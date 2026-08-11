"""
Agent planning layer: LLM menentukan rasio finansial apa yang relevan
untuk menjawab pertanyaan user, SEBELUM ada kalkulasi apapun dijalankan.
LLM di sini hanya membuat KEPUTUSAN (rasio apa + kenapa), bukan menghitung --
kalkulasi tetap 100% diserahkan ke ratio_calculator.py lewat tool-calling.
"""
import json
import ollama
from pydantic import BaseModel, ValidationError
from typing import List

MODEL_NAME = "llama3.2:3b"  # Pakai model yang sudah kita punya

AVAILABLE_RATIOS = [
    "ROE", "Debt-to-Equity", "P/E Ratio",
    "Current Ratio", "Net Margin", "Revenue Growth YoY",
]


class RatioPlan(BaseModel):
    """Struktur output terstruktur dari LLM planning -- divalidasi Pydantic."""
    relevant_ratios: List[str]
    reasoning: str


PLANNING_SYSTEM_PROMPT = f"""
Kamu adalah equity research planner. Tugasmu HANYA memilih rasio finansial
yang relevan untuk menjawab pertanyaan user, dari daftar ini: {AVAILABLE_RATIOS}.

ATURAN:
- Jangan menghitung rasio apapun di sini -- itu tugas sistem lain.
- Jangan sebut angka spesifik apapun -- kamu belum punya data.
- Jawab HANYA dalam format JSON: {{"relevant_ratios": [...], "reasoning": "..."}}

CONTOH:
User: "Apakah perusahaan ini undervalued?"
Output: {{"relevant_ratios": ["P/E Ratio"], "reasoning": "P/E Ratio adalah indikator utama untuk menilai apakah saham undervalued atau overvalued."}}

User: "Seberapa sehat likuiditas perusahaan ini?"
Output: {{"relevant_ratios": ["Current Ratio"], "reasoning": "Current Ratio mengukur kemampuan perusahaan membayar kewajiban jangka pendek."}}

User: "Apakah perusahaan ini profitable dan tumbuh?"
Output: {{"relevant_ratios": ["ROE", "Net Margin", "Revenue Growth YoY"], "reasoning": "ROE dan Net Margin mengukur profitabilitas, Revenue Growth YoY mengukur pertumbuhan."}}
"""


def plan_relevant_ratios(user_question: str) -> RatioPlan:
    """
    Kirim pertanyaan user ke LLM, minta LLM memilih rasio yang relevan
    dari AVAILABLE_RATIOS. Output divalidasi lewat Pydantic.
    """
    try:
        response = ollama.chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
                {"role": "user", "content": user_question},
            ],
            format="json",
        )
    except Exception as e:
        raise RuntimeError(f"Ollama error: {e}")

    raw_content = response["message"]["content"]
    
    try:
        parsed = json.loads(raw_content)
        plan = RatioPlan(**parsed)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"LLM output invalid: {e}\nRaw: {raw_content}")

    # Validasi: pastikan semua rasio yang dipilih ada di AVAILABLE_RATIOS
    invalid = [r for r in plan.relevant_ratios if r not in AVAILABLE_RATIOS]
    if invalid:
        raise ValueError(f"LLM memilih rasio tidak dikenal: {invalid}")

    return plan


def get_plan_prompt(user_question: str) -> str:
    """Helper untuk melihat prompt yang akan dikirim ke LLM (debugging)."""
    return f"System: {PLANNING_SYSTEM_PROMPT}\n\nUser: {user_question}"