# HDFC Mutual Fund FAQ RAG Architecture

## 1. System Overview

This system is a **facts-only, production-grade RAG chatbot** designed to answer user queries about 5 specific HDFC Mutual Fund schemes. It adheres to strict compliance rules: **No Advice, No PII, No Opinions**.

## 2. Decision Logic & Query Classification

The system employs a strict classification step before or during generation to enforce boundaries.

1. **Allowed (Factual):** Queries about scheme features (exit load, NAV, lock-in, asset allocation, objective).
2. **Refused (Advisory/Opinion/Forecast):** Queries asking "Is this good?", "Will it go up?", "Create a portfolio for me", "Compare with X bank".

| Measure | Strategy |
| :--- | :--- |
| **When to Answer** | ONLY when the query is factual AND the answer exists in the retrieved context. |
| **When to Refuse** | When query is Advice, Opinion, Future Performance, or Off-Topic. ALSO refuse if context is missing. |
| **How to Stay Factual** | System Prompt strictness + Temperature 0 + "Answer only from context" constraint. |

---

## 3. Data Ingestion Pipeline

### A. Document Processing

* **Source:** PDF Files for 5 Schemes.
* **Parser:** `PyMuPDF` (fitz) or `Unstructured` for high-fidelity text extraction. Key metadata (Scheme Name, Source URL, Date) MUST be attached to every chunk.

### B. Chunking Strategy

* **Method:** RecursiveCharacterTextSplitter.
* **Size:** **512 Tokens**.
* **Overlap:** **50 Tokens**.
* **Reasoning:** 512 tokens (~300-400 words) provides sufficient context for a specific fact (e.g., "Exit Load structure") without including too much irrelevant noise. Overlap ensures sentences aren't cut mid-context.

### C. Embeddings

* **Model:** **Gemini Embedding 001** (`models/embedding-001`).
* **Reasoning:** Native integration with Google ecosystem, optimized for semantic retrieval, and high performance on English retrieval benchmarks compared to older open-source models.

### D. Vector Store

* **Choice:** **ChromaDB** (Persistent Client).
* **Reasoning:** Open-source, supports complex metadata filtering (crucial for filtering by specific Scheme Name), and easy to scale for a dataset of this size (~100s of PDFs).

---

## 4. Retrieval Strategy

* **Method:** **Hybrid Search (Semantic + Metadata Filter)**.
* **Filtering:** If the user query specifically mentions a scheme (e.g., "HDFC Top 100 exit load"), the retriever **MUST** filter chunks by `metadata['scheme_name']` to prevent hallucinations from other schemes.
* **Top-K:** Retrieve **top 5** chunks.
* **Re-ranking (Optional):** If precision is low, add a Cross-Encoder re-ranker step, but standard top-5 with metadata filtering should suffice for this corpus size.

---

## 5. Generation & Prompting Strategy

### A. LLM

* **Model:** **Gemini 1.5 Flash** (recommended for speed/cost) or **Gemini 1.5 Pro**.
* **Temperature:** `0.0` (Maximum Determinism).

### B. Citation Enforcement

* **Mechanism:**
    1. Context chunks are provided with IDs/URLs.
    2. Prompt instructs LLM to append "Source: [URL]" from the used chunk.
    3. **Post-Process Check:** If the output does not contain a valid URL from the context, the system appends the URL of the top-ranked retrieved chunk automatically or returns a fallback error message if confidence is low.

### C. Refusal Rules

* **Refusal Message Template:**
    > "I am a facts-only assistant and cannot provide investment advice, opinions, or forecasts. Please refer to the official scheme documents or consult a financial advisor. Source: [HDFC Mutual Fund](https://www.hdfcfund.com/)"
* **Output Constraint:** Max 3 sentences.

---

## 6. Auditability

* **Logs:** Every interaction must log:
  * Input Query
  * Retrieved Chunk IDs & Scores
  * System Decision (Answer vs Refuse)
  * Final Output
  * Timestamp
* This ensures the "Why did it say that?" question can always be answered by looking at the retrieved context.
