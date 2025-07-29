"""
Streamlit frontend application for Product Search with Image Processing
"""
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import os
import time
from functools import lru_cache

# Set the backend URL based on environment
BACKEND_URL = os.getenv('BACKEND_URL', 'http://backend:8000')

# Cache for search results and suggestions to avoid repeated API calls
@st.cache_data(ttl=60)  # Cache for 60 seconds
def cached_search(query, size=10, use_groq=False):
    """Cached search function to avoid repeated API calls"""
    try:
        params = {"q": query, "size": size}
        if use_groq:
            params["use_groq_rerank"] = "true"
            
        response = requests.get(
            f"{BACKEND_URL}/api/search",
            params=params,
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
    except:
        return []
    return []

@st.cache_data(ttl=30)  # Cache for 30 seconds
def cached_instant_search(query, size=10):
    """Ultra-fast cached instant search"""
    if len(query) < 1:
        return []
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/instant-search",
            params={"q": query, "size": size},
            timeout=1  # Ultra-fast timeout for instant search
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('results', [])
    except:
        return []
    return []

@st.cache_data(ttl=30)  # Cache for 30 seconds
def cached_autocomplete(query):
    """Cached autocomplete function"""
    if len(query) < 1:
        return []
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/api/autocomplete",
            params={"q": query, "size": 8},
            timeout=2  # Very fast timeout for autocomplete
        )
        if response.status_code == 200:
            data = response.json()
            return data.get('suggestions', [])
    except:
        pass
    return []

st.set_page_config(
    page_title="Product Search Dashboard",
    page_icon="🔍",
    layout="wide"
)

def get_autocomplete_suggestions(query):
    """Get autocomplete suggestions from backend (cached)"""
    return cached_autocomplete(query)

def instant_search(query, size=10, use_groq=False):
    """Perform instant search - ultra-fast by default, GROQ reranking when enabled"""
    if use_groq:
        # Use regular search with GROQ reranking (slower but more accurate)
        return cached_search(query, size, use_groq)
    else:
        # Use ultra-fast instant search (millisecond response)
        return cached_instant_search(query, size)

