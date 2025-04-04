"""
Elasticsearch service for product indexing and searching with sentence-transformers embeddings
"""
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from typing import List, Dict
import os
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from urllib.parse import urlparse

load_dotenv()

class ElasticsearchService:
    def __init__(self):
        # Parse and validate Elasticsearch URL
        es_url = os.getenv("ELASTICSEARCH_HOST", "http://elasticsearch:9200")
        parsed_url = urlparse(es_url)
        
        # Ensure we have all required URL components
        if not all([parsed_url.scheme, parsed_url.hostname]):
            es_url = "http://elasticsearch:9200"
            parsed_url = urlparse(es_url)
            
        # Get port, default to 9200 if not specified
        port = parsed_url.port or 9200
        
        # Construct proper URL format
        es_url = f"{parsed_url.scheme}://{parsed_url.hostname}:{port}"
        self.es = Elasticsearch(es_url)
        self.index_name = "products"
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        self.setup_index()

    def setup_index(self):
        """Create index with proper mappings if it doesn't exist"""
        if not self.es.indices.exists(index=self.index_name):
            mappings = {
                "properties": {
                    "name": {"type": "text", "analyzer": "standard"},
                    "description": {"type": "text", "analyzer": "standard"},
                    "specifications": {"type": "object"},
                    "embedding": {"type": "dense_vector", "dims": 768},  # MPNet embeddings are 768-dimensional
                    "category": {"type": "keyword"},
                    "price": {"type": "float"},
                    "stock": {"type": "integer"}
                }
            }
            self.es.indices.create(index=self.index_name, mappings=mappings)

    def _add_embedding(self, product: Dict) -> Dict:
        """Add embedding to product document"""
        text_to_embed = f"{product['name']} {product['description']} {str(product.get('specifications', {}))}"
        product['embedding'] = self.embeddings.embed_query(text_to_embed)
        return product

    def index_product(self, product: Dict):
        """Index a single product"""
        product_with_embedding = self._add_embedding(product)
        self.es.index(index=self.index_name, document=product_with_embedding)

    def bulk_index_products(self, products: List[Dict]):
        """Bulk index multiple products"""
        products_with_embeddings = [self._add_embedding(product) for product in products]
        actions = [
            {
                "_index": self.index_name,
                "_source": product
            }
            for product in products_with_embeddings
        ]
        bulk(self.es, actions)

    def search_products(self, query: str, size: int = 10) -> List[Dict]:
        """Search for products using text query"""
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name^3", "description^2", "specifications.*"],
                    "type": "best_fields",
                    "tie_breaker": 0.3
                }
            },
            "size": size
        }
        
        response = self.es.search(index=self.index_name, body=search_query)
        return [hit["_source"] for hit in response["hits"]["hits"]]

    def vector_search(self, embedding: List[float], size: int = 10) -> List[Dict]:
        """Search for products using vector similarity"""
        search_query = {
            "query": {
                "script_score": {
                    "query": {"match_all": {}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                        "params": {"query_vector": embedding}
                    }
                }
            },
            "size": size
        }
        
        response = self.es.search(index=self.index_name, body=search_query)
        return [hit["_source"] for hit in response["hits"]["hits"]]
