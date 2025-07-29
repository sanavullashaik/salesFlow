"""
GROQ-based product matching and reranking service
"""
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

load_dotenv()

class GroqProductMatcher:
    def __init__(self):
        # Initialize Groq LLM with latest fast model
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.1-8b-instant",  # Latest fast model optimized for speed
            temperature=0.1,  # Lower temperature for consistent, fast results
            max_tokens=10    # Limit tokens for faster response - we only need a number
        )
        
        self.reranking_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product matching expert. Analyze the search query and candidate product 
             to determine their relevance score from 0-100. Consider product name, description, specifications, 
             category, and how well they match the search intent.
             
             Scoring guidelines:
             - 90-100: Perfect match (exact product or very close variant)
             - 70-89: Good match (same category, similar features)
             - 50-69: Moderate match (related but different product)
             - 30-49: Weak match (some relevance but not ideal)
             - 0-29: Poor match (little to no relevance)
             
             Output only the numeric score (0-100)."""),
            ("human", "Search Query: {query}\nCandidate Product: {product}")
        ])

    def rerank_search_results(self, query: str, products: List[Dict], top_k: int = 10, use_groq: bool = False) -> List[Dict]:
        """
        Rerank search results using GROQ LLM based on relevance to query
        If use_groq is False, returns results with simple scoring based on OpenSearch scores
        """
        if not products:
            return []
        
        # If GROQ reranking is disabled, use simple scoring
        if not use_groq:
            scored_products = []
            for i, product in enumerate(products):
                product_with_score = product.copy()
                # Use position-based scoring (first results get higher scores)
                product_with_score['relevance_score'] = max(100 - (i * 5), 10)
                scored_products.append(product_with_score)
            return scored_products[:top_k]
        
        scored_products = []
        
        for i, product in enumerate(products):
            try:
                # Create concise product string for analysis
                product_str = f"Name: {product.get('name', 'N/A')[:100]}\n"  # Limit length
                product_str += f"Category: {product.get('category', 'N/A')}\n"
                product_str += f"Brand: {product.get('brand', 'N/A')}"
                
                # Limit query length to avoid API errors
                limited_query = query[:100] if len(query) > 100 else query
                
                # Get relevance score from GROQ with error handling
                try:
                    response = self.llm.invoke(
                        self.reranking_prompt.format_messages(
                            query=limited_query,
                            product=product_str
                        )
                    )
                    
                    # Extract numeric score
                    score_text = response.content.strip()
                    score = float(score_text)
                    score = max(0, min(100, score))  # Clamp between 0-100
                    
                except Exception as groq_error:
                    # If GROQ fails, use position-based scoring
                    score = max(100 - (i * 5), 10)
                
                product_with_score = product.copy()
                product_with_score['relevance_score'] = score
                scored_products.append(product_with_score)
                
            except Exception as e:
                # If all fails, assign position-based score
                product_with_score = product.copy()
                product_with_score['relevance_score'] = max(100 - (i * 5), 10)
                scored_products.append(product_with_score)
        
        # Sort by relevance score (descending)
        scored_products.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Return top_k results
        return scored_products[:top_k]

    def get_product_suggestions(self, query: str, products: List[Dict], max_suggestions: int = 5) -> List[str]:
        """
        Get product name suggestions based on query similarity
        """
        if not products:
            return []
        
        # Simple keyword matching for suggestions
        query_lower = query.lower()
        suggestions = []
        
        for product in products:
            product_name = product.get('name', '').lower()
            if query_lower in product_name and product_name not in suggestions:
                suggestions.append(product.get('name', ''))
            
            if len(suggestions) >= max_suggestions:
                break
        
        return suggestions