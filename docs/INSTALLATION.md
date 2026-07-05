# Installation & Setup Guide

Complete instructions for setting up AI Smart Photo Vault locally or in production.

## Local Development Setup

### System Requirements

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Redis 7+
- Docker & Docker Compose (recommended)
- Git
- 4GB RAM minimum, 8GB recommended

### Option 1: Quick Setup with Docker Compose (Recommended)

**1. Clone and Configure**
```bash
git clone <your-repo-url>
cd ai-smart-photo-vault
cp .env.example .env
```

**2. Set Environment Variables**

Edit `.env` with your configuration:
```bash
# Database (will be created by Docker)
DATABASE_URL=postgresql://photo_user:secure_password@postgres:5432/photo_vault

# Google Cloud
GCP_PROJECT_ID=your-project-id
GCS_BUCKET_NAME=your-bucket-name
FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json

# Secrets
JWT_SECRET_KEY=your-super-secret-key-min-32-chars

# Features
DEBUG=true
LOG_LEVEL=INFO
```

**3. Add Firebase Credentials**

Place your Firebase service account JSON file at `firebase-credentials.json`

**4. Start Services**
```bash
docker-compose up -d
```

This starts:
- PostgreSQL at `localhost:5432`
- Redis at `localhost:6379`
- Backend at `http://localhost:8000`
- Frontend at `http://localhost:3000`

**5. View Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

**6. Stop Services**
```bash
docker-compose down
# With volume cleanup
docker-compose down -v
```

### Option 2: Manual Setup

#### Backend Setup

**1. Create Virtual Environment**
```bash
python -m venv venv

# Activate
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**2. Install Dependencies**
```bash
pip install -r requirements.txt
```

**3. Set Up Environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

**4. Set Up Database**

Make sure PostgreSQL is running:
```bash
# macOS with Homebrew
brew services start postgresql

# Or start manually
postgres -D /usr/local/var/postgres
```

Create database and user:
```bash
psql postgres
CREATE DATABASE photo_vault;
CREATE USER photo_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE photo_vault TO photo_user;
\q
```

Initialize tables:
```bash
python -c "from app.database import init_db; init_db()"
```

**5. Start Backend**
```bash
uvicorn main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

#### Frontend Setup

**1. Install Dependencies**
```bash
cd frontend
npm install
```

**2. Create .env.local**
```bash
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_FIREBASE_CONFIG='{"apiKey":"...","projectId":"..."}'
```

**3. Start Development Server**
```bash
npm start
# App available at http://localhost:3000
```

## Production Setup

### Prerequisites

- Google Cloud Project with billing enabled
- Firebase project configured
- Domain name (optional but recommended)
- SSL certificate (auto via Cloud Run)

### Step-by-Step Deployment

**1. Follow Deployment Guide**
See `docs/DEPLOYMENT.md` for complete production deployment instructions.

**2. Key Commands**
```bash
# Deploy backend
gcloud run deploy photo-vault-api \
  --image gcr.io/PROJECT_ID/photo-vault-api:latest \
  --region us-central1

# Deploy frontend
gsutil -m rsync -r frontend/build/ gs://PROJECT_ID-photo-vault-frontend/
```

## Testing

### Backend Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Frontend Tests

```bash
cd frontend
npm test
npm run build
```

## Troubleshooting

### Backend Issues

**"ModuleNotFoundError: No module named 'app'"**
```bash
# Make sure you're in the backend directory
cd ai-smart-photo-vault
python -m uvicorn main:app --reload
```

**"Error connecting to database"**
```bash
# Check PostgreSQL is running
psql postgres -U postgres

# Check connection string in .env
DATABASE_URL=postgresql://photo_user:PASSWORD@localhost:5432/photo_vault
```

**"Firebase credentials not found"**
```bash
# Download from Firebase Console
# Place at: ./firebase-credentials.json
ls -la firebase-credentials.json
```

**Port already in use**
```bash
# Backend (change to different port)
uvicorn main:app --port 8001

# Frontend (change to different port)
PORT=3001 npm start
```

### Frontend Issues

