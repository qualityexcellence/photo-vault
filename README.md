# AI Smart Photo Vault

A production-ready, full-stack application for intelligent photo management powered by Google Cloud AI services.

## 🎯 Features

✨ **Photo Management**
- Secure image uploads to Google Cloud Storage
- Organized photo library with albums and collections
- Image archiving and deletion with soft delete support

🤖 **AI-Powered Capabilities**
- Automatic image captioning using Vision AI
- Object detection and localization
- Face detection with landmarks
- OCR (Optical Character Recognition) for text extraction
- Dominant color detection
- Duplicate image detection

🔍 **Smart Search**
- Full-text search across captions and OCR text
- Tag-based search
- Object-based image search
- Color-based search
- Search suggestions and history

📊 **Analytics & Insights**
- Real-time dashboard with storage metrics
- Daily upload patterns
- Tag popularity analytics
- User engagement tracking via BigQuery
- AI-generated insights about photo collection

🔐 **Security & Scale**
- Firebase authentication with JWT tokens
- Role-based access control (admin functionality)
- Audit logging for all operations
- PostgreSQL for relational data
- BigQuery for analytics data warehouse
- Cloud Run for serverless deployment

## 🏗️ Architecture

```
Frontend (React + TypeScript)
        ↓
FastAPI Backend (Python)
        ↓
┌─────────────────────────────────┐
│   Google Cloud Services         │
├─────────────────────────────────┤
│ • Cloud Storage (Images)        │
│ • Vision AI (Image Analysis)    │
│ • Vertex AI (ML Models)         │
│ • BigQuery (Analytics)          │
│ • Cloud SQL (PostgreSQL)        │
│ • Cloud Run (Deployment)        │
└─────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Google Cloud Project with enabled APIs
- Firebase project setup

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/qualityexcellence/ai-smart-photo-vault.git
cd ai-smart-photo-vault
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services with Docker Compose**
```bash
docker-compose up -d
```

This will start:
- PostgreSQL database
- Redis cache
- FastAPI backend (with hot reload)
- React frontend

4. **Access the application**
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Backend Setup (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python -c "from app.database import init_db; init_db()"

# Run server
uvicorn main:app --reload
```

### Frontend Setup (without Docker)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📚 API Documentation

The API follows RESTful principles with the following main endpoints:

### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/auth/refresh-token` - Refresh JWT token

### Images
- `POST /api/v1/images/upload` - Upload image
- `GET /api/v1/images` - List user's images (paginated)
- `GET /api/v1/images/{image_id}` - Get image details
- `DELETE /api/v1/images/{image_id}` - Delete image
- `POST /api/v1/images/{image_id}/archive` - Archive image

### Search
- `POST /api/v1/search` - Search images by query
- `GET /api/v1/search/suggestions` - Get search suggestions
- `GET /api/v1/search/duplicates` - Find duplicate images

### Analytics
- `GET /api/v1/analytics/dashboard` - User dashboard
- `GET /api/v1/analytics/storage` - Storage analytics
- `GET /api/v1/analytics/search-history` - Search history
- `GET /api/v1/analytics/insights` - AI insights

### Admin
- `GET /api/v1/admin/users` - List users
- `GET /api/v1/admin/users/{user_id}` - User statistics
- `GET /api/v1/admin/statistics` - System statistics
- `GET /api/v1/admin/audit-logs` - Audit logs

## 🔧 Configuration

### Environment Variables

Key configuration options:

```
DATABASE_URL              # PostgreSQL connection string
GCP_PROJECT_ID           # Google Cloud Project ID
GCS_BUCKET_NAME          # Cloud Storage bucket
FIREBASE_CREDENTIALS_PATH # Path to Firebase key
JWT_SECRET_KEY           # JWT signing key
MAX_FILE_SIZE_MB         # Maximum upload size (default: 100)
```

See `.env.example` for complete list.

## 📦 Deployment

### Deploy to Cloud Run

1. **Build and push Docker image**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT/photo-vault-api
```

2. **Deploy to Cloud Run**
```bash
gcloud run deploy photo-vault-api \
  --image gcr.io/YOUR_PROJECT/photo-vault-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

3. **Deploy infrastructure with Terraform**
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

### CI/CD Pipeline

The project includes GitHub Actions workflows for:
- Running unit tests
- Building Docker images
- Deploying to Cloud Run
- Database migrations

See `.github/workflows/ci-cd.yml`

## 🧪 Testing

### Run tests locally

```bash
# Backend tests
pytest tests/ --cov=app

# Frontend tests
cd frontend && npm test
```

### Test coverage

- Backend: Pytest with coverage reporting
- Frontend: Jest with React Testing Library

## 📊 Database Schema

Key tables:
- `users` - User accounts and quota info
- `images` - Photo metadata and AI analysis results
- `albums` - Photo collections
- `search_history` - User search tracking
- `analytics` - Events for BigQuery sync
- `audit_logs` - Admin activity tracking

See `backend/app/models.py` for detailed schema.

## 🔐 Security

- **Authentication**: Firebase + JWT tokens
- **Authorization**: Role-based access control
- **Data Encryption**: HTTPS/TLS in transit, encryption at rest in Cloud Storage
- **Audit Logging**: All admin operations tracked
- **Rate Limiting**: Configurable per endpoint
- **CORS**: Whitelist specific origins

## 🎓 Interview Talking Points

1. **Scalability**: Serverless with Cloud Run auto-scaling
2. **Real-time Analytics**: BigQuery integration for insights
3. **AI Integration**: Google Vision API for image analysis
4. **Database Design**: Proper normalization with indexed queries
5. **API Design**: RESTful with clear versioning
6. **Error Handling**: Comprehensive exception handling
7. **Deployment**: Infrastructure as Code with Terraform
8. **Testing**: Automated CI/CD pipeline

## 📄 Resume Bullet Points

- **Designed and built a production-ready full-stack application** using React, FastAPI, PostgreSQL, and Google Cloud services, serving as portfolio piece
- **Implemented AI-powered image analysis** using Google Cloud Vision API, enabling automatic tagging, captioning, and metadata extraction
- **Built serverless architecture** with Cloud Run and BigQuery analytics, achieving automatic scaling and cost optimization
- **Developed comprehensive REST API** with FastAPI following best practices including authentication, validation, error handling, and pagination
- **Automated deployment pipeline** using GitHub Actions and Terraform, enabling continuous integration and infrastructure as code
- **Implemented full-text search** with multiple search types (text, tag, object, color) and duplicate detection
- **Created responsive React UI** with TypeScript for type safety and real-time analytics dashboard
- **Set up analytics infrastructure** with BigQuery for tracking user behavior and generating actionable insights

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review API documentation at `/docs`

## 🎯 Future Enhancements

- [ ] Mobile app with React Native
- [ ] Advanced ML models for image similarity
- [ ] Social sharing features
- [ ] Collaborative albums
- [ ] Photo editing tools
- [ ] Advanced permissions system
- [ ] Web3 integration
- [ ] Batch operations API
