from src.backend.rag_engine import RAGService
import os

def test_link_attribution():
    rag = RAGService()
    
    test_queries = [
        {
            "query": "What are the top 5 holdings of HDFC Flexi Cap Fund?",
            "expected_contains": "https://files.hdfcfund.com/s3fs-public/Others/2026-02/Fund%20Facts%20-%20HDFC%20Flexi%20Cap%20Fund_January%2026.pdf"
        },
        {
            "query": "What is the exit load for HDFC Large Cap Fund?",
            "expected_contains": "https://files.hdfcfund.com/s3fs-public/KIM/2025-11/KIM%20-%20HDFC%20Large%20Cap%20Fund%20dated%20November%2021%2C%202025_0.pdf"
        },
        {
            "query": "What is the investment objective of HDFC Tax Saver (ELSS)?",
            "expected_contains": "https://files.hdfcfund.com/s3fs-public/SID/2025-11/SID%20-%20HDFC%20ELSS%20Tax%20Saver%20dated%20November%2021%2C%202025.pdf"
        }
    ]
    
    print("\n--- PDF Link Verification Results ---\n")
    
    for item in test_queries:
        print(f"Query: {item['query']}")
        response = rag.query(item['query'])
        
        found = item['expected_contains'] in response
        if found:
            print(f"PASS: Correct link cited.")
        else:
            print(f"FAIL: Link not found in response.")
            # Print last few lines of response to see what was cited
            print("Citations Found:")
            for line in response.split('\n'):
                if "Source Link:" in line or "https://" in line:
                    print(f"  {line}")
        print("-" * 40)

if __name__ == "__main__":
    test_link_attribution()
