"""
Tool untuk menghitung rasio keuangan dengan citation tracking otomatis.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from equity_research_agent.calculation.ratio_calculator import (
    calculate_roe, calculate_debt_to_equity, calculate_pe_ratio,
    calculate_current_ratio, calculate_net_margin, calculate_revenue_growth_yoy,
)
from equity_research_agent.citation.citation_tracker import (
    record_citation, build_claim_text, SourceReference
)

# Registry semua fungsi rasio
RATIO_FUNCTIONS = {
    "ROE": calculate_roe,
    "Debt-to-Equity": calculate_debt_to_equity,
    "P/E Ratio": calculate_pe_ratio,
    "Current Ratio": calculate_current_ratio,
    "Net Margin": calculate_net_margin,
    "Revenue Growth YoY": calculate_revenue_growth_yoy,
}

# Skema tool untuk Ollama
CALCULATE_RATIO_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate_ratio",
        "description": (
            "Hitung rasio finansial dari data laporan keuangan. "
            "WAJIB dipanggil untuk setiap kalkulasi angka."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "ratio_name": {
                    "type": "string",
                    "enum": list(RATIO_FUNCTIONS.keys()),
                    "description": "Nama rasio yang ingin dihitung",
                },
                "net_income": {"type": "number", "description": "Laba bersih"},
                "total_equity": {"type": "number", "description": "Total ekuitas"},
                "total_liabilities": {"type": "number", "description": "Total liabilitas"},
                "price_per_share": {"type": "number", "description": "Harga per saham"},
                "earnings_per_share": {"type": "number", "description": "Laba per saham"},
                "current_assets": {"type": "number", "description": "Aset lancar"},
                "current_liabilities": {"type": "number", "description": "Liabilitas lancar"},
                "total_revenue": {"type": "number", "description": "Total pendapatan"},
                "revenue_prior_year": {"type": "number", "description": "Pendapatan tahun lalu"},
            },
            "required": ["ratio_name"],
        },
    },
}


def execute_calculate_ratio_tool(arguments: dict, sources: list = None) -> dict:
    """
    Eksekusi kalkulasi rasio DAN catat citation dalam satu langkah atomik.
    """
    ratio_name = arguments.get("ratio_name")
    calc_fn = RATIO_FUNCTIONS.get(ratio_name)
    
    if calc_fn is None:
        return {"error": f"Rasio tidak dikenal: {ratio_name}"}

    # Siapkan argumen untuk fungsi kalkulator
    calc_args = {k: v for k, v in arguments.items() if k != "ratio_name"}
    
    # Konversi nilai ke float (handle string)
    for key, value in calc_args.items():
        if isinstance(value, str):
            try:
                calc_args[key] = float(value.replace(',', '').replace(' ', ''))
            except ValueError:
                return {"error": f"Invalid number for {key}: {value}"}
    
    try:
        result = calc_fn(**calc_args)
    except Exception as e:
        return {"error": str(e)}

    # Catat citation jika ada sources
    citation_ids = []
    if sources:
        claim_text = build_claim_text(result.ratio_name, result.value)
        try:
            source_refs = [
                SourceReference(
                    statement_id=s.get("statement_id"),
                    page=s.get("page"),
                    line=s.get("line")
                ) for s in sources
            ]
            citation_ids = record_citation(claim_text, result.value, source_refs)
        except Exception as e:
            return {"error": f"Citation tracking gagal: {e}"}

    return {
        "ratio_name": result.ratio_name,
        "value": result.value,
        "formula": result.formula,
        "computed_by": result.computed_by,
        "citation_ids": citation_ids,
    }