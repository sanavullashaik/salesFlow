# SalesFlow - AI-Powered Product Search Platform

A modern, full-stack application for intelligent product search with AI-powered image processing and real-time search capabilities.

## 🚀 Features

### Core Functionality
- **🔍 Instant Search**: Ultra-fast product search with millisecond response times
- **🤖 AI Image Processing**: Extract product information from images using GROQ AI
- **⚡ Real-time Autocomplete**: Search-as-you-type suggestions powered by OpenSearch
- **🧠 AI-Powered Reranking**: Optional GROQ-based result reranking for enhanced accuracy
- **📱 Responsive UI**: Modern Streamlit-based interface with card layouts

### Advanced Search Features
- **Search-as-you-type**: Edge n-gram tokenization for instant results
- **Multi-field Search**: Search across product names, descriptions, brands, and categories
- **Fuzzy Matching**: Handles typos and partial matches
- **Category Filtering**: Browse products by category
- **Price and Stock Information**: Real-time inventory data

## 🏗️ Architecture

### Backend (FastAPI)
- **OpenSearch Integration**: Advanced search engine with custom analyzers
- **GROQ AI Integration**: Latest models for image processing and result reranking
- **RESTful API**: Clean, documented endpoints
- **Docker Support**: Containerized backend services

### Frontend (Streamlit)
- **Interactive Dashboard**: Search, image processing, and product management
- **Real-time Updates**: Instant search results as you type
- **Caching System**: Intelligent caching for optimal performance
- **Card-based UI**: Modern product display with images and ratings

