# Deployment Guide

Complete instructions for deploying AI Smart Photo Vault to production on Google Cloud Platform.

## Prerequisites

- Google Cloud Project with billing enabled
- gcloud CLI installed and authenticated
- Terraform installed (>= 1.0)
- Docker and Docker Compose
- Firebase project
- GitHub repository with secrets configured

## Step 1: Google Cloud Setup

### 1.1 Create Project

```bash
gcloud projects create photo-vault-prod --name="Photo Vault Production"
gcloud config set project photo-vault-prod
```

### 1.2 Enable Required APIs

```bash
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  vision.googleapis.com \
  aiplatform.googleapis.com \
  bigquery.googleapis.com \
  servicenetworking.googleapis.com \
  container.googleapis.com \
  cloudkms.googleapis.com
```

### 1.3 Set up Firebase

1. Go to Firebase Console
2. Create new project
3. Enable Authentication (Email/Password)
4. Create service account and download JSON key
5. Save to `firebase-credentials.json`

### 1.4 Create Storage Bucket

```bash
gsutil mb -l us-central1 gs://photo-vault-prod-images
gsutil versioning set on gs://photo-vault-prod-images
```

### 1.5 Create Artifact Registry

```bash
gcloud artifacts repositories create photo-vault \
  --repository-format=docker \
  --location=us-central1 \
  --description="Photo Vault Docker images"
```

## Step 2: Database Setup

### 2.1 Create Cloud SQL Instance

```bash
gcloud sql instances create photo-vault-postgres \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --availability-type=REGIONAL \
  --backup
```

### 2.2 Create Database and User

```bash
gcloud sql databases create photo_vault \
  --instance=photo-vault-postgres

gcloud sql users create photo_user \
  --instance=photo-vault-postgres \
  --password=$(openssl rand -base64 32)
```

### 2.3 Get Connection String

```bash
gcloud sql instances describe photo-vault-postgres \
  --format='value(connectionName)'
```

## Step 3: Infrastructure as Code Deployment

### 3.1 Configure Terraform

```bash
cd terraform

# Copy and edit terraform.tfvars
cp terraform.tfvars.example terraform.tfvars
# Edit with your project ID and values
```

### 3.2 Initialize Terraform

```bash
terraform init \
  -backend-config="bucket=YOUR_BUCKET" \
  -backend-config="prefix=photo-vault"
```

### 3.3 Plan and Apply

```bash
# Review changes
terraform plan

# Apply infrastructure
terraform apply
```

This will create:
- Cloud Run service
- Cloud Storage buckets
- BigQuery dataset
- IAM roles and service accounts

## Step 4: CI/CD Setup

### 4.1 Configure GitHub Secrets

Add the following secrets to your GitHub repository:

```
GCP_PROJECT_ID              # Your GCP project ID
WIF_PROVIDER                # Workload Identity Provider
WIF_SERVICE_ACCOUNT         # Service account email
DATABASE_URL                # Cloud SQL connection string
JWT_SECRET_KEY              # Random 64-char secret
DOCKER_REGISTRY             # us-central1-docker.pkg.dev/PROJECT/photo-vault
```

### 4.2 Set up Workload Identity Federation

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions CI/CD"

# Grant necessary roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Set up Workload Identity Federation
# (See Google Cloud documentation for detailed setup)
```

## Step 5: Manual Deployment (Alternative to CI/CD)

### 5.1 Build Backend Image

```bash
# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# Build image
docker build -t us-central1-docker.pkg.dev/PROJECT_ID/photo-vault/api:1.0.0 .

# Push image
docker push us-central1-docker.pkg.dev/PROJECT_ID/photo-vault/api:1.0.0
```

### 5.2 Deploy to Cloud Run

```bash
gcloud run deploy photo-vault-api \
  --image=us-central1-docker.pkg.dev/PROJECT_ID/photo-vault/api:1.0.0 \
  --region=us-central1 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --max-instances=100 \
  --set-env-vars=\
DATABASE_URL=YOUR_DATABASE_URL,\
GCP_PROJECT_ID=PROJECT_ID,\
JWT_SECRET_KEY=YOUR_SECRET_KEY,\
GCS_BUCKET_NAME=photo-vault-prod-images,\
BIGQUERY_DATASET=photo_vault
```

### 5.3 Run Database Migrations

```bash
# Create migration job
gcloud run jobs create photo-vault-migrate \
  --image=us-central1-docker.pkg.dev/PROJECT_ID/photo-vault/api:1.0.0 \
  --set-env-vars=DATABASE_URL=YOUR_DATABASE_URL \
  --command="python,-m,alembic,upgrade,head"

