"""
Equity Research Agent - Aplikasi Utama
Analisis Laporan Keuangan dengan AI + Verifikasi Otomatis

Cara menjalankan:
    streamlit run app.py
"""
import streamlit as st
import sys
from pathlib import Path
import tempfile
import os
import re
from datetime import datetime

# Set PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# ==================== KONFIGURASI HALAMAN ====================
st.set_page_config(
    page_title="Equity Research Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== CSS CUSTOM ====================
st.markdown("""
<style>
    .main-header {
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        color: #1E88E5 !important;
        text-align: center !important;
        padding: 1rem 0 !important;
    }
    .sub-header {
        font-size: 1.3rem !important;
        color: #555 !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
    }
    .card {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #e8e8e8;
    }
    .metric-value {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #1E88E5 !important;
    }
    .metric-label {
        font-size: 0.9rem !important;
        color: #888 !important;
    }
    .stButton button {
        width: 100%;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        padding: 0.8rem !important;
        border-radius: 10px !important;
        background-color: #1E88E5 !important;
        color: white !important;
        border: none !important;
        transition: all 0.3s !important;
    }
    .stButton button:hover {
        background-color: #1565C0 !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 136, 229, 0.4) !important;
    }
    .upload-area {
        border: 3px dashed #1E88E5 !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        text-align: center !important;
        background: #f0f7ff !important;
    }
    .footer {
        text-align: center;
        padding: 2rem 0 0.5rem 0;
        color: #aaa;
        font-size: 0.85rem;
        border-top: 1px solid #eee;
        margin-top: 3rem;
    }
    .badge-success {
        background: #4CAF50;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-danger {
        background: #f44336;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
    }
    .badge-warning {
        background: #FF9800;
        color: white;
        padding: 0.3rem 1rem;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
    }
    .memo-container {
        background: #fafafa;
        border-radius: 12px;
        padding: 2rem;
        border-left: 5px solid #1E88E5;
        line-height: 1.8;
        font-size: 1.05rem;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
st.markdown('<p class="main-header">📊 Equity Research Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Analisis Laporan Keuangan dengan AI + Verifikasi Otomatis</p>', unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("### ⚙️ Pengaturan")
    
    verification_mode = st.toggle(
        "🔒 **Verification Pass**",
        value=True,
        help="ON: Memo dengan angka tanpa sumber akan DIBLOKIR\nOFF: Angka tanpa sumber ditandai [TANPA SUMBER]"
    )
    
    st.markdown("---")
    st.markdown("### 📊 Status Sistem")
    st.markdown("""
    - ✅ Database: Terhubung
    - ✅ Ollama: Running
    - ✅ Model: llama3.2:3b
    """)
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.markdown("""
    1. Upload PDF laporan keuangan
    2. Klik Generate Memo
    3. Lihat analisis dengan citation
    4. Klik angka untuk lihat sumber
    """)
    
    st.markdown("---")
    st.markdown(f"<p style='color:#aaa;font-size:0.8rem;'>v1.0 • {datetime.now().strftime('%Y-%m-%d')}</p>", unsafe_allow_html=True)

# ==================== MAIN AREA ====================
# Upload Section
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    st.markdown("### 📄 Upload Laporan Keuangan")
    st.markdown("*Support: PDF | Maks: 10MB*")
    uploaded_file = st.file_uploader(
        "Pilih file PDF",
        type=["pdf"],
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file is not None:
    # File info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📁 Nama File", uploaded_file.name[:30] + "..." if len(uploaded_file.name) > 30 else uploaded_file.name)
    with col2:
        st.metric("📦 Ukuran", f"{uploaded_file.size / 1024:.1f} KB")
    with col3:
        st.metric("📄 Tipe", uploaded_file.type)
    with col4:
        st.metric("⏱️ Upload", "Berhasil ✅")
    
    # Simpan file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        pdf_path = tmp_file.name
    
    # Generate Button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_clicked = st.button("🚀 Generate Investment Memo", type="primary", use_container_width=True)
    
    if generate_clicked:
        with st.spinner("⏳ Memproses laporan keuangan... (bisa memakan waktu 30-60 detik)"):
            try:
                from equity_research_agent.extraction.pdf_table_extractor import extract_tables_from_pdf
                from equity_research_agent.extraction.schema_mapper import find_balance_sheet, find_income_statement
                from equity_research_agent.calculation.ratio_calculator import calculate_all_ratios
                from equity_research_agent.llm.planning.ratio_planner import plan_relevant_ratios
                from equity_research_agent.memo.memo_generator import generate_investment_memo
                from equity_research_agent.verification.verification_pass import get_verification_summary
                
                progress_bar = st.progress(0, text="Memulai proses...")
                
                progress_bar.progress(10, text="📄 Mengekstrak tabel dari PDF...")
                tables = extract_tables_from_pdf(pdf_path)
                
                progress_bar.progress(30, text="🔍 Mapping data ke struktur keuangan...")
                bs = find_balance_sheet(tables)
                is_ = find_income_statement(tables)
                
                if not bs or not is_:
                    st.error("❌ Balance Sheet atau Income Statement tidak ditemukan dalam PDF")
                    st.info("💡 Pastikan PDF berisi laporan keuangan dengan format standar")
                    st.stop()
                
                progress_bar.progress(50, text="📊 Menghitung rasio keuangan...")
                ratios = calculate_all_ratios(
                    net_income=is_.net_income,
                    total_equity=bs.total_equity,
                    total_liabilities=bs.total_liabilities,
                    total_assets=bs.total_assets,
                    total_revenue=is_.total_revenue,
                )
                
                calculated_ratios = []
                for name, result in ratios.items():
                    if not isinstance(result, dict):
                        calculated_ratios.append({
                            "ratio_name": name,
                            "value": result.value,
                            "formula": result.formula,
                        })
                
                progress_bar.progress(65, text="🧠 Agent menentukan rasio relevan...")
                user_question = "Analisis laporan keuangan perusahaan ini secara komprehensif"
                plan = plan_relevant_ratios(user_question)
                
                progress_bar.progress(80, text="📝 Menyusun investment memo...")
                result = generate_investment_memo(
                    company_id=1,
                    user_question=user_question,
                    calculated_ratios=calculated_ratios,
                    statement_ids=[1],
                    enforce_verification=verification_mode,
                )
                
                progress_bar.progress(100, text="✅ Selesai!")
                
                # ==================== HASIL ====================
                st.markdown("---")
                
                st.markdown("### 📊 Ringkasan Keuangan")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">Rp {bs.total_assets/1_000_000_000:.1f}M</div>
                        <div class="metric-label">Total Aset</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">Rp {bs.total_liabilities/1_000_000_000:.1f}M</div>
                        <div class="metric-label">Total Liabilitas</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">Rp {bs.total_equity/1_000_000_000:.1f}M</div>
                        <div class="metric-label">Total Ekuitas</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-value">Rp {is_.net_income/1_000_000:.1f}M</div>
                        <div class="metric-label">Laba Bersih</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("### 📈 Rasio Keuangan")
                ratio_cols = st.columns(len(calculated_ratios))
                for idx, ratio in enumerate(calculated_ratios):
                    with ratio_cols[idx % len(calculated_ratios)]:
                        value = ratio["value"]
                        if ratio["ratio_name"] in ["ROE", "Net Margin"]:
                            display = f"{value * 100:.2f}%"
                        else:
                            display = f"{value:.4f}"
                        st.markdown(f"""
                        <div class="metric-card">
                            <div class="metric-value">{display}</div>
                            <div class="metric-label">{ratio['ratio_name']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("### ✅ Verification Status")
                
                if verification_mode and result.is_verified:
                    st.markdown('<span class="badge-success">✅ Verified — Semua angka memiliki sumber</span>', unsafe_allow_html=True)
                elif verification_mode and not result.is_verified:
                    st.markdown('<span class="badge-danger">❌ Diblokir — Ada angka tanpa sumber</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-warning">⚠️ Mode Warning — Angka tanpa sumber ditandai</span>', unsafe_allow_html=True)
                
                st.info(get_verification_summary(result.verification_report))
                
                st.markdown("---")
                st.markdown("### 📄 Investment Memo")
                
                st.markdown(f"""
                <div class="memo-container">
                    {result.memo_text}
                </div>
                """, unsafe_allow_html=True)
                
                if not result.is_verified and result.verification_report.orphan_numbers:
                    st.warning(f"⚠️ Ditemukan {len(result.verification_report.orphan_numbers)} angka tanpa sumber: {', '.join(result.verification_report.orphan_numbers)}")
                
                st.markdown("---")
                st.caption("✨ Dibuat dengan Streamlit • Ollama • pgvector")
                
            except ValueError as e:
                st.error(f"🚫 MEMO DIBLOKIR!")
                st.error(f"**Alasan:** {str(e)}")
                st.info("💡 **Verification Pass** mendeteksi angka tanpa citation. Matikan verification di sidebar untuk melihat memo (mode demo).")
            except Exception as e:
                st.error(f"❌ Error: {e}")
                st.exception(e)
        
        try:
            os.unlink(pdf_path)
        except:
            pass

# ==================== FOOTER ====================
st.markdown("""
<div class="footer">
    Equity Research Agent • Built with ❤️ • Streamlit + Ollama + pgvector
</div>
""", unsafe_allow_html=True)