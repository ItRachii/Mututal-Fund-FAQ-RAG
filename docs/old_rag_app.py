import os
import argparse
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
LLM_MODEL = "gpt-4.1-nano"

def load_system_prompt():
    try:
        with open("system_prompt.md", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print("Warning: system_prompt.md not found. Using default prompt.")
        return "You are a helpful assistant. Answer the user's question based on the context."

def format_docs(docs):
    return "\n\n".join(f"Context: {doc.page_content}\nSource: {doc.metadata.get('source', 'Unknown')}" for doc in docs)

def main():
    parser = argparse.ArgumentParser(description="HDFC Mutual Fund RAG Chatbot")
    parser.add_argument("query", nargs="?", help="The user query")
    args = parser.parse_args()

    # 1. Initialize Embeddings
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found.")
        return

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=api_key)

    # 2. Load Vector Store
    if not os.path.exists(CHROMA_DB_DIR):
        print(f"Error: ChromaDB not found at '{CHROMA_DB_DIR}'. Run ingest.py first.")
        return

    try:
        vector_store = Chroma(
            collection_name="hdfc_mutual_fund",
            embedding_function=embeddings,
            persist_directory=CHROMA_DB_DIR
        )
    except Exception as e:
        print(f"Error loading ChromaDB: {e}")
        return

    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    # 3. Initialize LLM
    llm = ChatOpenAI(model=LLM_MODEL, temperature=0.0, openai_api_key=api_key)

    # 4. Setup Chain
    system_prompt_text = load_system_prompt()
    
    template = """{system_prompt}

Context:
{context}

User: {question}
Assistant:"""

    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough(), "system_prompt": lambda x: system_prompt_text}
        | prompt
        | llm
        | StrOutputParser()
    )

    # 5. Run Query
    if args.query:
        print(f"Query: {args.query}")
        print("-" * 30)
        try:
            response = chain.invoke(args.query)
            print(response)
        except Exception as e:
            print(f"Error generating response: {e}")
    else:
        print("Starting interactive mode. Type 'exit' to quit.")
        while True:
            query = input("\nEnter query: ")
            if query.lower() in ["exit", "quit"]:
                break
            try:
                response = chain.invoke(query)
                print("\n" + response)
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
