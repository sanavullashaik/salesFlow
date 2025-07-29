# SalesFlow Deployment Guide

This guide covers deployment options for the SalesFlow application using GitHub Actions.

## 🏗️ Architecture

The application consists of three main components:
- **Frontend**: Streamlit web interface (port 8501)
- **Backend**: FastAPI REST API (port 8000)
- **OpenSearch**: Search engine for product indexing (port 9200)

## 🚀 GitHub Actions Deployment

### Prerequisites

1. **GitHub Repository Secrets**: Set these in your repository settings:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   ```

2. **GitHub Container Registry**: The workflow automatically uses GitHub Container Registry (ghcr.io) to store Docker images.

### Deployment Process

The GitHub Actions workflow (`/.github/workflows/deploy.yml`) automatically:

1. **Builds and pushes Docker images** to GitHub Container Registry
2. **Deploys services** using Docker Compose with health checks
3. **Loads sample data** automatically
4. **Runs health checks** to ensure everything is working

### Workflow Triggers

- **Push to main branch**: Full deployment
- **Pull requests**: Build and test only (no deployment)

### Manual Deployment

You can also deploy manually:

```bash
# Clone the repository
git clone https://github.com/your-username/salesFlow.git
cd salesFlow

# Set environment variables
export GROQ_API_KEY="your_groq_api_key_here"

# Deploy using Docker Compose
docker-compose up -d

# Wait for services to be ready
sleep 60

# Load sample data
curl -X POST http://localhost:8000/api/data/load-sample
```

## 🌐 Accessing the Application

After deployment:

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **OpenSearch**: http://localhost:9200
- **API Documentation**: http://localhost:8000/docs

## 📊 Monitoring and Health Checks

### Health Check Endpoints

- **Backend**: `GET http://localhost:8000/`
- **OpenSearch**: `GET http://localhost:9200/_cluster/health`
- **Frontend**: `GET http://localhost:8501/_stcore/health`

### Docker Health Checks

All services include built-in health checks:

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs [service_name]
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | GROQ API key for AI processing | Required |
| `OPENSEARCH_HOST` | OpenSearch connection URL | `http://opensearch:9200` |
| `BACKEND_URL` | Backend API URL for frontend | `http://backend:8000` |

### Resource Requirements

**Minimum Requirements:**
- CPU: 2 cores
- RAM: 4GB
- Storage: 10GB

**Recommended for Production:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB
- SSD preferred for OpenSearch performance

## 🛡️ Security Features

- **Non-root containers**: All services run as non-root users
- **No hardcoded secrets**: Environment variables for sensitive data
- **Health checks**: Automatic service monitoring
- **Container isolation**: Each service runs in its own container

## 🚨 Troubleshooting

### Common Issues

1. **OpenSearch startup fails**:
   ```bash
   # Check OpenSearch logs
   docker-compose logs opensearch
   
   # Increase memory if needed
   # Edit docker-compose.yml and increase OPENSEARCH_JAVA_OPTS
   ```

2. **Backend can't connect to OpenSearch**:
   ```bash
   # Check network connectivity
   docker-compose exec backend curl http://opensearch:9200
   
   # Restart services in order
   docker-compose restart opensearch
   docker-compose restart backend
   ```

3. **Frontend can't connect to backend**:
   ```bash
   # Check backend health
   curl http://localhost:8000/
   
   # Check frontend logs
   docker-compose logs frontend
   ```

### Logs and Debugging

```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f opensearch

# Execute commands in containers
docker-compose exec backend bash
docker-compose exec frontend bash
```

## 📱 Using the Application

1. **Load Sample Data**: Go to "Product Management" → Click "Load Sample Products"
2. **Search Products**: Use the search tab with autocomplete and instant search
3. **Process Images**: Upload product images for AI-powered information extraction
4. **Manage Products**: Add individual products or bulk upload via JSON

## 🔄 Updates and Maintenance

### Updating the Application

1. Push changes to the main branch
2. GitHub Actions will automatically build and deploy
3. Services will be updated with zero downtime using rolling updates

### Backup and Recovery

```bash
# Backup OpenSearch data
docker-compose exec opensearch curl -X POST "localhost:9200/_snapshot/backup/snapshot_1"

# Export current data
curl "http://localhost:8000/api/search?q=*&size=1000" > backup.json
```

## 📈 Scaling

For production scaling:

1. **Horizontal scaling**: Deploy multiple backend instances behind a load balancer
2. **OpenSearch cluster**: Set up OpenSearch cluster for high availability
3. **Container orchestration**: Consider Kubernetes for large-scale deployments

## 🆘 Support

If you encounter issues:

1. Check the logs using the commands above
2. Verify environment variables are set correctly
3. Ensure all ports are available and not blocked by firewall
4. Check system resources (CPU, memory, disk space)

For additional support, create an issue in the GitHub repository with:
- Error logs
- System information
- Steps to reproduce the issue