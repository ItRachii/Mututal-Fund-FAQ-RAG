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
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")

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
        Loads URL mapping. Prioritizes official landing pages from corpus.md
        for user-friendly citations.
        """
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
            
            # Map scheme to slug
            slug_map = {
                "HDFC Large Cap Fund": "hdfc-large-cap-fund",
                "HDFC Flexi Cap Fund": "hdfc-flexi-cap-fund",
                "HDFC ELSS Tax Saver": "hdfc-elss-tax-saver",
                "HDFC Balanced Advantage Fund": "hdfc-balanced-advantage-fund",
                "HDFC Liquid Fund": "hdfc-liquid-fund"
            }
            
            fund_slug = slug_map.get(scheme_name)
            
            # If slug not found, try falling back to filename parsing (redundancy check)
            if not fund_slug:
                filename = os.path.basename(full_path.replace('\\', '/')).lower()
                if "largecap" in filename or "top 100" in filename: fund_slug = "hdfc-large-cap-fund"
                elif "flexicap" in filename or "multi-cap" in filename: fund_slug = "hdfc-flexi-cap-fund"
                elif "elss" in filename or "tax_saver" in filename: fund_slug = "hdfc-elss-tax-saver"
                elif "balancedadvantage" in filename or "prudence" in filename: fund_slug = "hdfc-balanced-advantage-fund"
                elif "liquid" in filename: fund_slug = "hdfc-liquid-fund"

            # 2. Determine the best URL
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
            
            # The doc.page_content now contains its own header with File/Scheme/Doc/Date
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
