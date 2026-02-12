from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag_engine import RAGService
import uvicorn

app = FastAPI(title="HDFC Mutual Fund RAG API")

# Initialize RAG Service
try:
    rag_service = RAGService()
except Exception as e:
    print(f"Failed to initialize RAG Service: {e}")
    rag_service = None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str

@app.post("/chat", response_model=QueryResponse)
async def chat(request: QueryRequest):
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG Service not available. Check server logs.")
    
    answer = rag_service.query(request.query)
    return QueryResponse(answer=answer)

@app.get("/health")
async def health_check():
    return {"status": "ok", "rag_service": "connected" if rag_service else "disconnected"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
