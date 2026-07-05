# Interview Questions & Discussion Points

## Architecture & Design

### Q1: Why did you choose this technology stack?

**Key Points:**
- React for responsive, interactive UI with TypeScript for type safety
- FastAPI for rapid development with automatic documentation
- PostgreSQL for relational data integrity
- Google Cloud services for managed, scalable infrastructure
- BigQuery for analytics at scale

**Answer Structure:**
1. Frontend needs real-time responsiveness → React
2. Backend needs fast iteration → FastAPI (automatic Swagger docs)
3. Relational data with complex queries → PostgreSQL
4. AI/ML capabilities built-in → GCP services
5. Serverless for cost efficiency → Cloud Run

### Q2: How does your architecture scale?

**Discussion Points:**
- Cloud Run auto-scales based on request volume
- Database read replicas for high query volume
- Redis caching for hot data
- BigQuery for analytics queries (doesn't impact production DB)
- CDN for frontend assets
- GCS for unlimited file storage

**Diagram They Might Ask For:**
```
Users
  ↓
Cloud Load Balancer
  ↓
Cloud Run (auto-scales 0-100+ instances)
  ↓
Cloud SQL Proxy → PostgreSQL (read replicas)
  ↓
BigQuery (analytics, separate from transactional data)
```

### Q3: How do you handle image uploads and processing?

**Technical Details:**
- Chunk-based upload for large files
- Server-side validation of file type and size
- Async processing with Vision AI
- Metadata stored in PostgreSQL
- Analytics events to BigQuery
- User storage quota tracking

**Code Example Discussion:**
```python
# Upload validation
if file.content_type not in ALLOWED_TYPES:
    raise HTTPException(...)

# Async AI processing
try:
    ai_analysis = vision_ai_service.analyze_image(content)
except Exception:
    # Continue without AI if it fails
    pass
```

## AI/ML Integration

### Q4: How do you handle Vision AI failures?

**Graceful Degradation Strategy:**
- Wrap Vision API calls in try-except
- Allow uploads to complete even if AI fails
- Mark images as "partial processing"
- Retry mechanism for AI analysis
- User notification on partial features

**Code Discussion:**
```python
try:
    ai_analysis = vision_ai_service.analyze_image(content)
    image.caption = ai_analysis.get("caption")
except Exception as e:
    logger.error(f"AI analysis error: {e}")
    image.caption = "Analysis pending"
```

### Q5: How do you prevent duplicate image uploads?

**Approaches:**
1. **Hash-based** (MD5/SHA-256): Fast, deterministic
2. **Perceptual hashing**: Similar images despite compression
3. **ML-based**: Similar vector embeddings

**Current Implementation:**
- File size similarity check
- Tag intersection comparison
- Could upgrade to perceptual hashing with imagehash library

**Discussion:**
```python
# Current simple approach
if (set(img1.tags) & set(img2.tags) and
    abs(img1.file_size_bytes - img2.file_size_bytes) < threshold):
    # Likely duplicate

# Better approach with perceptual hashing
import imagehash
from PIL import Image
hash1 = imagehash.phash(Image.open(image1_path))
hash2 = imagehash.phash(Image.open(image2_path))
if hash1 - hash2 < threshold:
    # Perceptually similar
```

## Database Design

### Q6: Why separate analytics into BigQuery?

**Reasons:**
1. **Transactional DB burden**: Analytics queries can be slow
2. **Separate scale**: Different optimization (OLAP vs OLTP)
3. **Cost**: BigQuery billed on data scanned, not storage
4. **Query power**: Complex aggregations easier in SQL
5. **Historical data**: Long-term retention without impacting production

**Architecture:**
```
PostgreSQL ←→ Application
    ↓ (events table)
    ↓ (scheduled job)
BigQuery ←→ Analytics Dashboard
```

### Q7: How do you handle migrations?

**Strategy:**
- Alembic for schema versioning
- Zero-downtime deployments
- Backward compatibility maintained
- Rollback procedures documented

**Example:**
```bash
# Create migration
alembic revision --autogenerate -m "Add image tags column"

# Review the migration
# Apply to production
alembic upgrade head
```

### Q8: How do you optimize database queries?

**Techniques:**
1. **Indexing**: On frequently filtered columns
```python
Index('idx_image_user_id', 'user_id')
Index('idx_image_created_at', 'created_at')
```

2. **Query Optimization**:
```python
# Bad: N+1 query problem
for image in images:
    tags = db.query(Tag).filter(Tag.image_id == image.id)

# Good: Use eager loading
images = db.query(Image).options(joinedload(Image.tags))
```

3. **Pagination**: Never fetch all records
```python
skip = (page - 1) * page_size
images = db.query(Image).offset(skip).limit(page_size)
```

## API Design

### Q9: How do you structure your API?

**REST Principles:**
- Resource-based URLs: `/api/v1/images/{id}`
- HTTP methods: GET (read), POST (create), DELETE
- Versioning: `/api/v1/` allows future `/api/v2/`
- Pagination: `?page=1&page_size=20`
- Filtering: `?archived=false&tag=vacation`

**Error Handling:**
```python
HTTPException(status_code=400, detail="Invalid file type")
HTTPException(status_code=401, detail="Unauthorized")
HTTPException(status_code=404, detail="Not found")
```

### Q10: How do you handle authentication?

**Flow:**
1. User signs up via Firebase (stores password securely)
2. Backend creates JWT token with user ID as subject
3. Token sent in Authorization header for subsequent requests
4. Backend validates JWT token before serving protected resources

**Code:**
```python
def get_current_user(authorization: str = Header(None)):
    token = authorization.split()[1]  # "Bearer <token>"
    payload = jwt_service.verify_access_token(token)
    user_id = payload.get("sub")
    return db.query(User).filter(User.id == user_id).first()
```

**Security:**
- JWT signed with secret key
- 24-hour expiration
- Refresh token endpoint for extension
- Logout via client-side token deletion

## Frontend Development

### Q11: How do you structure the React application?

**Components:**
- **Container components**: Handle logic
- **Presentational components**: Display only
- **Hooks**: Custom hooks for reusable logic
- **Context**: Global state (auth, user)
- **Services**: API calls

**Structure:**
```
frontend/
├── src/
│   ├── components/
│   │   ├── Auth/
│   │   ├── Gallery/
│   │   ├── Search/
│   │   └── Admin/
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useImages.ts
│   │   └── useSearch.ts
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   │   └── index.ts
│   └── App.tsx
```

### Q12: How do you handle state management?

**Options Discussed:**
1. **Context API**: Simple, built-in
2. **Redux**: Overkill for this project
3. **Zustand**: Good middle ground (lightweight)
4. **Recoil**: Atomic state

**Chosen: Zustand**
```typescript
// Lightweight, minimal boilerplate
interface AuthStore {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  login: async (email, password) => {
    const response = await api.post('/auth/login', {email, password})
    set({ user: response.user, token: response.token })
  },
  logout: () => set({ user: null, token: null }),
}))
```

## Testing & Quality

### Q13: How do you approach testing?

**Testing Strategy:**
1. **Unit Tests**: Individual functions
```python
def test_detect_labels():
    service = VisionAIService(project_id)
    labels = service.detect_labels(image_content)
    assert len(labels) > 0
```

2. **Integration Tests**: API endpoints
```python
def test_upload_image(client):
    response = client.post(
        "/api/v1/images/upload",
        files={"file": ("test.jpg", image_data)},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

3. **End-to-End Tests**: Full workflows

### Q14: How do you handle errors?

**Comprehensive Error Handling:**
```python
try:
    # Operation
except HTTPException:
    raise  # Re-raise HTTP errors
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="DB error")
except GoogleAPICallError as e:
    logger.error(f"GCP error: {e}")
    # Graceful degradation
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal error")
```

## Deployment & DevOps

### Q15: How do you handle deployments?

**CI/CD Pipeline:**
1. Push to main branch
2. GitHub Actions runs tests
3. Build Docker image
4. Push to Artifact Registry
5. Deploy to Cloud Run
6. Run database migrations
7. Deploy frontend to Storage

**Benefits:**
- Automated testing before deploy
- Zero-downtime deployments
- Rollback capability
- Audit trail

### Q16: How do you monitor production?

**Monitoring Stack:**
- Cloud Logging: Centralized logs
- Cloud Trace: Distributed tracing
- Cloud Monitoring: Metrics & alerts
- Error Reporting: Automatic error aggregation
- BigQuery: Analytics and diagnostics

**Key Metrics:**
- API latency (p50, p95, p99)
- Error rate and error types
- Database connection pool utilization
- Storage growth rate
- User activity patterns

### Q17: How do you handle secrets?

**Secrets Management:**
1. Environment variables for local dev
2. Terraform secrets for infrastructure
3. Google Secret Manager for production
4. Never commit secrets to Git

```terraform
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "jwt-secret"
}

