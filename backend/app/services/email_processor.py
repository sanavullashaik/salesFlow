"""
Email processing service using LangChain with Groq for content extraction
"""
from typing import Dict, List
from imap_tools import MailBox, AND
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel
from langchain.output_parsers import PydanticOutputParser
import os
from dotenv import load_dotenv

load_dotenv()

class ProductRequest(BaseModel):
    product_name: str
    description: str
    specifications: Dict[str, str]
    quantity: int
    priority: str

class EmailProcessor:
    def __init__(self):
        self.email_server = os.getenv("EMAIL_SERVER")
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            api_key=os.getenv("GROQ_API_KEY"),
            model_name="mixtral-8x7b-32768"  # Using Mixtral model
        )
        
        # Create parser for structured output
        self.parser = PydanticOutputParser(pydantic_object=ProductRequest)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "Extract product request details from the following email. Format as JSON."),
            ("human", "{email_content}"),
            ("system", "Format the output as follows:\n{format_instructions}")
        ])

    def fetch_new_emails(self) -> List[Dict]:
        """Fetch new unread emails using imap-tools"""
        emails = []
        
        with MailBox(self.email_server).login(self.email_user, self.email_password) as mailbox:
            # Fetch only unseen messages
            for msg in mailbox.fetch(AND(seen=False)):
                emails.append({
                    "subject": msg.subject,
                    "from": msg.from_,
                    "content": msg.text or msg.html
                })
                
        return emails

    def extract_product_request(self, email_content: str) -> ProductRequest:
        """Extract product request details using LangChain with Groq"""
        formatted_prompt = self.prompt.format_messages(
            email_content=email_content,
            format_instructions=self.parser.get_format_instructions()
        )
        
        response = self.llm.invoke(formatted_prompt)
        return self.parser.parse(response.content)
