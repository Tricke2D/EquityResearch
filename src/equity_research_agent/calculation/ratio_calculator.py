"""
Kalkulator rasio finansial -- DIPERLUAS Fase 2 dari 2 menjadi 6 rasio inti.
Tetap mengikuti prinsip Fase 1: pure function, tidak ada pemanggilan LLM,
computed_by selalu "TOOL".
"""
from dataclasses import dataclass


@dataclass
class RatioResult:
    """Hasil kalkulasi satu rasio, lengkap dengan formula yang dipakai (untuk audit)."""
    ratio_name: str
    value: float
    formula: str
    computed_by: str = "TOOL"


# ============ RASIO DARI FASE 1 ============

def calculate_roe(net_income: float, total_equity: float) -> RatioResult:
    """
    Return on Equity = Net Income / Total Equity.
    Mengukur seberapa efisien perusahaan menghasilkan laba dari modal pemegang saham.
    """
    if total_equity == 0:
        raise ValueError("total_equity tidak boleh nol -- pembagian tidak valid")
    value = net_income / total_equity
    return RatioResult(
        ratio_name="ROE",
        value=round(value, 4),
        formula="net_income / total_equity",
    )


def calculate_debt_to_equity(total_liabilities: float, total_equity: float) -> RatioResult:
    """
    Debt-to-Equity Ratio = Total Liabilities / Total Equity.
    Mengukur seberapa besar perusahaan bergantung pada utang vs modal sendiri.
    """
    if total_equity == 0:
        raise ValueError("total_equity tidak boleh nol -- pembagian tidak valid")
    value = total_liabilities / total_equity
    return RatioResult(
        ratio_name="Debt-to-Equity",
        value=round(value, 4),
        formula="total_liabilities / total_equity",
    )


# ============ RASIO BARU FASE 2 ============

def calculate_pe_ratio(price_per_share: float, earnings_per_share: float) -> RatioResult:
    """
    Price-to-Earnings Ratio = Price per Share / Earnings per Share.
    Mengukur berapa kali investor membayar untuk tiap Rupiah/Dollar laba perusahaan.
    """
    if earnings_per_share == 0:
        raise ValueError("earnings_per_share tidak boleh nol -- pembagian tidak valid")
    value = price_per_share / earnings_per_share
    return RatioResult(
        ratio_name="P/E Ratio",
        value=round(value, 4),
        formula="price_per_share / earnings_per_share",
    )


def calculate_current_ratio(current_assets: float, current_liabilities: float) -> RatioResult:
    """
    Current Ratio = Current Assets / Current Liabilities.
    Mengukur kemampuan perusahaan membayar kewajiban jangka pendek.
    """
    if current_liabilities == 0:
        raise ValueError("current_liabilities tidak boleh nol -- pembagian tidak valid")
    value = current_assets / current_liabilities
    return RatioResult(
        ratio_name="Current Ratio",
        value=round(value, 4),
        formula="current_assets / current_liabilities",
    )


def calculate_net_margin(net_income: float, total_revenue: float) -> RatioResult:
    """
    Net Profit Margin = Net Income / Total Revenue.
    Mengukur berapa persen pendapatan yang benar-benar jadi laba bersih.
    """
    if total_revenue == 0:
        raise ValueError("total_revenue tidak boleh nol -- pembagian tidak valid")
    value = net_income / total_revenue
    return RatioResult(
        ratio_name="Net Margin",
        value=round(value, 4),
        formula="net_income / total_revenue",
    )


def calculate_revenue_growth_yoy(revenue_current: float, revenue_prior_year: float) -> RatioResult:
    """
    Revenue Growth Year-over-Year = (Revenue Sekarang - Revenue Tahun Lalu) / Revenue Tahun Lalu.
    """
    if revenue_prior_year == 0:
        raise ValueError("revenue_prior_year tidak boleh nol -- pembagian tidak valid")
    value = (revenue_current - revenue_prior_year) / revenue_prior_year
    return RatioResult(
        ratio_name="Revenue Growth YoY",
        value=round(value, 4),
        formula="(revenue_current - revenue_prior_year) / revenue_prior_year",
    )


# ============ DAFTAR SEMUA RASIO ============

ALL_RATIOS = {
    "ROE": calculate_roe,
    "Debt-to-Equity": calculate_debt_to_equity,
    "P/E Ratio": calculate_pe_ratio,
    "Current Ratio": calculate_current_ratio,
    "Net Margin": calculate_net_margin,
    "Revenue Growth YoY": calculate_revenue_growth_yoy,
}


def calculate_all_ratios(net_income: float, total_equity: float, 
                         total_liabilities: float, total_assets: float,
                         total_revenue: float,
                         price_per_share: float = None,
                         earnings_per_share: float = None,
                         current_assets: float = None,
                         current_liabilities: float = None,
                         revenue_prior_year: float = None) -> dict:
    """Hitung semua rasio sekaligus."""
    results = {}
    
    for name, func in ALL_RATIOS.items():
        try:
            if name == "ROE":
                results[name] = func(net_income, total_equity)
            elif name == "Debt-to-Equity":
                results[name] = func(total_liabilities, total_equity)
            elif name == "P/E Ratio":
                if price_per_share is not None and earnings_per_share is not None:
                    results[name] = func(price_per_share, earnings_per_share)
                else:
                    results[name] = {"error": "Data P/E tidak tersedia"}
            elif name == "Current Ratio":
                if current_assets is not None and current_liabilities is not None:
                    results[name] = func(current_assets, current_liabilities)
                else:
                    results[name] = {"error": "Data Current Ratio tidak tersedia"}
            elif name == "Net Margin":
                results[name] = func(net_income, total_revenue)
            elif name == "Revenue Growth YoY":
                if revenue_prior_year is not None:
                    results[name] = func(total_revenue, revenue_prior_year)
                else:
                    results[name] = {"error": "Data revenue tahun lalu tidak tersedia"}
        except Exception as e:
            results[name] = {"error": str(e)}
    
    return results