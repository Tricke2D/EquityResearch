"""
Gate anti-halusinasi: memverifikasi bahwa SETIAP klaim angka dalam draft
memo punya citation yang valid di database. Ini adalah lapisan terakhir
sebelum memo dianggap 'final' -- draft yang gagal verifikasi TIDAK BOLEH
diteruskan ke output, harus di-flag dan (secara default) diblokir.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from equity_research_agent.citation.claim_matcher import match_sentence_to_citations, MatchResult


@dataclass
class VerificationReport:
    """Hasil lengkap verifikasi satu draft memo."""
    is_verified: bool
    total_numbers_checked: int = 0
    orphan_numbers: List[str] = field(default_factory=list)
    orphan_sentences: List[str] = field(default_factory=list)
    verified_at_sentence_level: Dict[str, List[MatchResult]] = field(default_factory=dict)


def verify_memo_draft(memo_sentences: List[str], statement_ids: List[int]) -> VerificationReport:
    """
    Jalankan verifikasi kalimat demi kalimat pada draft memo.
    Mengumpulkan SEMUA angka orphan dari SELURUH memo.
    """
    orphan_numbers: List[str] = []
    orphan_sentences: List[str] = []
    sentence_results: Dict[str, List[MatchResult]] = {}

    total_checked = 0
    
    for sentence in memo_sentences:
        if not sentence.strip():
            continue
            
        matches = match_sentence_to_citations(sentence, statement_ids)
        sentence_results[sentence] = matches
        total_checked += len(matches)

        sentence_has_orphan = any(m.is_orphan for m in matches)
        if sentence_has_orphan:
            orphan_sentences.append(sentence)
            for m in matches:
                if m.is_orphan:
                    orphan_numbers.append(m.number_found)

    return VerificationReport(
        is_verified=len(orphan_numbers) == 0,
        total_numbers_checked=total_checked,
        orphan_numbers=orphan_numbers,
        orphan_sentences=orphan_sentences,
        verified_at_sentence_level=sentence_results,
    )


def block_if_unverified(report: VerificationReport, strict: bool = True) -> None:
    """
    Gate keras: raise exception kalau memo tidak lolos verifikasi.
    Dipanggil di jalur produksi -- memo dengan angka orphan TIDAK BOLEH
    sampai ke output final.
    """
    if not report.is_verified and strict:
        raise ValueError(
            f"🚫 MEMO DIBLOKIR: {len(report.orphan_numbers)} angka tanpa citation ditemukan.\n"
            f"Angka orphan: {report.orphan_numbers}\n"
            f"Kalimat bermasalah: {report.orphan_sentences}"
        )
    elif not report.is_verified:
        print(f"⚠️  WARNING: {len(report.orphan_numbers)} angka tanpa citation ditemukan (mode advisory)")


def get_verification_summary(report: VerificationReport) -> str:
    """Buat ringkasan verifikasi untuk ditampilkan ke user."""
    if report.is_verified:
        return f"✅ Verifikasi lulus! {report.total_numbers_checked} angka diperiksa, semua memiliki citation."
    else:
        return (
            f"❌ Verifikasi GAGAL! {len(report.orphan_numbers)} angka tanpa citation:\n"
            f"  - Angka orphan: {report.orphan_numbers}\n"
            f"  - {len(report.orphan_sentences)} kalimat bermasalah"
        )