**"npm ERR! code ERESOLVE"**
```bash
# Try force dependency resolution
npm install --legacy-peer-deps
```

**CORS errors in console**
```bash
# Make sure ALLOWED_ORIGINS in backend includes frontend URL
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Blank page or 404**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check .env variables
echo $REACT_APP_API_URL
```

### Database Issues

**"permission denied for schema public"**
```bash
# Grant proper permissions
psql -U postgres -d photo_vault
GRANT ALL ON SCHEMA public TO photo_user;
```

**"could not translate host name"**
```bash
# Make sure database host is correct in CONNECTION_STRING
# For Docker: use service name "postgres"
# For local: use "localhost"
```

## Project Structure

```
ai-smart-photo-vault/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration
│   │   ├── database.py         # Database setup
│   │   ├── models.py           # SQLAlchemy models
│   │   ├── schemas.py          # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   │   ├── auth.py
│   │   │   ├── gcs.py
│   │   │   ├── vision_ai.py
│   │   │   └── bigquery.py
│   │   └── routes/             # API endpoints
│   │       ├── auth.py
│   │       ├── images.py
│   │       ├── search.py
│   │       ├── admin.py
│   │       └── analytics.py
│   ├── main.py                 # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── hooks/             # Custom hooks
│   │   ├── services/          # API client
│   │   ├── types/             # TypeScript types
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── terraform/                  # IaC
│   ├── main.tf
│   ├── variables.tf
│   └── terraform.tfvars.example
├── docs/                      # Documentation
│   ├── DEPLOYMENT.md
│   ├── INTERVIEW_QUESTIONS.md
│   └── RESUME_BULLETS.md
├── .github/workflows/         # CI/CD
├── docker-compose.yml         # Local dev
├── Dockerfile                 # Backend image
├── .env.example              # Environment template
└── README.md
```

## Development Workflow

### Making Code Changes

**Backend:**
```bash
# Code changes auto-reload with --reload flag
uvicorn main:app --reload

# Changes to models require migration
alembic revision --autogenerate -m "description"
alembic upgrade head
```

**Frontend:**
```bash
# Changes auto-reload with npm start
npm start
```

### Committing Code

```bash
# Format code
# Backend
pip install black
black .

# Frontend
npx prettier --write .

# Commit
git add .
git commit -m "feat: add awesome feature"
git push origin feature-branch
```

### Creating a Pull Request

1. Create feature branch
2. Make changes
3. Run tests locally
4. Push to GitHub
5. Create PR with clear description
6. Wait for CI/CD checks to pass
7. Get review
8. Merge to main

## Common Development Tasks

### Add a new API endpoint

**1. Create model** (if needed) in `backend/app/models.py`
**2. Create schema** in `backend/app/schemas.py`
**3. Create route** in `backend/app/routes/`
**4. Test with**:
```bash
curl -X POST http://localhost:8000/api/v1/endpoint
```

### Add a new React component

**1. Create component** in `frontend/src/components/`
**2. Import and use** in parent component
**3. Test in browser** at `http://localhost:3000`

### Add migration

```bash
# Make model changes in backend/app/models.py
# Generate migration
alembic revision --autogenerate -m "describe changes"
# Review migration file
# Apply
alembic upgrade head
```

## Performance Tips

**Frontend:**
- Use React DevTools Profiler to find slow components
- Implement code splitting for lazy loading
- Optimize images with proper formats and sizes

**Backend:**
- Use database query logger to find N+1 queries
- Implement caching for frequently accessed data
- Profile with `cProfile` or `py-spy`

**Database:**
- Monitor slow queries: `log_min_duration_statement = 1000`
- Use EXPLAIN ANALYZE to optimize queries
- Regular VACUUM and ANALYZE

## Next Steps

1. Explore the codebase
2. Run tests to ensure everything works
3. Try making a small code change
4. Deploy to production following `docs/DEPLOYMENT.md`
5. Set up monitoring and alerts

## Support

For issues:
1. Check this guide for common problems
2. Review error messages in logs
3. Check API documentation at `/docs`
4. See troubleshooting section above
