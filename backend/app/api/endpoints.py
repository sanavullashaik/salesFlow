"""
FastAPI endpoints for the product search application
"""
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from typing import List, Dict
from ..services.image_processor import ImageProcessor, ProductInfo
from ..services.opensearch_service import OpenSearchService
from ..services.groq_product_matcher import GroqProductMatcher
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy service initialization
_services = {}

def get_services():
    """Get services with lazy initialization"""
    if not _services:
        try:
            logger.info("Initializing services...")
            _services['image_processor'] = ImageProcessor()
            _services['opensearch_service'] = OpenSearchService()
            _services['product_matcher'] = GroqProductMatcher()
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            raise HTTPException(status_code=503, detail=f"Service initialization failed: {str(e)}")
    
    return _services['image_processor'], _services['opensearch_service'], _services['product_matcher']

@router.post("/images/process")
async def process_image(file: UploadFile = File(...)) -> Dict:
    """Process an uploaded image to extract product information"""
    try:
        logger.info("Processing uploaded image...")
        image_processor, _, _ = get_services()
        
        # Read file content
        file_content = await file.read()
        import io
        
        # Convert to file-like object
        image_file = io.BytesIO(file_content)
        products = image_processor.extract_products_from_image(image_file)
        
        logger.info(f"Successfully extracted {len(products)} products from image")
        return {
            "status": "success",
            "products_found": len(products),
            "extracted_products": products
        }
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/products")
async def index_product(product: Dict):
    """Index a new product"""
    try:
        logger.info("Indexing product...")
        _, opensearch_service, _ = get_services()
        opensearch_service.index_product(product)
        logger.info("Product indexed successfully")
        return {"status": "success", "message": "Product indexed successfully"}
    except Exception as e:
        logger.error(f"Error indexing product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/products/bulk")
async def bulk_index_products(products: List[Dict]):
    """Bulk index products"""
    try:
        logger.info(f"Bulk indexing {len(products)} products...")
        _, opensearch_service, _ = get_services()
        opensearch_service.bulk_index_products(products)
        logger.info("Products indexed successfully")
        return {"status": "success", "message": f"{len(products)} products indexed successfully"}
    except Exception as e:
        logger.error(f"Error bulk indexing products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_products(q: str, size: int = 10, use_groq_rerank: bool = False):
    """Search for products using text query"""
    try:
        logger.info(f"Searching for products with query: {q}")
        _, opensearch_service, product_matcher = get_services()
        
        # Get results from OpenSearch (get more if reranking is enabled)
        search_size = size * 2 if use_groq_rerank else size
        initial_results = opensearch_service.search_products(q, search_size)
        
        # Rerank results (with or without GROQ)
        reranked_results = product_matcher.rerank_search_results(q, initial_results, size, use_groq_rerank)
        
        rerank_type = "GROQ-reranked" if use_groq_rerank else "OpenSearch-scored"
        logger.info(f"Found {len(reranked_results)} {rerank_type} matching products")
        return {"status": "success", "results": reranked_results}
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instant-search")
async def instant_search_products(q: str, size: int = 10):
    """Ultra-fast instant search optimized for millisecond responses"""
    try:
        logger.info(f"Instant searching for products with query: {q}")
        _, opensearch_service, _ = get_services()
        
        # Use the ultra-fast search method
        results = opensearch_service.instant_search_products(q, size)
        
        # Add simple position-based scoring for instant results
        for i, result in enumerate(results):
            result['relevance_score'] = max(100 - (i * 3), 10)
        
        logger.info(f"Found {len(results)} instant search results")
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Error in instant search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/autocomplete")
async def autocomplete_products(q: str, size: int = 5):
    """Get autocomplete suggestions for product search"""
    try:
        logger.info(f"Getting autocomplete suggestions for: {q}")
        _, opensearch_service, _ = get_services()
        suggestions = opensearch_service.autocomplete_suggestions(q, size)
        logger.info(f"Found {len(suggestions)} suggestions")
        return {"status": "success", "suggestions": suggestions}
    except Exception as e:
        logger.error(f"Error getting autocomplete suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/data/load-sample")
async def load_sample_data():
    """Load sample product data from JSON file"""
    try:
        logger.info("Loading sample product data...")
        _, opensearch_service, _ = get_services()
        
        # Recreate index to ensure proper mappings for autocomplete
        logger.info("Recreating index with autocomplete mappings...")
        opensearch_service.recreate_index()
        
        # Load sample data from file
        import json
        import os
        
        # Get the absolute path to the sample data file
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sample_file_path = os.path.join(current_dir, "data", "sample_products.json")
        
        with open(sample_file_path, 'r') as file:
            sample_products = json.load(file)
        
        # Index all sample products with autocomplete fields
        opensearch_service.bulk_index_products(sample_products)
        
        logger.info(f"Successfully loaded {len(sample_products)} sample products with autocomplete")
        return {
            "status": "success", 
            "message": f"Successfully loaded {len(sample_products)} sample products with autocomplete features",
            "products_loaded": len(sample_products)
        }
    except Exception as e:
        logger.error(f"Error loading sample data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index/recreate")
async def recreate_index():
    """Recreate the OpenSearch index with new mappings"""
    try:
        logger.info("Recreating OpenSearch index...")
        _, opensearch_service, _ = get_services()
        
        opensearch_service.recreate_index()
        
        logger.info("Index recreated successfully")
        return {
            "status": "success", 
            "message": "Index recreated successfully with new mappings"
        }
    except Exception as e:
        logger.error(f"Error recreating index: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
