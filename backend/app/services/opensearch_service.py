"""
OpenSearch service for product indexing and searching with keyword-based search
"""
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from typing import List, Dict
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

class OpenSearchService:
    def __init__(self):
        # Parse and validate OpenSearch URL
        os_url = os.getenv("OPENSEARCH_HOST", "http://opensearch:9200")
        parsed_url = urlparse(os_url)
        
        # Ensure we have all required URL components
        if not all([parsed_url.scheme, parsed_url.hostname]):
            os_url = "http://opensearch:9200"
            parsed_url = urlparse(os_url)
            
        # Get port, default to 9200 if not specified
        port = parsed_url.port or 9200
        
        # Construct proper URL format
        os_url = f"{parsed_url.scheme}://{parsed_url.hostname}:{port}"
        self.client = OpenSearch(
            hosts=[os_url],
            use_ssl=False,
            verify_certs=False,
            connection_class=None,
            timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
        self.index_name = "products"
        self._index_created = False

    def setup_index(self):
        """Create index with proper mappings including autocomplete features"""
        if self._index_created:
            return
            
        try:
            if not self.client.indices.exists(index=self.index_name):
                # Define custom analyzers for autocomplete and search-as-you-type
                index_settings = {
                    "settings": {
                        "analysis": {
                            "tokenizer": {
                                "autocomplete_tokenizer": {
                                    "type": "edge_ngram",
                                    "min_gram": 1,
                                    "max_gram": 20,
                                    "token_chars": ["letter", "digit"]
                                }
                            },
                            "analyzer": {
                                "autocomplete_index": {
                                    "type": "custom",
                                    "tokenizer": "autocomplete_tokenizer",
                                    "filter": ["lowercase"]
                                },
                                "autocomplete_search": {
                                    "type": "custom",
                                    "tokenizer": "standard",
                                    "filter": ["lowercase"]
                                },
                                "search_as_you_type_analyzer": {
                                    "type": "custom",
                                    "tokenizer": "standard",
                                    "filter": ["lowercase", "stop", "snowball"]
                                }
                            }
                        }
                    },
                    "mappings": {
                        "properties": {
                            "name": {
                                "type": "search_as_you_type",
                                "analyzer": "search_as_you_type_analyzer",
                                "fields": {
                                    "standard": {
                                        "type": "text",
                                        "analyzer": "standard"
                                    },
                                    "autocomplete": {
                                        "type": "text",
                                        "analyzer": "autocomplete_index",
                                        "search_analyzer": "autocomplete_search"
                                    }
                                }
                            },
                            "name_suggest": {
                                "type": "completion",
                                "analyzer": "simple",
                                "preserve_separators": True,
                                "preserve_position_increments": True,
                                "max_input_length": 50
                            },
                            "description": {
                                "type": "search_as_you_type",
                                "analyzer": "search_as_you_type_analyzer",
                                "fields": {
                                    "standard": {
                                        "type": "text",
                                        "analyzer": "standard"
                                    },
                                    "autocomplete": {
                                        "type": "text",
                                        "analyzer": "autocomplete_index",
                                        "search_analyzer": "autocomplete_search"
                                    }
                                }
                            },
                            "category": {
                                "type": "keyword"
                            },
                            "category_suggest": {
                                "type": "completion",
                                "analyzer": "simple"
                            },
                            "specifications": {"type": "object"},
                            "price": {"type": "float"},
                            "stock": {"type": "integer"},
                            "image_url": {
                                "type": "keyword",
                                "index": False
                            },
                            "brand": {
                                "type": "keyword"
                            },
                            "rating": {"type": "float"},
                            "reviews_count": {"type": "integer"}
                        }
                    }
                }
                self.client.indices.create(index=self.index_name, body=index_settings)
            self._index_created = True
        except Exception as e:
            raise Exception(f"Failed to setup OpenSearch index: {str(e)}")

    def _prepare_product_for_indexing(self, product: Dict) -> Dict:
        """Prepare product document with suggest fields for autocomplete"""
        product_doc = product.copy()
        
        # Add suggest data for name field
        if 'name' in product_doc:
            name_value = product_doc['name']
            # Split name into words for better suggestions
            name_words = name_value.split()
            suggest_inputs = [name_value] + name_words
            
            # Keep original name and add suggest field
            product_doc['name'] = name_value
            if 'name' not in product_doc:
                product_doc['name'] = {}
            product_doc['name_suggest'] = {
                "input": suggest_inputs,
                "weight": 10
            }
        
        # Add suggest data for category field
        if 'category' in product_doc:
            category_value = product_doc['category']
            product_doc['category_suggest'] = {
                "input": [category_value],
                "weight": 5
            }
        
        return product_doc

    def index_product(self, product: Dict):
        """Index a single product with autocomplete suggest fields"""
        self.setup_index()
        product_doc = self._prepare_product_for_indexing(product)
        self.client.index(index=self.index_name, body=product_doc)

    def bulk_index_products(self, products: List[Dict]):
        """Bulk index multiple products with autocomplete suggest fields"""
        self.setup_index()
        actions = [
            {
                "_index": self.index_name,
                "_source": self._prepare_product_for_indexing(product)
            }
            for product in products
        ]
        bulk(self.client, actions)

    def search_products(self, query: str, size: int = 10) -> List[Dict]:
        """Search for products using search-as-you-type and multi-match queries"""
        self.setup_index()
        search_query = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "type": "bool_prefix",
                                "fields": [
                                    "name",
                                    "name._2gram",
                                    "name._3gram"
                                ],
                                "boost": 3
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "type": "bool_prefix",
                                "fields": [
                                    "description",
                                    "description._2gram",
                                    "description._3gram"
                                ],
                                "boost": 2
                            }
                        },
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name.standard^4", "description.standard^2", "brand^2", "category^1"],
                                "type": "best_fields",
                                "tie_breaker": 0.3
                            }
                        },
                        {
                            "match": {
                                "name.autocomplete": {
                                    "query": query,
                                    "boost": 2
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "size": size
        }
        
        response = self.client.search(index=self.index_name, body=search_query)
        return [hit["_source"] for hit in response["hits"]["hits"]]

    def instant_search_products(self, query: str, size: int = 10) -> List[Dict]:
        """Ultra-fast search optimized for instant results (millisecond response)"""
        self.setup_index()
        
        # Simplified, lightning-fast query for instant search
        search_query = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "match_phrase_prefix": {
                                "name": {
                                    "query": query,
                                    "max_expansions": 5  # Limit expansions for speed
                                }
                            }
                        },
                        {
                            "match": {
                                "name": {
                                    "query": query,
                                    "boost": 2
                                }
                            }
                        },
                        {
                            "match": {
                                "brand": {
                                    "query": query,
                                    "boost": 1.5
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "_source": ["name", "brand", "category", "price", "stock", "rating", "reviews_count", "image_url", "description"],  # Only essential fields
            "size": size,
            "timeout": "50ms"  # Ultra-fast timeout
        }
        
        try:
            response = self.client.search(index=self.index_name, body=search_query)
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception:
            # If fast search fails, fallback to basic match
            fallback_query = {
                "query": {
                    "match": {
                        "name": query
                    }
                },
                "_source": ["name", "brand", "category", "price", "stock", "rating", "reviews_count", "image_url"],
                "size": size,
                "timeout": "20ms"
            }
            response = self.client.search(index=self.index_name, body=fallback_query)
            return [hit["_source"] for hit in response["hits"]["hits"]]

    def autocomplete_suggestions(self, query: str, size: int = 5) -> List[Dict]:
        """Get autocomplete suggestions using OpenSearch completion suggester"""
        self.setup_index()
        
        # Simplified ultra-fast autocomplete query
        suggest_query = {
            "suggest": {
                "product_suggestions": {
                    "prefix": query,
                    "completion": {
                        "field": "name_suggest",
                        "size": size,
                        "skip_duplicates": True
                    }
                }
            },
            # Simple match for instant results
            "query": {
                "match_phrase_prefix": {
                    "name": {
                        "query": query,
                        "max_expansions": 3  # Limit for speed
                    }
                }
            },
            "_source": ["name", "category", "brand"],
            "size": 3,
            "timeout": "30ms"  # Ultra-fast timeout
        }
        
        response = self.client.search(index=self.index_name, body=suggest_query)
        
        suggestions = []
        
        # Fast processing - prioritize completion suggestions
        if "suggest" in response and "product_suggestions" in response["suggest"]:
            for option in response["suggest"]["product_suggestions"]:
                for suggestion in option["options"][:size]:
                    suggestions.append({
                        "text": suggestion["text"],
                        "type": "product",
                        "score": suggestion.get("_score", 100)
                    })
        
        # Add search results only if we need more suggestions
        if len(suggestions) < size and "hits" in response and response["hits"]["hits"]:
            for hit in response["hits"]["hits"]:
                if len(suggestions) >= size:
                    break
                source = hit["_source"]
                name = source.get("name", "")
                if name and name.lower().startswith(query.lower()):
                    suggestions.append({
                        "text": name,
                        "type": "search_result",
                        "score": hit.get("_score", 50)
                    })
        
        # Quick deduplication and return
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            text_lower = suggestion["text"].lower()
            if text_lower not in seen:
                seen.add(text_lower)
                unique_suggestions.append(suggestion)
                if len(unique_suggestions) >= size:
                    break
        
        return unique_suggestions

    def recreate_index(self):
        """Recreate the index with new mappings (useful for schema changes)"""
        try:
            # Delete the index if it exists
            if self.client.indices.exists(index=self.index_name):
                self.client.indices.delete(index=self.index_name)
            
            # Reset the flag to force recreation
            self._index_created = False
            
            # Recreate the index
            self.setup_index()
            
            return True
        except Exception as e:
            raise Exception(f"Failed to recreate index: {str(e)}")