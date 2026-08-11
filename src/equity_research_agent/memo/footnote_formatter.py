"""
Mengubah draft memo + hasil verifikasi jadi teks dengan footnote citation
yang readable, mengikuti format akademik standar.
"""
import re
from typing import List, Dict
from equity_research_agent.verification.verification_pass import VerificationReport


def attach_footnotes(draft_memo: str, report: VerificationReport) -> str:
    """
    Sisipkan penanda footnote [n] setelah tiap angka yang berhasil di-citation,
    lalu lampirkan daftar referensi di akhir memo.
    """
    if report.is_verified:
        return _attach_verified_footnotes(draft_memo, report)
    else:
        return _attach_unverified_footnotes(draft_memo, report)


def _attach_verified_footnotes(draft_memo: str, report: VerificationReport) -> str:
    """Tambahkan footnote untuk memo yang lolos verifikasi."""
    footnote_index = 1
    references: List[str] = []
    annotated_memo = draft_memo
    
    # Kumpulkan semua angka yang ter-citation dari laporan
    citation_map = {}
    for sentence, matches in report.verified_at_sentence_level.items():
        for match in matches:
            if not match.is_orphan and match.matched_citation_id:
                citation_map[match.number_found] = match.matched_citation_id
    
    # Ganti angka dengan angka + footnote
    for number, citation_id in citation_map.items():
        if number in annotated_memo:
            marker = f" [{footnote_index}]"
            annotated_memo = annotated_memo.replace(number, number + marker, 1)
            references.append(
                f"[{footnote_index}] Citation ID {citation_id}"
            )
            footnote_index += 1
    
    if references:
        annotated_memo += "\n\n--- Referensi ---\n" + "\n".join(references)
    
    return annotated_memo


def _attach_unverified_footnotes(draft_memo: str, report: VerificationReport) -> str:
    """Tambahkan footnote dengan tanda khusus untuk angka orphan."""
    annotated_memo = draft_memo
    
    # Tandai angka orphan dengan [TANPA SUMBER]
    for orphan in report.orphan_numbers:
        if orphan in annotated_memo:
            annotated_memo = annotated_memo.replace(orphan, f"{orphan} [TANPA SUMBER]", 1)
    
    # Tambahkan peringatan di akhir
    if report.orphan_numbers:
        annotated_memo += (
            f"\n\n⚠️ PERINGATAN: {len(report.orphan_numbers)} angka tidak memiliki sumber "
            f"yang valid: {', '.join(report.orphan_numbers)}"
        )
    
    return annotated_memo


def extract_citation_ids_from_memo(memo: str) -> List[int]:
    """Ekstrak semua citation ID dari memo yang sudah diformat."""
    pattern = r'Citation ID (\d+)'
    matches = re.findall(pattern, memo)
    return [int(m) for m in matches]