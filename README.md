# HDFC Mutual Fund FAQ Assistant

A production-grade, facts-only RAG chatbot for HDFC Mutual Fund schemes.

## 🚀 Overview

This assistant answers factual queries about 5 HDFC Mutual Fund schemes using a localized RAG (Retrieval-Augmented Generation) pipeline. It is designed with strict compliance guardrails:

- **No Advice**: Politely refuses investment recommendations.
- **Factual Only**: Answers based strictly on official SID/KIM documents and portal data.
- **Auditable**: Provides direct links to official sources for every answer.
- **Concise**: All responses are 3 sentences or fewer.

## 📂 Scope

- **AMC**: HDFC Asset Management Company (AMC).
- **Schemes**: HDFC Large Cap Fund, HDFC Flexi Cap Fund, HDFC ELSS Tax Saver, HDFC Balanced Advantage Fund, HDFC Liquid Fund.

## 🛠️ Setup Instructions

### 1. Prerequisites

- Python 3.13 (Required for ChromaDB compatibility).
- OpenAI API Key.

### 2. Installation

```bash
# Create virtual environment
py -3.13 -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=sk-...
```

### 4. Running the Application

```bash
# Step 1: Ingest Data (Processes PDFs into Vector Store)
python ingest.py

# Step 2: Start Backend API
python api.py

# Step 3: Start Streamlit Frontend (New Terminal)
streamlit run streamlit_app.py
```

## ⚠️ Known Limits

- **Static Knowledge**: Data is based on sources updated as of February 2026.
- **No PII**: The system does not support queries involving personal account data (PAN, Aadhaar).
- **No Computations**: The bot does not calculate returns or compare schemes mathematically.

## ⚖️ Disclaimer

**Facts-only. No investment advice.** This tool is for informational purposes only. Refer to official scheme documents before investing.
