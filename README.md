# Product Search Application

A smart product search application that processes email requests, extracts product information, and uses Elasticsearch with RAG for intelligent product matching.

## Features

- Email Processing: Automatically fetch and process product request emails
- Product Search: Advanced search capabilities using Elasticsearch
- RAG-based Matching: Uses Retrieval Augmented Generation for intelligent product matching
- Modern UI: Streamlit-based dashboard for easy interaction
- Docker Support: Fully containerized application

## Tech Stack

- Backend: FastAPI, Python 3.11
- Frontend: Streamlit
- Database: Elasticsearch
- LLM Integration: Groq
- Containerization: Docker

## Prerequisites

- Docker and Docker Compose
- Python 3.11 or higher
- Groq API key
- Email account for processing requests

## Environment Variables

Create a `.env` file with the following variables:

```bash
GROQ_API_KEY=your_groq_api_key
EMAIL_SERVER=your_email_server
EMAIL_USER=your_email_username
EMAIL_PASSWORD=your_email_app_password
```

## Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/salesFlow.git
   cd salesFlow
   ```

2. Create and configure the `.env` file as described above.

3. Build and start the containers:
   ```bash
   docker-compose up --build
   ```

4. Access the application:
   - Frontend Dashboard: http://localhost:8501
   - Backend API: http://localhost:8000
   - Elasticsearch: http://localhost:9200

## Project Structure
```
salesFlow/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── endpoints.py
│   │   └── services/
│   │       ├── email_processor.py
│   │       ├── elasticsearch_service.py
│   │       └── product_matcher.py
│   └── main.py
├── frontend/
│   └── app.py
├── docker/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## API Endpoints

- `GET /api/emails/check`: Check for new product request emails
- `POST /api/products`: Index a single product
- `POST /api/products/bulk`: Bulk index products
- `GET /api/search`: Search for products
- `POST /api/match`: Match products using RAG

## Development

To run the application in development mode:

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   .\venv\Scripts\activate  # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run services individually:
   ```bash
   # Terminal 1 - Backend
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

   # Terminal 2 - Frontend
   streamlit run frontend/app.py

   # Terminal 3 - Elasticsearch (using Docker)
   docker-compose up elasticsearch
   ```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
