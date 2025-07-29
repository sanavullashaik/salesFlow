"""
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import endpoints
import uvicorn

app = FastAPI(title="Product Search API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(endpoints.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "message": "Product Search API",
        "endpoints": {
            "Process Image": "/api/images/process",
            "Index Product": "/api/products",
            "Bulk Index": "/api/products/bulk",
            "Search": "/api/search",
            "Instant Search": "/api/instant-search",
            "Autocomplete": "/api/autocomplete",
            "Load Sample Data": "/api/data/load-sample",
            "Recreate Index": "/api/index/recreate"
        }
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