### Infrastructure
- **OpenSearch**: Search engine with autocomplete and analytics
- **Docker Compose**: Multi-service orchestration
- **GitHub Actions**: CI/CD pipeline for automated deployment
- **Health Checks**: Service monitoring and reliability

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)
- GROQ API Key (get from [console.groq.com](https://console.groq.com))
- Git

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/salesFlow.git
cd salesFlow
```

### 2. Environment Setup
The `.env` file contains your GROQ API key:
```bash
GROQ_API_KEY=your_groq_api_key_here
OPENSEARCH_HOST=http://opensearch:9200
BACKEND_URL=http://backend:8000
```

**Important**: Replace `your_groq_api_key_here` with your actual GROQ API key.

### 3. Start the Application
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access the Application
- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **OpenSearch**: http://localhost:9200

### 5. Load Sample Data
1. Go to the **Product Management** tab
2. Click **"Load Sample Products"**
3. Wait for 26 sample products to be indexed
4. Start searching for products like "iPhone", "laptop", "headphones"

## 🛠️ Development Setup

### Local Development (Without Docker)

1. **Install Python Dependencies**:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
pip install -r requirements.txt
```

2. **Start OpenSearch**:
```bash
docker run -d -p 9200:9200 -e "discovery.type=single-node" opensearchproject/opensearch:latest
```

3. **Start Backend**:
```bash
cd backend
python main.py
```

4. **Start Frontend**:
```bash
cd frontend
streamlit run app.py
```

## 📊 API Documentation

### Core Endpoints

#### Search Products
```http
GET /api/search?q=laptop&size=10&use_groq_rerank=false
```

#### Instant Search (Ultra-fast)
```http
GET /api/instant-search?q=iphone&size=10
```

#### Autocomplete Suggestions
```http
GET /api/autocomplete?q=lap&size=5
```

#### Process Image
```http
POST /api/images/process
Content-Type: multipart/form-data
```

#### Index Product
```http
POST /api/products
Content-Type: application/json

{
  "name": "iPhone 15 Pro",
  "description": "Latest iPhone with titanium design",
  "category": "smartphones",
  "price": 999.99,
  "stock": 50,
  "brand": "Apple",
  "rating": 4.8,
  "reviews_count": 12847
}
```

### Sample API Responses

**Search Results**:
```json
{
  "status": "success",
  "results": [
    {
      "name": "iPhone 15 Pro",
      "brand": "Apple",
      "category": "smartphones",
      "price": 999.99,
      "stock": 50,
      "rating": 4.8,
      "reviews_count": 12847,
      "image_url": "https://example.com/iphone15pro.jpg",
      "relevance_score": 95.2
    }
  ]
}
```

## 🤖 AI Features

### Image Processing
- **Model**: `llama-3.2-90b-vision-preview`
- **Capabilities**: Extract product names, categories, descriptions, specifications
- **Supported Formats**: PNG, JPG, JPEG, GIF, BMP
- **Processing Time**: ~2-5 seconds per image

### Search Reranking
- **Model**: `llama-3.1-8b-instant`
- **Purpose**: Improve search relevance using AI understanding
- **Fallback**: Position-based scoring when AI is disabled
- **Performance**: Optional feature for accuracy vs speed trade-off

## 🔧 Configuration

### Environment Variables
```bash
# GROQ AI Configuration
GROQ_API_KEY=your_key_here

# OpenSearch Configuration  
OPENSEARCH_HOST=http://opensearch:9200

# Backend URL (for frontend)
BACKEND_URL=http://backend:8000

# Logging Level
LOG_LEVEL=INFO
```

### OpenSearch Settings
- **Index Name**: `products`
- **Analyzers**: Custom edge n-gram tokenizers for autocomplete
- **Mappings**: Search-as-you-type fields for instant results
- **Timeout**: 50ms for instant search, 2s for regular search

### Performance Tuning
- **Cache TTL**: 60s for search results, 30s for autocomplete
- **Request Timeouts**: 1s for instant search, 10s for regular search
- **Max Results**: 50 products per search query

## 🚀 Deployment

### GitHub Actions (Recommended)
The repository includes GitHub Actions workflows for:
- **Automated Testing**: Run tests on push/PR
- **Docker Build**: Build and push images to GitHub Container Registry
- **Deployment**: Deploy to cloud platforms

### Manual Deployment
```bash
# Build images
docker-compose build

# Push to registry
docker tag salesflow_backend:latest your-registry/salesflow-backend:latest
docker push your-registry/salesflow-backend:latest

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Environment-Specific Configurations
- **Development**: `docker-compose.yml`
- **Production**: `docker-compose.prod.yml`
- **Testing**: `docker-compose.test.yml`

## 🔍 Search Technology

### OpenSearch Features Used
1. **Search-as-you-type**: Built-in field type for instant results
2. **Completion Suggester**: Fast autocomplete with prefix matching
3. **Multi-match Queries**: Search across multiple fields with boosting
4. **Bool Prefix Queries**: Optimized for partial word matching
5. **Custom Analyzers**: Edge n-gram tokenization for fuzzy matching

### Search Performance
- **Instant Search**: <50ms response time
- **Regular Search**: <200ms response time
- **Autocomplete**: <30ms response time
- **Concurrent Users**: Handles 100+ simultaneous searches

## 📈 Monitoring & Analytics

### Health Checks
- Backend API health endpoint: `/health`
- OpenSearch cluster health: `/_cluster/health`
- Service dependency checks

### Logging
- Structured JSON logging
- Request/response timing
- Error tracking and alerting
- Search query analytics

## 🛡️ Security

### API Security
- CORS configuration for frontend integration
- Input validation and sanitization
- Rate limiting (production deployment)
- Secure environment variable handling

### Data Privacy
- No personal data collection
- Anonymous search analytics
- GDPR compliance ready
- Secure image processing (temporary storage only)

## 📚 Project Structure

```
salesFlow/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── services/       # Business logic
│   │   └── data/           # Sample data
│   ├── requirements.txt
│   └── main.py
├── frontend/               # Streamlit frontend
│   ├── app.py
│   └── requirements.txt
├── docker/                 # Docker configurations
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── .github/workflows/      # CI/CD pipelines
├── docker-compose.yml      # Development setup
├── .env                    # Environment variables
└── README.md              # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Add tests for new features
- Update documentation
- Use semantic commit messages

## 🐛 Troubleshooting

### Common Issues

**OpenSearch Connection Failed**:
```bash
# Check OpenSearch status
docker-compose logs opensearch

# Restart OpenSearch
docker-compose restart opensearch
```

**GROQ API Errors**:
- Verify API key in `.env` file
- Check API rate limits
- Ensure model names are current

**Slow Search Performance**:
- Check OpenSearch cluster health
- Review cache hit rates
- Monitor system resources

**Frontend Not Loading**:
```bash
# Check backend connectivity
curl http://localhost:8000/api/health

# Restart frontend
docker-compose restart frontend
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenSearch**: For providing excellent search capabilities
- **GROQ**: For fast AI inference and vision models
- **FastAPI**: For the modern, fast web framework
- **Streamlit**: For rapid UI development
- **Docker**: For containerization and deployment

## 📞 Support

For support and questions:
- Open an issue on GitHub
- Check the [documentation](https://github.com/your-username/salesFlow/wiki)
- Join our community discussions

---

**Built with ❤️ for modern product search experiences**