# Service account can access
resource "google_secret_manager_secret_iam_member" "jwt_secret_accessor" {
  secret_id = google_secret_manager_secret.jwt_secret.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.cloud_run.email}"
}
```

## Product & Business Questions

### Q18: What would you add next?

**Priority Features:**
1. **Collaborative Albums**: Share with other users
2. **Advanced Permissions**: Granular access control
3. **Mobile App**: React Native
4. **Photo Editing**: In-browser editing
5. **Social Features**: Comments, likes
6. **Advanced ML**: Custom object detection

### Q19: How would you handle a viral spike?

**Scaling Strategy:**
1. Cloud Run auto-scales automatically (no manual intervention needed)
2. Database read replicas handle query load
3. Redis caching reduces DB hits
4. BigQuery handles analytics separately
5. CDN caches frontend assets
6. Could implement request queuing if needed

### Q20: How would you reduce costs?

**Cost Optimization:**
1. Use preemptible VMs for batch jobs
2. Committed Use Discounts for Cloud SQL
3. Archive old images to cold storage
4. Compress images on upload
5. Implement intelligent caching
6. Monitor BigQuery costs (can be expensive!)

## Behavioral Questions

### Q21: Tell me about a challenge you faced

**Story Structure:**
1. **Situation**: "Implementing duplicate detection was tricky"
2. **Task**: "Needed fast, accurate comparison of thousands of images"
3. **Action**: "Started with simple file size comparison, then added tag intersection, considered perceptual hashing"
4. **Result**: "Achieved 95% accuracy with minimal overhead"

### Q22: How do you stay updated with tech?

**Genuine Answers:**
- Follow GitHub trends
- Read technical blogs
- Contribute to open source
- Build side projects
- Attend tech conferences/meetups

### Q23: What did you learn building this?

**Real Learning Outcomes:**
- AI/ML integration with Cloud Vision
- Serverless architecture considerations
- Database optimization techniques
- CI/CD best practices
- Full-stack thinking (backend, frontend, infrastructure)