def main():
    st.title("🔍 Product Search Dashboard")
    
    # Sidebar for configuration
    st.sidebar.title("Settings")
    api_url = st.sidebar.text_input("API URL", value=BACKEND_URL)
    
    # Main content
    tabs = st.tabs(["🖼️ Image Processing", "🔍 Search Products", "📦 Product Management"])
    
    with tabs[0]:
        st.header("Image Processing")
        st.info("Upload product images to extract information automatically using AI")
        
        # Image upload section
        uploaded_file = st.file_uploader(
            "Upload Product Image", 
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
            help="Upload an image of a product to extract information"
        )
        
        if uploaded_file is not None:
            # Display the uploaded image
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
            
            with col2:
                if st.button("🤖 Process Image", type="primary"):
                    with st.spinner("Processing image with AI..."):
                        try:
                            # Send image to backend for processing
                            files = {"file": uploaded_file.getvalue()}
                            response = requests.post(
                                f"{api_url}/api/images/process",
                                files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                st.success(f"✅ Found {data['products_found']} product(s)")
                                
                                # Display extracted products
                                for i, product in enumerate(data['extracted_products']):
                                    st.subheader(f"Product {i+1}")
                                    
                                    # Create columns for product info
                                    info_col1, info_col2 = st.columns(2)
                                    
                                    with info_col1:
                                        st.write(f"**Name:** {product.get('product_name', 'N/A')}")
                                        st.write(f"**Category:** {product.get('category', 'N/A')}")
                                        st.write(f"**Price Range:** {product.get('estimated_price_range', 'N/A')}")
                                    
                                    with info_col2:
                                        st.write(f"**Description:** {product.get('description', 'N/A')}")
                                        if product.get('specifications'):
                                            st.write("**Specifications:**")
                                            for key, value in product['specifications'].items():
                                                st.write(f"- {key}: {value}")
                                    
                                    # Option to index the product
                                    if st.button(f"📥 Index Product {i+1}", key=f"index_{i}"):
                                        index_response = requests.post(
                                            f"{api_url}/api/products",
                                            json=product,
                                            timeout=10
                                        )
                                        if index_response.status_code == 200:
                                            st.success("Product indexed successfully!")
                                        else:
                                            st.error("Failed to index product")
                            else:
                                st.error(f"Error processing image: {response.status_code}")
                        except Exception as e:
                            st.error(f"Error processing image: {str(e)}")
    
    with tabs[1]:
        st.header("Search Products")
        st.info("Search for products with autocomplete and instant results")
        
        # Search interface with autocomplete
        search_col1, search_col2 = st.columns([3, 1])
        
        with search_col1:
            # Create a container for the search box and suggestions
            search_container = st.container()
            
            with search_container:
                # Search input with session state
                if 'search_query' not in st.session_state:
                    st.session_state.search_query = ""
                
                query = st.text_input(
                    "🔍 Search Products", 
                    value=st.session_state.search_query,
                    placeholder="Start typing to see suggestions...",
                    key="search_input"
                )
                
                # Show autocomplete suggestions in rows with real-time updates  
                if query and len(query) >= 1:
                    suggestions = get_autocomplete_suggestions(query)
                    if suggestions:
                        st.write("**💡 Quick Suggestions:**")
                        
                        # Group suggestions by type
                        product_suggestions = [s for s in suggestions if s.get('type') == 'product']
                        category_suggestions = [s for s in suggestions if s.get('type') == 'category']
                        search_suggestions = [s for s in suggestions if s.get('type') == 'search_result']
                        
                        # Combine and limit suggestions
                        all_suggestions = []
                        all_suggestions.extend(product_suggestions[:3])
                        all_suggestions.extend(category_suggestions[:2])
                        all_suggestions.extend(search_suggestions[:3])
                        
                        # Display suggestions in rows of 3
                        for i in range(0, min(len(all_suggestions), 6), 3):
                            cols = st.columns(3)
                            for j, col in enumerate(cols):
                                if i + j < len(all_suggestions):
                                    suggestion = all_suggestions[i + j]
                                    suggestion_text = suggestion.get('text', suggestion) if isinstance(suggestion, dict) else suggestion
                                    suggestion_type = suggestion.get('type', 'product') if isinstance(suggestion, dict) else 'product'
                                    
                                    # Choose icon based on type
                                    icon = "🛍️" if suggestion_type == 'product' else ("📂" if suggestion_type == 'category' else "🔍")
                                    
                                    # Truncate long suggestion text
                                    display_text = suggestion_text if len(suggestion_text) <= 20 else suggestion_text[:20] + "..."
                                    
                                    with col:
                                        if st.button(f"{icon} {display_text}", 
                                                   key=f"suggest_{i}_{j}", 
                                                   help=suggestion_text,
                                                   use_container_width=True):
                                            st.session_state.search_query = suggestion_text
                                            st.rerun()
        
        with search_col2:
            size = st.slider("Results", min_value=1, max_value=50, value=10)
            instant_search_enabled = st.checkbox("⚡ Instant Search", value=True)
            use_groq_rerank = st.checkbox("🧠 GROQ Reranking", value=False, help="Enable AI-powered result reranking (slower but more accurate)")
        
        # Perform search
        search_results = []
        if query:
            if instant_search_enabled:
                # Instant search as user types (no spinner to avoid UI blocking)
                search_results = instant_search(query, size, use_groq_rerank)
            else:
                # Manual search button
                if st.button("🔍 Search", type="primary"):
                    with st.spinner("Searching..."):
                        search_results = instant_search(query, size, use_groq_rerank)
        
        # Display search results as cards
        if search_results:
            rerank_info = " (AI-ranked)" if use_groq_rerank else " (OpenSearch-ranked)"
            st.write(f"**Found {len(search_results)} results{rerank_info}:**")
            
            # Display results in a grid layout (2 cards per row)
            for i in range(0, len(search_results), 2):
                cols = st.columns(2)
                
                for j, col in enumerate(cols):
                    if i + j < len(search_results):
                        result = search_results[i + j]
                        
                        with col:
                            # Create a card-like container
                            with st.container():
                                # Product image
                                if result.get('image_url'):
                                    try:
                                        st.image(result['image_url'], width=150)
                                    except:
                                        st.write("📷 Image not available")
                                else:
                                    st.write("📷 No image")
                                
                                # Product name and brand
                                st.subheader(result.get('name', 'Unknown Product'))
                                
                                # Brand and category
                                brand_category = []
                                if result.get('brand'):
                                    brand_category.append(f"**{result['brand']}**")
                                if result.get('category'):
                                    brand_category.append(result['category'].title())
                                st.write(" • ".join(brand_category))
                                
                                # Rating and reviews
                                if result.get('rating') and result.get('reviews_count'):
                                    stars = "⭐" * int(result['rating'])
                                    st.write(f"{stars} {result['rating']}/5 ({result['reviews_count']:,} reviews)")
                                
                                # Price and stock
                                price_stock_col1, price_stock_col2 = st.columns(2)
                                with price_stock_col1:
                                    if result.get('price'):
                                        st.write(f"**💰 ${result['price']:.2f}**")
                                with price_stock_col2:
                                    if result.get('stock'):
                                        stock_color = "🟢" if result['stock'] > 50 else ("🟡" if result['stock'] > 10 else "🔴")
                                        st.write(f"{stock_color} {result['stock']} in stock")
                                
                                # Description
                                if result.get('description'):
                                    desc = result['description']
                                    if len(desc) > 100:
                                        desc = desc[:100] + "..."
                                    st.write(desc)
                                
                                # Key specifications
                                if result.get('specifications'):
                                    specs = result['specifications']
                                    if isinstance(specs, dict):
                                        key_specs = []
                                        # Show only first 3 specs
                                        for key, value in list(specs.items())[:3]:
                                            key_specs.append(f"**{key.title()}:** {value}")
                                        if key_specs:
                                            st.write("**Key Specs:**")
                                            for spec in key_specs:
                                                st.write(f"• {spec}")
                                
                                # Relevance score (if available)
                                if result.get('relevance_score'):
                                    st.caption(f"Relevance: {result['relevance_score']:.1f}")
                                
                                st.divider()
        elif query:
            st.info("No products found matching your search. Try different keywords or check the suggestions above.")
    
    with tabs[2]:
        st.header("Product Management")
        st.info("Add or bulk index products")
        
        # Load sample data section
        with st.expander("🗂️ Load Sample Data", expanded=True):
            st.write("Load 20 sample products to get started with the application")
            if st.button("📥 Load Sample Products", type="primary"):
                with st.spinner("Loading sample products..."):
                    try:
                        response = requests.post(
                            f"{api_url}/api/data/load-sample",
                            timeout=30
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✅ {data['message']}")
                            st.info("You can now search for products like 'iPhone', 'laptop', 'headphones', etc.")
                        else:
                            st.error(f"❌ Error: {response.status_code} - {response.text}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ Error loading sample data: {str(e)}")
        
        # Single product indexing
        with st.expander("📝 Index Single Product"):
            product_data = {
                "name": st.text_input("Product Name"),
                "description": st.text_area("Description"),
                "category": st.text_input("Category"),
                "price": st.number_input("Price", min_value=0.0, step=0.01),
                "stock": st.number_input("Stock", min_value=0),
                "specifications": st.text_area("Specifications (JSON)", value="{}")
            }
            
            if st.button("📥 Index Product"):
                try:
                    if product_data["name"]:  # Basic validation
                        specs = json.loads(product_data["specifications"]) if product_data["specifications"] else {}
                        product_data["specifications"] = specs
                        
                        response = requests.post(
                            f"{api_url}/api/products",
                            json=product_data,
                            timeout=10
                        )
                        if response.status_code == 200:
                            st.success("✅ Product indexed successfully")
                        else:
                            st.error(f"❌ Error: {response.status_code} - {response.text}")
                    else:
                        st.warning("Please enter at least a product name")
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON in specifications")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error indexing product: {str(e)}")
        
        # Bulk indexing
        with st.expander("📚 Bulk Index Products"):
            uploaded_file = st.file_uploader("Upload JSON file with products", type="json")
            if uploaded_file:
                try:
                    products = json.load(uploaded_file)
                    st.write(f"Found {len(products)} products in file")
                    
                    # Preview first few products
                    if len(products) > 0:
                        st.write("**Preview of first product:**")
                        st.json(products[0])
                    
                    if st.button("📥 Bulk Index All Products"):
                        with st.spinner(f"Indexing {len(products)} products..."):
                            response = requests.post(
                                f"{api_url}/api/products/bulk",
                                json=products,
                                timeout=30
                            )
                            if response.status_code == 200:
                                st.success(f"✅ Successfully indexed {len(products)} products")
                            else:
                                st.error(f"❌ Error: {response.status_code} - {response.text}")
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file")
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error bulk indexing products: {str(e)}")

if __name__ == "__main__":
    main()