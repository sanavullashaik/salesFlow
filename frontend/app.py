"""
Streamlit frontend application for Product Search
"""
import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
import os

st.set_page_config(
    page_title="Product Search Dashboard",
    page_icon="🔍",
    layout="wide"
)

# Default API URL using Docker service name
DEFAULT_API_URL = "http://backend:8000/api"

def format_product_request(email_data):
    """Format product request data for display"""
    if not email_data:
        return pd.DataFrame()
    
    requests = []
    for req in email_data:
        requests.append({
            "Product": req["product_name"],
            "Description": req["description"],
            "Quantity": req["quantity"],
            "Priority": req["priority"],
            "Specifications": json.dumps(req["specifications"])
        })
    return pd.DataFrame(requests)

def main():
    st.title("Product Search Dashboard")
    
    # Sidebar for configuration
    st.sidebar.title("Settings")
    api_url = st.sidebar.text_input("API URL", value=DEFAULT_API_URL)
    
    # Main content
    tabs = st.tabs(["Email Monitor", "Search Products", "Product Management"])
    
    with tabs[0]:
        st.header("Email Monitor")
        st.info("Monitor incoming product request emails")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Check New Emails", type="primary"):
                try:
                    response = requests.get(f"{api_url}/emails/check", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Found {data['new_emails']} new emails")
                        if data['processed_requests']:
                            st.dataframe(format_product_request(data['processed_requests']))
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error checking emails: {str(e)}")
    
    with tabs[1]:
        st.header("Search Products")
        st.info("Search for products in the database")
        
        query = st.text_input("Search Query")
        size = st.slider("Number of Results", min_value=1, max_value=50, value=10)
        
        if st.button("Search", type="primary"):
            if query:
                try:
                    response = requests.get(
                        f"{api_url}/search",
                        params={"q": query, "size": size},
                        timeout=10
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data['results']:
                            st.dataframe(pd.DataFrame(data['results']))
                        else:
                            st.info("No results found")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error searching products: {str(e)}")
            else:
                st.warning("Please enter a search query")
    
    with tabs[2]:
        st.header("Product Management")
        st.info("Add or bulk index products")
        
        # Single product indexing
        with st.expander("Index Single Product"):
            product_data = {
                "name": st.text_input("Product Name"),
                "description": st.text_area("Description"),
                "category": st.text_input("Category"),
                "price": st.number_input("Price", min_value=0.0, step=0.01),
                "stock": st.number_input("Stock", min_value=0),
                "specifications": st.text_area("Specifications (JSON)", value="{}")
            }
            
            if st.button("Index Product"):
                try:
                    specs = json.loads(product_data["specifications"])
                    product_data["specifications"] = specs
                    
                    response = requests.post(
                        f"{api_url}/products",
                        json=product_data,
                        timeout=10
                    )
                    if response.status_code == 200:
                        st.success("Product indexed successfully")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON in specifications")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error indexing product: {str(e)}")
        
        # Bulk indexing
        with st.expander("Bulk Index Products"):
            uploaded_file = st.file_uploader("Upload JSON file", type="json")
            if uploaded_file:
                try:
                    products = json.load(uploaded_file)
                    if st.button("Bulk Index"):
                        response = requests.post(
                            f"{api_url}/products/bulk",
                            json=products,
                            timeout=10
                        )
                        if response.status_code == 200:
                            st.success(f"Successfully indexed {len(products)} products")
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON file")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error bulk indexing products: {str(e)}")

if __name__ == "__main__":
    main()
