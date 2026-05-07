from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import os
import tempfile
import shutil

from src.input.codebase_loader import CodebaseLoader
from src.graph.tigergraph_client import TigerGraphClient
from src.graph.sqlite_fallback import SQLiteGraph
from src.router.cache import PredictiveCache
from src.router.budget_controller import BudgetController
from src.router.adaptive_learning import AdaptiveLearning

app = FastAPI(title="GraphMind Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

loader = CodebaseLoader()
tg_client = TigerGraphClient()
fallback_graph = SQLiteGraph()
cache = PredictiveCache()
budget_ctrl = BudgetController()
learning = AdaptiveLearning()

class IngestRequest(BaseModel):
    codebase_id: str

class QueryRequest(BaseModel):
    query: str
    codebase_id: str

class BudgetRequest(BaseModel):
    budget: int

class CloneRequest(BaseModel):
    url: str

query_history = []

@app.post("/api/ingest")
async def ingest_codebase(request: IngestRequest):
    cache.invalidate_all()
    return {
        "status": "success",
        "nodes_created": 1200,
        "edges_created": 3400
    }

@app.post("/api/query")
async def query_codebase(request: QueryRequest):
    start_time = time.time()
    
    cached_result = cache.get(request.query)
    if cached_result:
        query_history.insert(0, cached_result)
        return cached_result
        
    forced_tier = budget_ctrl.get_forced_tier()
    preferred_tier = learning.get_preferred_tier(request.query)
    
    tier = forced_tier or preferred_tier or "GRAPH_RAG"
    
    # Simple simulated logic based on query words
    q = request.query.lower()
    if 'fact' in q or 'what does' in q and len(q.split()) < 6:
        tier = "GRAPH_ONLY"
    elif 'open-ended' in q or 'summarize' in q:
        tier = "LLM_FULL"
        
    if forced_tier:
        tier = forced_tier
    
    time.sleep(0.5)
    
    if tier == "GRAPH_ONLY":
        tokens_used = 150
    elif tier == "GRAPH_RAG":
        tokens_used = 850
    else:
        tokens_used = 4000
        
    estimated_full_tokens = 4000
    
    budget_ctrl.add_usage(tokens_used, estimated_full_tokens)
    
    response_time = time.time() - start_time
    answer = f"Generated answer for '{request.query}' using {tier}."
    
    result = {
        "answer": answer,
        "tier": tier,
        "tokens_used": tokens_used,
        "response_time": round(response_time, 2),
        "savings": round(1.0 - (tokens_used / estimated_full_tokens), 2) if estimated_full_tokens else 0,
        "reasoning": f"Routed via {tier} based on engine rules."
    }
    
    cache.set(request.query, result["answer"], result["tier"], result["tokens_used"], result["response_time"])
    
    history_entry = {**result, "query": request.query, "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
    query_history.insert(0, history_entry)
    
    learning.log_query(request.query, tier, 0.9)
    
    return result

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/metrics")
async def get_metrics():
    status = budget_ctrl.get_status()
    return {
        "total_tokens": status["budget_used"],
        "total_cost": status["dollar_cost"],
        "savings_percentage": status["savings_percentage"],
        "queries_count": len(query_history)
    }

@app.get("/api/graph")
async def get_graph():
    return {
        "nodes": [
            { "data": { "id": "func1", "label": "authenticate", "type": "function" } },
            { "data": { "id": "func2", "label": "validate_token", "type": "function" } }
        ],
        "edges": [
            { "data": { "source": "func1", "target": "func2", "type": "calls" } }
        ]
    }

@app.get("/api/query-history")
async def get_query_history():
    return query_history[:10]

@app.post("/api/budget")
async def set_budget(request: BudgetRequest):
    budget_ctrl.set_budget(request.budget)
    status = budget_ctrl.get_status()
    return {
        "budget_limit": status["budget_limit"],
        "budget_used": status["budget_used"],
        "budget_remaining": status["budget_remaining"]
    }

@app.post("/api/upload")
async def upload_zip(file: UploadFile = File(...)):
    if not file.filename.endswith('.zip'):
        return {"status": "error", "message": "Only ZIP files are allowed"}
        
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name
        
    result = loader.load_from_zip(tmp_path)
    os.unlink(tmp_path)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
        
    return {
        "status": "success",
        "file_count": result.get("file_count", 0),
        "languages": result.get("languages", []),
        "codebase_id": "zip_" + str(int(time.time()))
    }

@app.post("/api/clone")
async def clone_repo(request: CloneRequest):
    result = loader.load_from_git(request.url)
    
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("message"))
        
    return {
        "status": "success",
        "repo_name": result.get("repo_name", "unknown"),
        "file_count": result.get("file_count", 0),
        "codebase_id": "git_" + str(int(time.time()))
    }

@app.get("/api/learning/stats")
async def learning_stats():
    return learning.get_stats()
