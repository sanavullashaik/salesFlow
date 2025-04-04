"""
FastAPI endpoints for the product search application
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
from ..services.email_processor import EmailProcessor, ProductRequest
from ..services.elasticsearch_service import ElasticsearchService
from ..services.product_matcher import ProductMatcher
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Service instances with retry logic
def initialize_services():
    retries = 5
    retry_delay = 5  # seconds
    
    for _ in range(retries):
        try:
            logger.info("Initializing services...")
            email_processor = EmailProcessor()
            es_service = ElasticsearchService()
            product_matcher = ProductMatcher()
            logger.info("Services initialized successfully")
            return email_processor, es_service, product_matcher
        except Exception as e:
            logger.error(f"Error initializing services: {str(e)}")
            if _ < retries - 1:  # don't sleep on the last attempt
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    raise Exception("Failed to initialize services after multiple attempts")

email_processor, es_service, product_matcher = initialize_services()

@router.get("/emails/check")
async def check_emails() -> Dict:
    """Check for new product request emails"""
    try:
        logger.info("Checking for new emails...")
        new_emails = email_processor.fetch_new_emails()
        processed_requests = []
        
        for email in new_emails:
            product_request = email_processor.extract_product_request(email["content"])
            processed_requests.append(product_request)
        
        logger.info(f"Successfully processed {len(new_emails)} emails")
        return {
            "status": "success",
            "new_emails": len(new_emails),
            "processed_requests": [req.dict() for req in processed_requests]
        }
    except Exception as e:
        logger.error(f"Error checking emails: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/products")
async def index_product(product: Dict):
    """Index a new product"""
    try:
        logger.info("Indexing product...")
        es_service.index_product(product)
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
        es_service.bulk_index_products(products)
        logger.info("Products indexed successfully")
        return {"status": "success", "message": f"{len(products)} products indexed successfully"}
    except Exception as e:
        logger.error(f"Error bulk indexing products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_products(q: str, size: int = 10):
    """Search for products using text query"""
    try:
        logger.info(f"Searching for products with query: {q}")
        results = es_service.search_products(q, size)
        logger.info(f"Found {len(results)} matching products")
        return {"status": "success", "results": results}
    except Exception as e:
        logger.error(f"Error searching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/match")
async def match_products(request: ProductRequest, top_k: int = 5):
    """Match products using RAG"""
    try:
        logger.info("Matching products for request...")
        matches = product_matcher.match_products(request, es_service, top_k)
        logger.info(f"Found {len(matches)} matching products")
        return {"status": "success", "matches": matches}
    except Exception as e:
        logger.error(f"Error matching products: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
