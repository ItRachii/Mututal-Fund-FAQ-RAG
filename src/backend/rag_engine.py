import os
import json
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

# Configuration
CHROMA_DB_DIR = "./chroma_db"
EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "gpt-4o-mini"


class RAGService:
    def __init__(self):
        # 1. Try environment variables, then falls back to Streamlit secrets for cloud deployment
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            try:
                import streamlit as st
                self.api_key = st.secrets.get("OPENAI_API_KEY")
            except:
                pass
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found. Please set it in .env or Streamlit Secrets.")

        # Load Manifest for URL mapping
        self.url_map = {}
        self._load_manifest()

        # 1. Initialize Embeddings
        self.embeddings = OpenAIEmbeddings(
            model=EMBEDDING_MODEL, 
            openai_api_key=self.api_key
        )

        # 2. Load Vector Store
        if not os.path.exists(CHROMA_DB_DIR):
            raise FileNotFoundError(f"ChromaDB not found at '{CHROMA_DB_DIR}'. Run ingest.py first.")
        
        self.vector_store = Chroma(
            collection_name="hdfc_mutual_fund",
            embedding_function=self.embeddings,
            persist_directory=CHROMA_DB_DIR
        )

        self.retriever = self.vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 10, "fetch_k": 30, "lambda_mult": 0.5}
        )

        # 3. Initialize LLM
        self.llm = ChatOpenAI(
            model=LLM_MODEL, 
            temperature=0.0, 
            openai_api_key=self.api_key
        )

        # 4. Setup Chain
        self.system_prompt_text = self._load_system_prompt()
        
        template = """{system_prompt}

Context:
{context}

User: {question}
Assistant:"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "{system_prompt}"),
            ("human", "Context:\n{context}\n\nQuestion: {question}")
        ])

        self.chain = (
            {
                "context": self.retriever | self._format_docs, 
                "question": RunnablePassthrough(), 
                "system_prompt": lambda x: self.system_prompt_text
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )

    def _load_manifest(self):
        """
        Loads URL mapping. Prioritizes specific PDF links provided by user,
        then fund landing pages from corpus.md for user-friendly citations.
        """
        # Specific PDF Mapping (User Provided)
        self.pdf_url_map = {
            # HDFC LARGE CAP FUND
            "HDFC_LargeCapFund_SID_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Large%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf",
            "HDFC_LargeCapFund_KIM_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Large%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf",
            "HDFC_LargeCapFund_Leaflet_Jan_2026.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2026-02/HDFC%20Large%20Cap%20Fund%20Leaflet%20%28Jan%202026%29.pdf",
            "HDFC_LargeCapFund_Presentation_September_2025.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2025-10/HDFC%20Large%20Cap%20Fund%20Presentation%20%28September%202025%29.pdf",
            "HDFC_LargeCapFund_Fund_Facts_January_2026.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2026-02/Fund%20Facts%20-%20HDFC%20Large%20Cap%20Fund_January%2026.pdf",
            
            # HDFC FLEXI CAP FUND
            "HDFC_FlexiCap_SID_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Flexi%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf",
            "HDFC_FlexiCap_KIM_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Flexi%20Cap%20Fund%20dated%20November%2021%2C%202025_1.pdf",
            "HDFC_FlexiCap_Fund_Facts_Jan_2026.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2026-02/Fund%20Facts%20-%20HDFC%20Flexi%20Cap%20Fund_January%2026.pdf",
            "HDFC_FlexiCap_Presentation_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2025-12/HDFC%20Flexi%20Cap%20Fund%20Presentation%20%28November%202025%29.pdf",
            "HDFC_FlexiCap_Leaflet_Dec_2025.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2025-12/HDFC%20Flexi%20Cap%20Fund%20Leaflet%20%28December%202025%29.pdf",
            
            # HDFC BALANCE ADVANTAGE FUND
            "HDFC_BalancedAdvantage_SID_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Balanced%20Advantage%20Fund%20dated%20November%2021%2C%202025_0.pdf",
            "HDFC_BalancedAdvantage_KIM_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Balanced%20Advantage%20Fund%20dated%20November%2021%2C%202025_0.pdf",
            "HDFC_BalancedAdvantage_Fund_Facts_Jan_2026.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2026-02/Fund%20Facts%20-%20HDFC%20Balanced%20Advantage%20Fund_January%2026.pdf",
            "HDFC_BalancedAdvantage_Presentation_Jan_2026.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2026-02/Presentation%20-%20HDFC%20Balanced%20Advantage%20Fund%20%28Jan%202026%29.pdf",
            "HDFC_BalancedAdvantage_Leaflet_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2025-11/Leaflet%20-%20HDFC%20Balanced%20Advantage%20Fund%20%28November%202025%29.pdf",
            
            # HDFC Tax Saver (ELSS)
            "HDFC_ELSS_Tax_Saver_SID_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20ELSS%20Tax%20Saver%20dated%20November%2021%2C%202025.pdf",
            "HDFC_ELSS_Tax_Saver_KIM_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20ELSS%20Tax%20Saver%20dated%20November%2021%2C%202025_0.pdf",
            "HDFC_ELSS_Tax_Saver_Presentation_Oct_2025.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2025-10/HDFC%20ELSS%20Tax%20saver%20Presentation%20%28October%202025%29.pdf",
            "HDFC_ELSS_Tax_Saver_Leaflet_Jan_2024.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2025-01/HDFC%20ELSS%20%20Tax%20saver%20Leaflet%20-%20January%202024%20%281%29.pdf",
            "HDFC_ELSS_Tax_Saver_Fund_Facts_Jan_2026.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2026-02/Fund%20Facts%20-%20HDFC%20TaxSaver%20Fund_January%2026.pdf",
            
            # HDFC Liquid Fund
            "HDFC_Liquid_SID_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20Liquid%20Fund%20dated%20November%2021%2C%202025.pdf",
            "HDFC_Liquid_KIM_21_Nov_2025.pdf": "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Liquid%20Fund%20dated%20November%2021%2C%202025.pdf",
            "HDFC_Liquid_Fund_Facts_Dec_2025.pdf": "https://files.hdfcfund.com/s3fs-public/Others/2025-12/Fund%20Facts%20-%20HDFC%20Liquid%20Fund%20-%20December%202025%20%5Ba%5D.pdf",
        }

        # Primary Mapping from corpus.md
        self.url_map = {
            "HDFC_LargeCap_ProductPage": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-large-cap-fund/direct",
            "HDFC_LargeCap_KIM": "https://www.hdfcfund.com/investor-services/fund-documents/kim",
            "HDFC_LargeCapFund_SID_21_Nov_2025": "https://www.hdfcfund.com/investor-services/fund-documents/sid",
            "HDFC_FlexiCap_ProductPage": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-flexi-cap-fund/direct",
            "HDFC_FlexiCap_KIM": "https://www.hdfcfund.com/investor-services/fund-documents/kim",
            "HDFC_ELSS_ProductPage": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-elss-tax-saver/direct",
            "HDFC_ELSS_KIM": "https://www.hdfcfund.com/investor-services/fund-documents/kim",
            "HDFC_BalancedAdvantage_ProductPage": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-balanced-advantage-fund/direct",
            "HDFC_BalancedAdvantage_KIM": "https://www.hdfcfund.com/investor-services/fund-documents/kim",
            "HDFC_Liquid_ProductPage": "https://www.hdfcfund.com/explore/mutual-funds/hdfc-liquid-fund/direct",
            "HDFC_Liquid_KIM": "https://www.hdfcfund.com/investor-services/fund-documents/kim",
            "HDFC_Factsheets": "https://www.hdfcfund.com/investor-services/factsheets",
            "HDFC_SchemeSummary": "https://www.hdfcfund.com/investor-services/fund-documents/scheme-summary",
            "AMFI_NAV": "https://www.amfiindia.com/spages/NAVAll.txt",
        }
        
        # Fallback to manifest for any missing entries
        manifest_path = "raw/corpus_manifest.json"
        if os.path.exists(manifest_path):
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for doc in data.get("documents", []):
                        # Map base filename to URL
                        name = doc.get("name")
                        url = doc.get("url")
                        if name and url and name not in self.url_map:
                            self.url_map[name] = url
            except Exception as e:
                print(f"Warning: Failed to load manifest fallback: {e}")

    def _load_system_prompt(self):
        try:
            with open("system_prompt.md", "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return "You are a helpful assistant. Answer the user's question based on the context."

    def _format_docs(self, docs):
        formatted = []
        for doc in docs:
            # Prefer enriched metadata if available
            scheme_name = doc.metadata.get('scheme_name')
            doc_type = doc.metadata.get('document_name')
            full_path = doc.metadata.get('source', 'Unknown')
            filename = os.path.basename(full_path.replace('\\', '/'))
            
            # 1. Check if we have a direct PDF mapping for this filename
            public_url = self.pdf_url_map.get(filename)
            
            # 2. If no direct PDF link, fall back to landing pages
            if not public_url:
                # Map scheme to slug
                slug_map = {
                    "HDFC Large Cap Fund": "hdfc-large-cap-fund",
                    "HDFC Flexi Cap Fund": "hdfc-flexi-cap-fund",
                    "HDFC ELSS Tax Saver": "hdfc-elss-tax-saver",
                    "HDFC Balanced Advantage Fund": "hdfc-balanced-advantage-fund",
                    "HDFC Liquid Fund": "hdfc-liquid-fund"
                }
                
                fund_slug = slug_map.get(scheme_name)
                
                # Redundancy check for slug
                if not fund_slug:
                    filename_lower = filename.lower()
                    if "largecap" in filename_lower or "top 100" in filename_lower: fund_slug = "hdfc-large-cap-fund"
                    elif "flexicap" in filename_lower or "multi-cap" in filename_lower: fund_slug = "hdfc-flexi-cap-fund"
                    elif "elss" in filename_lower or "tax_saver" in filename_lower: fund_slug = "hdfc-elss-tax-saver"
                    elif "balancedadvantage" in filename_lower or "prudence" in filename_lower: fund_slug = "hdfc-balanced-advantage-fund"
                    elif "liquid" in filename_lower: fund_slug = "hdfc-liquid-fund"

                if fund_slug:
                    public_url = f"https://www.hdfcfund.com/explore/mutual-funds/{fund_slug}/direct"
                elif doc_type and "Factsheet" in doc_type:
                    public_url = "https://www.hdfcfund.com/investor-services/factsheets"
                elif doc_type and "SID" in doc_type:
                    public_url = "https://www.hdfcfund.com/investor-services/fund-documents/sid"
                elif doc_type and "KIM" in doc_type:
                    public_url = "https://www.hdfcfund.com/investor-services/fund-documents/kim"
                else:
                    public_url = "https://www.hdfcfund.com/explore/mutual-funds"
            
            # Append doc with source link
            formatted.append(f"--- Document Source ---\n{doc.page_content}\nSource Link: {public_url}")
        return "\n\n".join(formatted)

    def query(self, user_question: str) -> str:
        """
        Queries the RAG system with a user question.
        Returns the answer as a string.
        """
        try:
            response = self.chain.invoke(user_question)
            return response
        except Exception as e:
            return f"Error generating response: {str(e)}"
