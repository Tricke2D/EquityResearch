# 📊 Equity Research Agent
**Analisis Laporan Keuangan dengan AI + Verifikasi Otomatis**

Alat bantu analisis laporan keuangan yang menggunakan AI untuk menghitung rasio keuangan, menyusun investment memo, dan memastikan setiap angka yang disebut memiliki sumber yang dapat dilacak.

---

## 📑 Daftar Isi
- [Quick Start](#-quick-start)
- [Masalah & Solusi](#-masalah--solusi)
- [Cara Kerja](#-cara-kerja)
- [Arsitektur](#-arsitektur)
- [Instalasi](#-instalasi)
- [Penggunaan](#-penggunaan)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Roadmap](#-roadmap)
- [Troubleshooting](#-troubleshooting)

---

## ⚡ Quick Start

### Dengan Docker (Recommended)
```bash
git clone https://github.com/Tricke2D/equity-research-agent.git
cd equity-research-agent

docker-compose up -d
poetry install
poetry run alembic upgrade head
ollama pull llama3.2:3b
poetry run streamlit run app.py
```
Akses di: `http://localhost:8501`

### Manual Setup
```bash
poetry init && poetry shell
poetry add pdfplumber sqlalchemy psycopg[binary] pydantic python-dotenv pytest alembic ollama pgvector sentence-transformers rapidfuzz pymupdf streamlit pdf2image jinja2

# Setup PostgreSQL
docker run -d --name equity_db -e POSTGRES_PASSWORD=password -p 5432:5432 pgvector/pgvector:pg16
docker exec -it equity_db psql -U postgres -c "CREATE DATABASE equity_research;"

# Setup environment
cat > .env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/equity_research
OLLAMA_HOST=http://localhost:11434
EOF

poetry run alembic upgrade head
ollama pull llama3.2:3b
poetry run streamlit run app.py
```

---

## 🧠 Masalah & Solusi

### Masalah Saat Ini
| Aspek | Tantangan |
|-------|-----------|
| **Manual Analysis** | Laporan keuangan manual memakan waktu + rentan error |
| **AI Hallucination** | LLM sering membuat angka yang tidak ada (berhalusinasi) |
| **Verifikasi** | Sulit melacak sumber setiap angka ke data asli |
| **Risk** | Keputusan investasi berdasarkan data palsu = kerugian besar |

### Solusi: Ground Truth First ✅

```
PDF Upload
    ↓
Ekstraksi Deterministik (pdfplumber - bukan LLM)
    ↓
Kalkulasi Python (Pure functions, 100% testable)
    ↓
Verifikasi Otomatis (Citation tracking)
    ↓
Anti-Halusinasi Gate (Block angka orphan)
    ↓
Investment Memo + Footnote
```

**Kunci solusi:** Angka diambil dari PDF, bukan dihasilkan LLM. LLM hanya untuk reasoning & memo writing.

---

## 🔄 Cara Kerja

### User Flow (Simple)
1. **Upload PDF** — Laporan keuangan perusahaan
2. **Generate Memo** — Sistem memproses & ekstrak data
3. **Verifikasi** — Setiap angka dilacak ke sumbernya
4. **Hasil** — Memo investment dengan footnote + citation

### Internal Pipeline (Technical)

```
1. extract_tables_from_pdf()
   └─ pdfplumber + camelot fallback
   
2. find_balance_sheet() + find_income_statement()
   └─ Schema mapping dengan Pydantic validation
   
3. calculate_all_ratios()
   └─ ROE, Debt-to-Equity, Net Margin, dll
   
4. plan_relevant_ratios(user_question)
   └─ LLM (Ollama) tentukan rasio mana yang relevan
   
5. generate_investment_memo()
   ├─ Draft memo (Ollama)
   ├─ verify_memo_draft()
   │  └─ match_sentence_to_citations() [fuzzy matching]
   ├─ block_if_unverified() [anti-hallucination gate]
   └─ attach_footnotes()
   
6. highlight_source_in_pdf()
   └─ Render halaman PDF dengan highlight kuning
```

### Contoh Output

**Input:**
- PDF: laporan-keuangan-mei-2026.pdf
- Pertanyaan: "Analisis komprehensif laporan ini"

**Metrik Terekstraksi:**
| Metrik | Nilai |
|--------|-------|
| Total Aset | Rp 1.592.981.197 |
| Total Liabilitas | Rp 259.870.771 |
| Total Ekuitas | Rp 1.333.110.426 |
| Laba Bersih | Rp 25.683.371 |
| Total Pendapatan | Rp 38.409.131 |

**Rasio Keuangan:**
| Rasio | Nilai | Interpretasi |
|-------|-------|--------------|
| ROE | 1.93% | Rendah - efisiensi pengembalian investasi kurang optimal |
| Debt-to-Equity | 0.1949 | Sehat - rasio utang terhadap modal rendah |
| Net Margin | 66.87% | Sangat tinggi - profitabilitas sangat baik |
| Current Ratio | 2.50 | Sehat - likuiditas jangka pendek cukup |

---

## 🏗️ Arsitektur

### Komponen Utama

```
┌─────────────────────────────────────────────┐
│      Streamlit UI (Frontend)                │
│  [Upload] [Settings] [Generate] [Display]   │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│                   Backend (Python/Poetry)                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────┐    │
│  │ PDF Extract  │  │ Schema Map   │  │ Ratio Calculator    │    │
│  │              │  │              │  │ • ROE               │    │
│  │ • pdfplumber │  │ • BS Finder  │  │ • Debt-to-Equity    │    │
│  │ • camelot    │  │ • IS Finder  │  │ • P/E Ratio         │    │
│  │              │  │ • Pydantic   │  │ • Current Ratio     │    │
│  └──────────────┘  └──────────────┘  │ • Net Margin        │    │
│                                      │ • Revenue Growth    │    │
│  ┌──────────────┐  ┌──────────────┐  └─────────────────────┘    │
│  │ Agent Plan   │  │ Memo Gen     │                             │
│  │              │  │              │  ┌─────────────────────┐    │
│  │ • Ollama LLM │  │ • Draft      │  │ Verification Pass   │    │
│  │ • JSON out   │  │ • Footnotes  │  │                     │    │
│  │              │  │              │  │ • Claim matcher     │    │
│  └──────────────┘  └──────────────┘  │ • Block orphan #    │    │
│                                      └─────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────────┐
│      PostgreSQL 16 + pgvector                                   │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ companies│  │financial_stmt│  │ citations                │   │
│  └──────────┘  └──────────────┘  │ (embedding, citation)    │   │
│                                  └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow
| Tahap | Input | Process | Output |
|-------|-------|---------|--------|
| Extract | PDF file | pdfplumber | ExtractedTable[] |
| Map | ExtractedTable[] | Schema matching | BalanceSheet, IncomeStatement |
| Calculate | Statement data | Pure Python | RatioDict |
| Plan | User question | Ollama planning | RatioPlan (JSON) |
| Generate | Ratios + statements | Ollama memo gen | Draft memo |
| Verify | Memo text | Fuzzy matching | VerificationReport |
| Output | Verified memo | Footnote format | Final memo + PDF highlight |

---

## 🛠️ Tech Stack

| Technology | Role | Alasan Dipilih |
|------------|------|---|
| **Python 3.11+** | Bahasa utama | Mature data science ecosystem |
| **Poetry** | Dependency mgmt | Reproducible builds |
| **PostgreSQL 16** | Database | Reliable, mature |
| **pgvector** | Vector search | Similarity search untuk perbandingan |
| **pdfplumber** | PDF extraction | Deterministik (tidak seperti LLM vision) |
| **SQLAlchemy** | ORM | Database abstraction |
| **Pydantic** | Validation | Data quality gate |
| **Ollama** | Local LLM | Tanpa API eksternal, privat |
| **llama3.2:3b** | LLM model | Ringan (3B), bisa di RAM 4GB |
| **RapidFuzz** | Fuzzy matching | Citation matching |
| **PyMuPDF** | PDF rendering | Highlight source di PDF |
| **Streamlit** | UI | Fast prototyping |

### Requirements

**Minimal:**
- Python 3.11+
- Docker 20.10+
- PostgreSQL 16 + pgvector
- RAM: 4GB
- Storage: 2GB

**Recommended:**
- RAM: 8GB+
- GPU: NVIDIA (untuk Ollama acceleration)
- Storage: 10GB+

---

## 📥 Instalasi

### Option 1: Docker Compose (Fastest)

```bash
git clone https://github.com/Tricke2D/equity-research-agent.git
cd equity-research-agent

# Start all services
docker-compose up -d

# Setup app
poetry install
poetry run alembic upgrade head
ollama pull llama3.2:3b

# Run
poetry run streamlit run app.py
```

### Option 2: Manual (Linux/Mac)

```bash
# 1. Virtual env
python3.11 -m venv venv
source venv/bin/activate

# 2. Dependencies
poetry install

# 3. PostgreSQL
docker run -d --name equity_db \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  pgvector/pgvector:pg16

# 4. Create database
docker exec -it equity_db psql -U postgres \
  -c "CREATE DATABASE equity_research;"

# 5. Environment
cat > .env << EOF
DATABASE_URL=postgresql://postgres:secure_password@localhost:5432/equity_research
OLLAMA_HOST=http://localhost:11434
EOF

# 6. Migrations
poetry run alembic upgrade head

# 7. LLM model
ollama pull llama3.2:3b

# 8. Run app
poetry run streamlit run app.py
```

### Option 3: Manual (Windows)

```powershell
# Virtual env
python -m venv venv
.\venv\Scripts\Activate.ps1

# Dependencies
poetry install

# PostgreSQL (Docker Desktop required)
docker run -d --name equity_db -e POSTGRES_PASSWORD=password -p 5432:5432 pgvector/pgvector:pg16

# Create database
docker exec -it equity_db psql -U postgres -c "CREATE DATABASE equity_research;"

# .env
@"
DATABASE_URL=postgresql://postgres:password@localhost:5432/equity_research
OLLAMA_HOST=http://localhost:11434
"@ | Out-File -Encoding UTF8 .env

# Migrations & model
poetry run alembic upgrade head
ollama pull llama3.2:3b
poetry run streamlit run app.py
```

---

## 📖 Penggunaan

### Workflow di UI

1. **Buka Streamlit** → `http://localhost:8501`
2. **Upload PDF** → Klik "Browse files" → pilih laporan keuangan
3. **Configure** → Di sidebar, atur:
   - Verification mode: **ON** (block orphan) atau **OFF** (warning)
   - Question: "Analisis laporan ini"
4. **Generate** → Klik "🚀 Generate Investment Memo"
5. **Review Results:**
   - 📊 Financial Summary (Total Aset, Liabilitas, Ekuitas)
   - 📈 Calculated Ratios
   - ✅ Verification Status
   - 📝 Investment Memo (dengan footnote)
   - 🖍️ PDF Highlights (lihat sumber di halaman asli)

### Mode Verification

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Strict (ON)** | Memo diblokir jika ada angka orphan | Production, client-facing |
| **Advisory (OFF)** | Angka orphan ditandai `[TANPA SUMBER]` | Exploratory, draft analysis |

---

## 📡 API Reference

### PDF Extraction

```python
from equity_research_agent.extraction.pdf_table_extractor import extract_tables_from_pdf

tables = extract_tables_from_pdf("path/to/report.pdf")
# Returns: List[ExtractedTable]
#   - rows: list of dict
#   - page_number: int
#   - extraction_method: str ("pdfplumber" | "camelot")
```

### Schema Mapping

```python
from equity_research_agent.extraction.schema_mapper import (
    find_balance_sheet,
    find_income_statement
)

bs = find_balance_sheet(tables)      # BalanceSheetData | None
is_ = find_income_statement(tables)  # IncomeStatementData | None
```

### Ratio Calculator

```python
from equity_research_agent.calculation.ratio_calculator import calculate_all_ratios

ratios = calculate_all_ratios(
    net_income=25683371,
    total_equity=1333110426,
    total_liabilities=259870771,
    total_assets=1592981197,
    total_revenue=38409131,
    current_assets=800000000,
    current_liabilities=320000000,
)
# Returns: {
#   "roe": 0.0193,
#   "debt_to_equity": 0.1949,
#   "net_margin": 0.6687,
#   "current_ratio": 2.50,
#   "pe_ratio": None,
#   "revenue_growth_yoy": None
# }
```

### Agent Planning

```python
from equity_research_agent.llm.planning.ratio_planner import plan_relevant_ratios

plan = plan_relevant_ratios("Apakah perusahaan ini undervalued?")
# Returns: RatioPlan(
#   relevant_ratios=["roe", "pe_ratio", "debt_to_equity"],
#   reasoning="ROE menunjukkan efisiensi..."
# )
```

### Memo Generation

```python
from equity_research_agent.memo.memo_generator import generate_investment_memo

result = generate_investment_memo(
    company_id=1,
    user_question="Analisis laporan keuangan komprehensif",
    calculated_ratios=ratios,
    statement_ids=[bs.id, is_.id],
    enforce_verification=True,  # Strict mode
)
# Returns: MemoResult(
#   memo_text="Investment Memo\n...",
#   verification_report=VerificationReport(...),
#   is_verified=True
# )
```

### Verification Pass

```python
from equity_research_agent.verification.verification_pass import (
    verify_memo_draft,
    block_if_unverified
)

report = verify_memo_draft(sentences, statement_ids)
# Returns: VerificationReport with match results

block_if_unverified(report, strict=True)  # Raises ValueError if orphan found
```

### PDF Highlighting

```python
from equity_research_agent.visualization.pdf_highlighter import highlight_source_in_pdf

result = highlight_source_in_pdf(
    pdf_path="path/to/report.pdf",
    page_number=1,
    search_text="Total Aset"
)
# Returns: HighlightedPage(image_bytes=..., page_number=1)
```

---

## 🧪 Testing

### Menjalankan Tests

```bash
# Semua test
poetry run pytest

# Test spesifik
poetry run pytest tests/calculation/
poetry run pytest tests/extraction/
poetry run pytest tests/db/
poetry run pytest -v  # Verbose
poetry run pytest --cov  # Coverage report
```

### Struktur Test

| Lokasi | Scope | Test |
|--------|-------|------|
| `tests/calculation/` | Unit | Fungsi kalkulator rasio |
| `tests/extraction/` | Unit | PDF extraction + schema mapping |
| `tests/verification/` | Unit | Citation matching logic |
| `tests/db/` | Integration | Database + pgvector |
| `test_*.py` (root) | E2E | Full pipeline dengan sample PDF |

---

## 📁 Project Structure

```
equity-research-agent/
├── app.py                              # Streamlit UI utama
├── pyproject.toml                      # Poetry dependencies
├── .env.example                        # Environment template
├── docker-compose.yml                  # Docker orchestration
├── alembic.ini                         # Migration config
│
├── alembic/versions/                   # Database migrations
│
├── src/equity_research_agent/
│   ├── config.py                       # Config loader
│   ├── db/
│   │   ├── models.py                   # SQLAlchemy ORM
│   │   ├── session.py                  # DB session
│   │   └── repositories/               # Repository pattern
│   ├── extraction/
│   │   ├── pdf_table_extractor.py      # pdfplumber + camelot
│   │   ├── schema_mapper.py            # BS/IS detection
│   │   └── validators.py               # Pydantic schemas
│   ├── calculation/
│   │   └── ratio_calculator.py         # 6 rasio keuangan
│   ├── llm/
│   │   ├── ollama_client.py            # Ollama wrapper
│   │   ├── planning/
│   │   │   └── ratio_planner.py        # Agent planning
│   │   └── tools/
│   │       └── calculate_ratio_tool.py # Function calling
│   ├── citation/
│   │   ├── citation_tracker.py         # Record citations
│   │   └── claim_matcher.py            # Fuzzy match
│   ├── memo/
│   │   ├── memo_generator.py           # Orchestrate memo
│   │   └── footnote_formatter.py       # Footnote formatting
│   ├── verification/
│   │   └── verification_pass.py        # Anti-hallucination
│   └── visualization/
│       └── pdf_highlighter.py          # PDF rendering
│
├── tests/                              # Unit & integration tests
│   ├── extraction/
│   ├── calculation/
│   ├── verification/
│   └── db/
│
└── scripts/
    └── init_db.sh                      # DB setup helper
```

---

## ⚙️ Fitur & Capabilities

### User-Facing Features

| Fitur | Deskripsi |
|-------|-----------|
| 📄 **Upload PDF** | Upload laporan keuangan langsung |
| 📊 **Auto Ratio Calculation** | Hitung 6 rasio keuangan otomatis |
| 🧠 **AI Agent Planning** | LLM tentukan rasio mana yang relevan |
| 📝 **Investment Memo** | Analisis komprehensif dengan reasoning |
| 🔒 **Verification Gate** | Setiap angka diverifikasi ke sumber |
| 🖍️ **PDF Highlight** | Lihat lokasi sumber di PDF asli |
| ⚡ **Batch Mode** | Processing cepat (30-60 detik) |

### Technical Capabilities

| Capability | Implementation |
|-----------|-----------------|
| PDF Extraction | pdfplumber + camelot fallback |
| Table Detection | Regex + layout analysis |
| Schema Recognition | Keyword matching + Pydantic validation |
| Ratio Calculation | Pure Python (100% testable) |
| LLM Integration | Ollama llama3.2:3b local |
| Citation Tracking | PostgreSQL + citation table |
| Fuzzy Matching | RapidFuzz (80% threshold) |
| Anti-Hallucination | Claim matcher + verification gate |
| PDF Rendering | PyMuPDF (highlight + annotation) |

---

## ⚠️ Limitations & Roadmap

### Current Limitations

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| **Text-only PDFs** | Scan/image PDFs tidak bisa diekstrak | Use OCR tool dulu (Tesseract) |
| **LLM 3B model** | Terkadang function calling inconsistent | Upgrade ke llama2:7b |
| **Fuzzy matching** | False positive/negative pada angka unik | Kalibrasi threshold |
| **4GB RAM minimum** | Device terbatas tidak bisa jalan | Dukungan tinyllama:1b (Q1 2027) |
| **Single company** | Hanya analisis 1 perusahaan | Multi-company comparison (Q1 2027) |
| **No auth** | Data tidak aman untuk production | Auth layer (Q2 2027) |

### Roadmap

**✅ Completed (Phase 1-3)**
- PDF extraction & schema mapping
- Ratio calculator (6 rasio)
- Agent planning & memo generation
- Citation tracking & verification
- Streamlit UI

**📅 Q4 2026 - Q2 2027**
- OCR untuk PDF scan/image
- Multi-company comparison
- Export to PDF
- Batch processing
- Authentication & user isolation
- REST API
- Cloud deployment

**🔮 Future (2027+)**
- Mobile app
- Advanced financial modeling
- Real-time data feeds
- Competitor benchmarking

---

## 🔧 Troubleshooting

### ❌ "No module named 'src'"
**Penyebab:** Python tidak mengenali folder src.

**Solusi:**
```bash
# Linux/Mac
export PYTHONPATH=$(pwd)/src:$PYTHONPATH

# Windows
set PYTHONPATH=C:\path\to\project\src
```

### ❌ "Ollama: connection refused"
**Penyebab:** Ollama service tidak running.

**Solusi:**
```bash
ollama serve  # Start Ollama
ollama pull llama3.2:3b  # Pull model
```

### ❌ "psycopg2: No module named 'psycopg2'"
**Penyebab:** PostgreSQL driver tidak terinstall.

**Solusi:**
```bash
poetry add psycopg2-binary
# Atau ubah URL database: postgresql+psycopg://...
```

### ❌ "ConnectionResetError: [WinError 10054]"
**Penyebab:** Bug Windows + Python 3.14 + asyncio.

**Solusi:** Abaikan — tidak mempengaruhi fungsi aplikasi.

### ❌ "EXTRACT: Failed to extract tables"
**Penyebab:** PDF memiliki tabel kompleks atau scan.

**Solusi:**
1. Gunakan camelot extractor (otomatis fallback)
2. Jika masih gagal, convert PDF dengan tools eksternal
3. Laporkan ke GitHub dengan sample PDF

---

## 🤝 Contributing

### Workflow
1. Fork repository
2. Branch dari `main`: `git checkout -b feature/your-feature`
3. Commit dengan pesan jelas
4. Push & open Pull Request

### Development Setup
```bash
git clone https://github.com/yourusername/equity-research-agent.git
cd equity-research-agent

poetry install
poetry run pytest  # Ensure tests pass
poetry run pre-commit install  # Optional: setup git hooks
```

### Code Standards
- **Format:** Black (`poetry run black .`)
- **Imports:** isort (`poetry run isort .`)
- **Types:** mypy (`poetry run mypy src/`)
- **Tests:** pytest (`poetry run pytest`)
- **Docs:** Docstrings (Google style)

---

## 📄 License & Credits

**License:** MIT License (lihat `LICENSE` file)

**Author:** Muhamad Syukron Zakka

**Acknowledgments:**
- [Ollama](https://ollama.ai) — Local LLM runtime
- [pgvector](https://github.com/pgvector/pgvector) — Vector similarity
- [Streamlit](https://streamlit.io) — UI framework
- [pdfplumber](https://github.com/jsvine/pdfplumber) — PDF extraction
- [SQLAlchemy](https://sqlalchemy.org) — ORM
- [Pydantic](https://pydantic-settings.readthedocs.io) — Validation

---

## 📞 Support

Punya pertanyaan atau issue?

- **GitHub Issues:** [Create issue](https://github.com/Tricke2D/equity-research-agent/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Tricke2D/equity-research-agent/discussions)
- **Email:** mhdsyukronzakka@gmail.com

---

**Last updated:** August 2026 | [Star on GitHub](https://github.com/Tricke2D/equity-research-agent) ⭐
