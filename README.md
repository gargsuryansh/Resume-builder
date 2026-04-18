# 🚀 Smart AI Resume Analyzer & Builder

An advanced, enterprise-grade system that transforms unstructured resumes into actionable talent insights. Powered by **FastAPI** and **Google Gemini**, it provides deep analysis, ATS optimization, and a powerful HR Dashboard for modern recruitment teams.

---

## ✨ Key Features (Kya-kya hai isme?)

### 🧠 1. AI-Driven Resume Analysis
*   **Deep Extraction:** Multi-format support (PDF/DOCX) with Google Gemini integration for structured data extraction.
*   **Full Analysis:** Detailed feedback on Strengths, Weaknesses, and professional suggestions.
*   **ATS Scoring:** Real-time ATS score calculation and keyword optimization matching.

### 💼 2. Candidate Data Persistence (Neon PostgreSQL)
*   **Structured Storage:** Permanent storage of candidate details (Experience, Skills, Location, etc.) in **Neon PostgreSQL**.
*   **ORM Layer:** Clean and scalable data management using **SQLAlchemy ORM**.
*   **Migrations:** Seamless database schema updates via **Alembic**.

### 🎯 3. Advanced HR Dashboard (Candidate Filtering)
*   **Precision Filtering:** Shortlist talent based on:
    *   **Job Role** (Fuzzy matching)
    *   **Min Experience** (Numerical comparison)
    *   **Location** (Regional search)
    *   **Skills** (PostgreSQL Array Overlap for precise matching)
    *   **ATS Score** (High-quality shortlisting)

### 🛠️ 4. Professional Resume Builder
*   **One-Click Generation:** Transform candidate data into polished PDF or DOCX professional resumes.
*   **Custom Templates:** Quick layout selection for high-impact resumes.

---

## 🛠️ Tech Stack

*   **Backend:** FastAPI (Python)
*   **Database:** PostgreSQL (Neon) with SQLAlchemy ORM
*   **AI Engine:** Google Gemini (Gemini 1.5 Flash)
*   **Migrations:** Alembic
*   **Parsing:** pdfplumber, python-docx, Pytesseract (OCR Fallback)
*   **Automation:** Selenium (LinkedIn scraping support)
*   **Analytics:** Pandas, Plotly (for Dashboard charts)

---

## 📂 Project Structure

```bash
Resume-builder/
├── api/                # FastAPI routes & App initialization
│   ├── routes/         # Modular routers (resume, candidate)
│   └── main.py         # Entry point for FastAPI
├── models/             # SQLAlchemy Database Models (Candidate, etc.)
├── schemas/            # Pydantic Schemas for validation & API responses
├── services/           # Business Logic Layer (CRUD, Filter logic)
├── utils/              # AI Logic & Extraction utility classes
├── config/             # Database & Environment configurations
├── alembic/            # Database migration scripts
├── data/               # Persistent data storage (local fallback)
└── requirements.txt    # Project dependencies
```

---

## 🚀 Getting Started

### 1. Prerequisites
*   Python 3.9+ 
*   PostgreSQL (Neon.tech recommended)
*   Google Gemini API Key

### 2. Installation
```bash
# Clone the repository
git clone <repo-url>
cd Resume-builder

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Setup
Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql://user:password@host.neon.tech/dbname?sslmode=require

# AI Services
GOOGLE_API_KEY=your_gemini_key_here
OPENROUTER_API_KEY=your_claude_key_here (optional)

# Security
JWT_SECRET=your_super_secret_key
```

### 4. Database Migrations
Create your tables in PostgreSQL:
```bash
alembic upgrade head
```

### 5. Running the App
```bash
python run_app.py
```
The API will be live at `http://localhost:8000`.

---

## 🔌 API Endpoints (Highlights)

*   `POST /analyze/`: Multi-step resume processing & DB persistence.
*   `GET /candidates/search`: Advanced filtering for the HR Dashboard.
*   `GET /dashboard/metrics`: Real-time stats and recruitment trends.

---

## 🛡️ Security & Notes
*   **JWT Auth:** Admin and HR Dashboard routes are secured using JWT (JSON Web Tokens).
*   **Neon SSL:** Database connections are encrypted for production security.
*   **Structured AI:** LLM prompts are optimized for 100% JSON accuracy.

---

Developed with ❤️ for building the next generation of HR-Tech.
