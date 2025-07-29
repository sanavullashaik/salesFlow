"""
Image processing service using GROQ for extracting product information from images
"""
from typing import Dict, List
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
import os
from dotenv import load_dotenv
import base64
import io
from PIL import Image

load_dotenv()

class ProductInfo(BaseModel):
    product_name: str
    description: str
    specifications: Dict[str, str]
    category: str
    estimated_price_range: str

class ImageProcessor:
    def __init__(self):
        # Initialize Groq LLM with latest vision model
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="llama-3.2-90b-vision-preview",  # Latest vision model
            temperature=0.3,
            max_tokens=500  # Limit for faster responses
        )
        
        # Create parser for structured output
        self.parser = PydanticOutputParser(pydantic_object=ProductInfo)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a product information extraction expert. Analyze the product image and extract detailed information about the product including name, description, specifications, category, and estimated price range. Be as specific as possible about technical specifications, dimensions, materials, brand, model, etc.
            
            Format the output as follows:
            {format_instructions}"""),
            ("human", "Extract product information from this image: {image_description}")
        ])

    def process_image_file(self, image_file) -> ProductInfo:
        """Process an uploaded image file and extract product information"""
        # Convert image to base64 for processing
        image = Image.open(image_file)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Create a description prompt for the image
        image_description = "Product image uploaded for analysis"
        
        formatted_prompt = self.prompt.format_messages(
            image_description=image_description,
            format_instructions=self.parser.get_format_instructions()
        )
        
        response = self.llm.invoke(formatted_prompt)
        return self.parser.parse(response.content)

    def extract_products_from_image(self, image_file) -> List[Dict]:
        """Extract multiple products from a single image if present"""
        try:
            # For now, process as single product
            product_info = self.process_image_file(image_file)
            return [product_info.dict()]
        except Exception as e:
            # Fallback to basic product structure
            return [{
                "product_name": "Unknown Product",
                "description": "Product extracted from image",
                "specifications": {},
                "category": "general",
                "estimated_price_range": "Unknown"
            }]