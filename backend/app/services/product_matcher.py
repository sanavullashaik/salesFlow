"""
RAG-based product matching service using LangChain, LangGraph, and open-source models
"""
from typing import List, Dict, Any
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langgraph.graph import Graph
import operator
from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class ProductMatcher:
    def __init__(self):
        # Initialize Groq LLM
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="mixtral-8x7b-32768"
        )
        
        # Initialize sentence-transformers embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2"
        )
        
        self.reranking_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product matching expert. Analyze the product request and candidate product 
             to determine their compatibility score from 0-100. Consider all specifications and requirements.
             Output only the numeric score."""),
            ("human", "Product Request: {request}\nCandidate Product: {product}")
        ])
        
        # Define graph nodes
        self.workflow = self.create_workflow()

    def create_workflow(self) -> Graph:
        """Create the LangGraph workflow for product matching"""
        
        def generate_embeddings(state):
            """Generate embeddings for the product request"""
            request_text = (f"{state['request'].product_name} "
                          f"{state['request'].description} "
                          f"{str(state['request'].specifications)}")
            state["embedding"] = self.embeddings.embed_query(request_text)
            return state
        
        def semantic_search(state):
            """Perform semantic search using embeddings"""
            state["candidates"] = state["es_service"].vector_search(
                state["embedding"],
                size=state["top_k"]
            )
            return state
        
        def rerank_candidates(state):
            """Rerank candidates using LLM"""
            scores = []
            request_str = str(state["request"].dict())
            
            for product in state["candidates"]:
                response = self.llm.invoke(
                    self.reranking_prompt.format_messages(
                        request=request_str,
                        product=str(product)
                    )
                )
                scores.append(float(response.content.strip()))
            
            # Sort candidates by score
            ranked_candidates = [
                x for _, x in sorted(
                    zip(scores, state["candidates"]),
                    key=operator.itemgetter(0),
                    reverse=True
                )
            ]
            
            state["ranked_candidates"] = ranked_candidates
            return state

        # Create the graph
        workflow = Graph()
        
        # Add nodes
        workflow.add_node("generate_embeddings", generate_embeddings)
        workflow.add_node("semantic_search", semantic_search)
        workflow.add_node("rerank_candidates", rerank_candidates)
        
        # Add edges
        workflow.add_edge("generate_embeddings", "semantic_search")
        workflow.add_edge("semantic_search", "rerank_candidates")
        
        # Set entry point
        workflow.set_entry_point("generate_embeddings")
        
        # Return the final node as the end state
        workflow.end_state = "rerank_candidates"
        
        return workflow.compile()

    def match_products(self, product_request: Any, es_service, top_k: int = 5) -> List[Dict]:
        """
        Match products using the RAG workflow
        """
        # Initialize state
        initial_state = {
            "request": product_request,
            "es_service": es_service,
            "top_k": top_k
        }
        
        # Run the workflow
        final_state = self.workflow.invoke(initial_state)
        
        return final_state["ranked_candidates"]
