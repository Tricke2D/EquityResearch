"""
Mencocokkan angka yang muncul dalam kalimat naratif LLM dengan citation
record yang sudah tercatat dari tool call.

Pendekatan: ekstrak angka numerik dari kalimat, cocokkan ke citation.claim_text
via fuzzy match (karena LLM bisa menulis format berbeda).
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Set
from rapidfuzz import fuzz
from src.equity_research_agent.db.session import SessionLocal
from src.equity_research_agent.db.models import Citation

MATCH_THRESHOLD = 80  # skor kemiripan minimum (0-100) untuk dianggap cocok


@dataclass
class MatchResult:
    """Hasil pencocokan satu angka dalam kalimat ke citation (jika ada)."""
    number_found: str
    normalized_value: float
    matched_citation_id: Optional[int]
    is_orphan: bool  # True jika angka ini TIDAK ADA citation-nya


def extract_numbers(sentence: str) -> List[str]:
    """
    Ekstrak semua token angka dari kalimat.
    - Handle koma ribuan: 38,409,131 -> 38409131
    - Handle persen: 9.74% -> 0.0974
    - Handle desimal: 0.193
    - Handle angka dengan titik ribuan: 1.592.981.197 -> 1592981197
    """
    numbers = []
    
    # Pattern 1: Angka dengan koma ribuan (38,409,131) - tangkap sebagai satu kesatuan
    # Pattern 2: Angka dengan persen (9.74%)
    # Pattern 3: Angka desimal biasa (0.193)
    # Pattern 4: Angka dengan titik ribuan (1.592.981.197)
    
    # Cari angka dengan koma ribuan dulu (prioritas)
    comma_pattern = r'\d{1,3}(?:,\d{3})+\.?\d*%?'
    found_comma = re.findall(comma_pattern, sentence)
    for num in found_comma:
        normalized = _normalize_number(num)
        if normalized is not None:
            numbers.append(str(normalized))
        # Hapus dari sentence agar tidak diproses ulang
        sentence = sentence.replace(num, '')
    
    # Cari angka dengan persen
    percent_pattern = r'\d+\.?\d*%'
    found_percent = re.findall(percent_pattern, sentence)
    for num in found_percent:
        normalized = _normalize_number(num)
        if normalized is not None:
            numbers.append(str(normalized))
        sentence = sentence.replace(num, '')
    
    # Cari angka dengan titik ribuan (1.592.981.197)
    dot_pattern = r'\d{1,3}(?:\.\d{3})+\.?\d*'
    found_dot = re.findall(dot_pattern, sentence)
    for num in found_dot:
        normalized = _normalize_number(num)
        if normalized is not None:
            numbers.append(str(normalized))
        sentence = sentence.replace(num, '')
    
    # Cari sisa angka desimal biasa
    decimal_pattern = r'\d+\.?\d*'
    found_decimal = re.findall(decimal_pattern, sentence)
    for num in found_decimal:
        if num and num != '0':
            normalized = _normalize_number(num)
            if normalized is not None:
                numbers.append(str(normalized))
    
    # Hapus duplikat tapi pertahankan urutan
    seen: Set[str] = set()
    unique_numbers = []
    for num in numbers:
        if num not in seen:
            seen.add(num)
            unique_numbers.append(num)
    
    return unique_numbers


def _normalize_number(num_str: str) -> Optional[float]:
    """
    Normalisasi format angka ke float.
    19.3% -> 0.193
    38,409,131 -> 38409131
    1.592.981.197 -> 1592981197
    0.193 -> 0.193
    """
    if not num_str:
        return None
    
    cleaned = num_str.strip()
    
    # Handle persen: 19.3% -> 0.193
    is_percent = False
    if cleaned.endswith('%'):
        is_percent = True
        cleaned = cleaned[:-1]
    
    # Handle koma ribuan: 38,409,131 -> 38409131
    # Hapus semua koma
    cleaned = cleaned.replace(',', '')
    
    # Handle titik ribuan: 1.592.981.197 -> 1592981197
    # Tapi hati-hati dengan desimal (1.5 -> 1.5)
    # Jika ada lebih dari 1 titik, anggap sebagai pemisah ribuan
    if cleaned.count('.') > 1:
        cleaned = cleaned.replace('.', '')
    
    try:
        value = float(cleaned)
    except ValueError:
        return None
    
    # Konversi persen ke desimal
    if is_percent:
        value = value / 100
    
    return value


def match_sentence_to_citations(sentence: str, statement_ids: List[int]) -> List[MatchResult]:
    """
    Untuk satu kalimat memo, cari setiap angka di dalamnya dan cek apakah
    ada citation yang cocok (dari statement_ids yang relevan).
    Angka yang tidak match ditandai is_orphan=True.
    """
    numbers = extract_numbers(sentence)
    results = []

    if not numbers:
        return results

    db = SessionLocal()
    try:
        candidate_citations = (
            db.query(Citation)
            .filter(Citation.source_statement_id.in_(statement_ids))
            .all()
        )
    finally:
        db.close()

    # Ekstrak nilai numerik dari citation untuk matching yang lebih akurat
    citation_values = []
    for citation in candidate_citations:
        # Ekstrak angka dari claim_text
        claim_numbers = extract_numbers(citation.claim_text)
        for claim_num in claim_numbers:
            try:
                val = float(claim_num)
                citation_values.append({
                    'citation_id': citation.id,
                    'claim_text': citation.claim_text,
                    'value': val,
                })
            except ValueError:
                continue

    for number in numbers:
        best_match_id = None
        best_score = 0
        best_normalized = None
        
        try:
            num_val = float(number)
        except ValueError:
            continue
        
        # Cari citation dengan nilai terdekat
        for cv in citation_values:
            # Hitung similarity berdasarkan nilai numerik
            # Semakin dekat nilainya, semakin tinggi skor
            diff = abs(num_val - cv['value'])
            if num_val == 0:
                similarity = 100 if diff == 0 else 0
            else:
                similarity = max(0, 100 - (diff / num_val * 100))
            
            # Tambahkan fuzzy match pada teks
            text_score = fuzz.partial_ratio(number, cv['claim_text'])
            
            # Kombinasi skor: 60% numerik + 40% teks
            combined_score = (similarity * 0.6) + (text_score * 0.4)
            
            if combined_score > best_score:
                best_score = combined_score
                best_match_id = cv['citation_id']
                best_normalized = cv['value']

        is_orphan = best_score < MATCH_THRESHOLD
        results.append(MatchResult(
            number_found=number,
            normalized_value=num_val,
            matched_citation_id=None if is_orphan else best_match_id,
            is_orphan=is_orphan,
        ))

    return results


def validate_memo_sentences(sentences: List[str], statement_ids: List[int]) -> dict:
    """
    Validasi seluruh kalimat dalam memo.
    Return dict dengan hasil per kalimat.
    """
    results = {}
    all_orphans = []
    
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
        matches = match_sentence_to_citations(sentence, statement_ids)
        results[f"sentence_{i}"] = {
            "text": sentence,
            "matches": matches,
            "has_orphan": any(m.is_orphan for m in matches),
        }
        for m in matches:
            if m.is_orphan:
                all_orphans.append({
                    "sentence": sentence,
                    "number": m.number_found,
                    "normalized": m.normalized_value,
                })
    
    return {
        "results": results,
        "total_orphans": len(all_orphans),
        "orphan_list": all_orphans,
    }


def get_all_citations(statement_ids: List[int]) -> List[Citation]:
    """Ambil semua citation untuk statement_ids."""
    db = SessionLocal()
    try:
        citations = db.query(Citation).filter(
            Citation.source_statement_id.in_(statement_ids)
        ).all()
        return citations
    finally:
        db.close()