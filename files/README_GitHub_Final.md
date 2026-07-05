# Photo Vault - AI-Powered Smart Photo Management Platform

Enterprise-grade full-stack web application combining cloud-native architecture with AI-powered image analysis.

## Features

- **Secure Authentication** - Firebase + JWT tokens with bcrypt password hashing
- **Fast Image Upload** - Direct to Google Cloud Storage with automatic processing
- **AI Image Analysis** - Google Cloud Vision API (labels, text, faces, colors, objects)
- **Real-time Analytics** - Dashboard with storage tracking and insights
- **Data Warehouse** - BigQuery integration for advanced analytics
- **Professional UI** - Responsive HTML/CSS/JavaScript (zero dependencies)
- **Complete API** - RESTful with auto-generated Swagger documentation
- **Containerized** - Docker Compose for local development
- **Cloud Native** - Cloud Run, Cloud SQL, Cloud Storage, BigQuery
- **CI/CD Pipeline** - GitHub Actions with automatic deployment

## Tech Stack

### Backend
- **Framework**: Python FastAPI
- **Database**: PostgreSQL (Cloud SQL)
- **Cache**: Redis
- **Authentication**: Firebase Admin SDK + JWT (passlib bcrypt)
- **ORM**: SQLAlchemy
- **Validation**: Pydantic

### Cloud Services
- **Compute**: Google Cloud Run
- **Storage**: Google Cloud Storage
- **Database**: Cloud SQL (PostgreSQL)
- **Analytics**: Google BigQuery
- **AI/ML**: Google Cloud Vision API
- **Artifact Registry**: Docker image storage

### Frontend
- **Type**: Standalone HTML/CSS/JavaScript
- **No Dependencies**: Works in any browser
- **API Documentation**: Swagger UI + Postman Collection

### DevOps & Infrastructure
- **Containerization**: Docker + Docker Compose
- **IaC**: Terraform (Google Cloud Platform)
- **CI/CD**: GitHub Actions

## Quick Start

### Local Development

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/photo-vault.git
cd photo-vault

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://user:password@postgres:5432/photo_vault
REDIS_URL=redis://redis:6379
GCP_PROJECT_ID=aivaultphotosgcp
GCS_BUCKET=aivaultphotosgcp-images
ENVIRONMENT=development
EOF

# Place firebase-credentials.json from GCP Console

# Start all services
docker-compose up -d

# Access:
# - Backend API: http://localhost:8000
# - Swagger UI: http://localhost:8000/docs
# - Frontend: open frontend/index.html in browser
```

## API Documentation

### Key Endpoints

**Authentication**
- `POST /api/v1/auth/signup` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user

**Images**
- `POST /api/v1/images/upload` - Upload image (auto-analyzed)
- `GET /api/v1/images/` - List user images
- `DELETE /api/v1/images/{id}` - Delete image

**Analytics**
- `GET /api/v1/analytics/dashboard` - Dashboard statistics
- `GET /api/v1/analytics/images` - Image analytics

View complete API docs at: http://localhost:8000/docs

## Vision AI Integration

Every uploaded image is automatically analyzed:
- **Labels** - Objects detected in image
- **Text** - OCR text extraction
- **Faces** - Face detection and count
- **Colors** - Dominant colors
- **Properties** - Image attributes

Results stored in PostgreSQL and BigQuery for analytics.

## Deployment

### Option 1: GitHub Actions (Recommended)
1. Push to main branch
2. Workflow automatically builds and deploys to Cloud Run

### Option 2: Manual with gcloud
```bash
gcloud run deploy photo-vault-backend \
  --source . \
  --region us-central1 \
  --platform managed
```

### Option 3: Terraform
```bash
cd terraform
terraform init
terraform apply
```

See DEPLOYMENT.md for detailed instructions.

## Project Structure

```
photo-vault/
├── .github/workflows/      # GitHub Actions CI/CD
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Business logic
│   │   └── models.py      # Database models
│   └── requirements.txt
├── frontend/               # HTML/CSS/JS app
│   └── index.html
├── terraform/              # Infrastructure as Code
├── docker-compose.yml      # Local development
├── Dockerfile
├── README.md
└── DEPLOYMENT.md
```

## Testing

```bash
cd backend
pip install pytest pytest-cov
pytest tests/ -v --cov=app
```

GitHub Actions runs tests on every pull request.

## Development Workflow

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and commit: `git commit -m "Add feature"`
3. Push to GitHub: `git push origin feature/my-feature`
4. Open Pull Request
5. Tests run automatically - merge when green
6. Automatic deployment to Cloud Run on main branch

## Performance

- **API Response**: < 200ms average
- **Image Upload**: Supports up to 100GB quota
- **Vision AI**: < 2 seconds per image
- **Cloud Run Startup**: < 10 seconds

## Security

- Password hashing with bcrypt
- JWT token authentication
- Firebase security
- Cloud SQL SSL/TLS
- Environment variable secrets
- Service account based access

## Monitoring

```bash
# View Cloud Run logs
gcloud run services logs read photo-vault-backend --limit 50

# Access metrics
# GCP Console → Cloud Run → photo-vault-backend → Metrics
```

## Cost Estimation (Monthly)

- Cloud Run: ~$10-20 (pay per request)
- Cloud SQL: ~$15-30
- Cloud Storage: ~$0.50/10GB
- Vision API: ~$1-5
- BigQuery: ~$5-10

**Total: ~$40-70/month**

## Troubleshooting

**Backend won't start**
```bash
docker-compose logs backend
docker-compose up -d --build
```

**Database connection error**
```bash
docker-compose restart postgres
docker-compose logs postgres
```

**Vision API errors**
- Verify GCP credentials
- Check Vision API is enabled in GCP Console
- Verify service account permissions

## Future Enhancements

- Mobile app (React Native)
- Advanced search with embeddings
- Batch image processing
- Collaborative albums
- Image sharing
- Cost optimization recommendations

## Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

Ensure code passes tests and linting before submitting.

## License

MIT License - see LICENSE file

## Author

**Your Name**
- GitHub: [@YOUR_USERNAME](https://github.com/YOUR_USERNAME)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)
- Email: your@email.com

## Support

For issues:
1. Check DEPLOYMENT.md for deployment issues
2. Check CHALLENGES.md for technical solutions
3. Open GitHub Issue with clear description

---

**Built with ❤️ for production and portfolio**

If this project helped you, please star it! ⭐
