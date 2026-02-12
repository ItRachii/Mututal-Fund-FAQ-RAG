from rag_engine import RAGService
import json

def test_query():
    rag = RAGService()
    query = "What is the exit load for HDFC Top 100?"
    
    # Manually get docs to see what's being retrieved
    docs = rag.retriever.invoke(query)
    print("\n--- RETRIEVED CONTEXT ---")
    for i, doc in enumerate(docs):
        print(f"Doc {i+1}: {doc.metadata.get('source', 'Unknown')}")
        # Use ascii for safety in console or just replace known issues
        content = doc.page_content[:500].replace('\u25cf', '*')
        print(f"Content: {content}")
        print("-" * 20)
    
    # Get full response
    response = rag.query(query)
    print("\n--- ASSISTANT RESPONSE ---")
    print(response)

if __name__ == "__main__":
    test_query()