# Run the job
gcloud run jobs execute photo-vault-migrate --region=us-central1
```

### 5.4 Deploy Frontend

```bash
# Build React app
cd frontend
npm install
npm run build

# Upload to Cloud Storage
gsutil -m rsync -r -d build/ gs://PROJECT_ID-photo-vault-frontend/

# Enable public access
gsutil iam ch allUsers:objectViewer gs://PROJECT_ID-photo-vault-frontend
```

## Step 6: Post-Deployment Configuration

### 6.1 Configure Firebase Firewall Rules

In Firebase Console:
1. Go to Authentication > Sign-in method
2. Enable Email/Password
3. Add authorized domains

### 6.2 Set up Cloud Load Balancer (Optional)

```bash
gcloud compute backend-services create photo-vault-backend \
  --global \
  --protocol HTTP2 \
  --health-checks health-check
```

### 6.3 Configure CORS

Update `app/config.py`:
```python
ALLOWED_ORIGINS = [
    "https://your-domain.com",
    "https://www.your-domain.com",
]
```

## Step 7: Monitoring and Logging

### 7.1 Set up Cloud Logging

```bash
# View logs
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=photo-vault-api" \
  --limit 100

# Create log sink
gcloud logging sinks create photo-vault-bigquery \
  bigquery.googleapis.com/projects/PROJECT_ID/datasets/logs \
  --log-filter='resource.type="cloud_run_revision"'
```

### 7.2 Set up Monitoring Alerts

```bash
# Create alert policy for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Photo Vault High Error Rate"
```

### 7.3 Application Performance Monitoring

Enable Cloud Trace:
```python
from google.cloud import trace
trace_client = trace.Client()
```

## Step 8: Security Hardening

### 8.1 Enable VPC Service Controls

```bash
# Create VPC Service Perimeter
gcloud access-context-manager perimeters create photo-vault \
  --resources=projects/PROJECT_ID \
  --restricted-services=storage.googleapis.com
```

### 8.2 Enable Cloud Armor

```bash
gcloud compute security-policies create photo-vault \
  --description="Photo Vault API protection"

# Add rules
gcloud compute security-policies rules create 100 \
  --security-policy photo-vault \
  --action "allow"
```

### 8.3 Secrets Management

```bash
# Create secrets in Secret Manager
echo -n "YOUR_JWT_SECRET" | gcloud secrets create jwt-secret --data-file=-

# Grant access
gcloud secrets add-iam-policy-binding jwt-secret \
  --member=serviceAccount:photo-vault@PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/secretmanager.secretAccessor
```

## Step 9: Backup and Disaster Recovery

### 9.1 Configure Cloud SQL Backups

```bash
gcloud sql backups create \
  --instance=photo-vault-postgres \
  --backup-configuration-start-time=03:00
```

### 9.2 Enable Cross-Region Backup

```bash
gcloud sql instances patch photo-vault-postgres \
  --backup-start-time=03:00 \
  --retained-backups-count=30
```

## Step 10: Cost Optimization

### 10.1 Enable Committed Use Discounts

- 3-year commitment for Cloud SQL
- Reserved instances for compute

### 10.2 Set up Budget Alerts

```bash
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Photo Vault Monthly" \
  --budget-amount=500 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100
```

## Troubleshooting

### Cloud Run Service Won't Start

```bash
# Check logs
gcloud run services describe photo-vault-api \
  --region=us-central1

# View detailed logs
gcloud logging read \
  "resource.type=cloud_run_revision" \
  --limit=50 \
  --format=json
```

### Database Connection Issues

```bash
# Check SQL instance status
gcloud sql instances describe photo-vault-postgres

# Test connection
gcloud sql connect photo-vault-postgres \
  --user=photo_user \
  --database=photo_vault
```

### Permission Denied Errors

```bash
# Check service account permissions
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"
```

## Rollback Procedure

### Rollback Cloud Run Deployment

```bash
# Get previous revision
gcloud run revisions list --service=photo-vault-api

# Route traffic to previous revision
gcloud run services update-traffic photo-vault-api \
  --to-revisions=PREVIOUS_REVISION_ID=100
```

## Next Steps

1. Set up monitoring dashboards
2. Configure alert policies
3. Document runbooks
4. Plan disaster recovery drills
5. Schedule regular backups
6. Review security audits
7. Monitor costs and optimize

## Support

For deployment issues:
- Check Cloud Run logs
- Review IAM permissions
- Verify environment variables
- Test database connectivity
- Check API quotas and limits
