# Cloud Run Deployment Guide

Complete guide to deploy Photo Vault backend to Google Cloud Run.

---

## Prerequisites

- Google Cloud Project (aivaultphotosgcp)
- gcloud CLI installed
- Docker installed
- Service account with permissions
- GitHub repository set up

---

## Option 1: Deploy Using GitHub Actions (Recommended)

GitHub Actions automatically deploys on every push to main branch.

### Setup:

1. Push code to GitHub main branch
2. Workflow automatically:
   - Builds Docker image
   - Pushes to Artifact Registry
   - Deploys to Cloud Run
3. Check Actions tab for status

---

## Option 2: Manual Deployment

### Step 1: Set up authentication

```bash
gcloud auth login
gcloud config set project aivaultphotosgcp
```

### Step 2: Build Docker image

```bash
docker build -t photo-vault-backend:latest ./backend
```

### Step 3: Tag for Artifact Registry

```bash
docker tag photo-vault-backend:latest \
  us-central1-docker.pkg.dev/aivaultphotosgcp/photo-vault/backend:latest
```

### Step 4: Configure Docker authentication

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### Step 5: Push to Artifact Registry

```bash
docker push us-central1-docker.pkg.dev/aivaultphotosgcp/photo-vault/backend:latest
```

### Step 6: Deploy to Cloud Run

```bash
gcloud run deploy photo-vault-backend \
  --image us-central1-docker.pkg.dev/aivaultphotosgcp/photo-vault/backend:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars DATABASE_URL=postgresql://user:pass@host/db \
  --set-env-vars REDIS_URL=redis://host:6379 \
  --set-env-vars GCP_PROJECT_ID=aivaultphotosgcp \
  --set-env-vars GCS_BUCKET=aivaultphotosgcp-images \
  --memory 512Mi \
  --cpu 1 \
  --timeout 300 \
  --service-account photo-vault-app@aivaultphotosgcp.iam.gserviceaccount.com
```

### Step 7: Get the service URL

```bash
gcloud run services describe photo-vault-backend \
  --region us-central1 \
  --format 'value(status.url)'
```

---

## Option 3: Deploy Using Terraform

### Step 1: Initialize Terraform

```bash
cd terraform
terraform init
```

### Step 2: Create terraform.tfvars

Copy `terraform.tfvars.example` to `terraform.tfvars`

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit values if needed

### Step 3: Plan deployment

```bash
terraform plan
```

### Step 4: Apply

```bash
terraform apply
```

This creates:
- Cloud SQL PostgreSQL instance
- Cloud Run service
- Cloud Storage buckets
- BigQuery dataset
- Service accounts and IAM roles
- Artifact Registry

### Step 5: Get outputs

```bash
terraform output cloud_run_url
terraform output database_host
```

---

## Post-Deployment

### 1. Test the API

```bash
curl https://your-cloud-run-url/docs
```

Should show Swagger UI

### 2. Create database tables

Connect to Cloud SQL and run migrations:

```bash
# Option A: Use Cloud Shell
gcloud sql connect photo-vault-postgres

# Option B: Using Python
python backend/app/database.py
```

### 3. Upload service account key

Cloud Run needs access to your firebase-credentials.json

Options:
- Mount from Secret Manager
- Store in Cloud SQL
- Pass via environment variable (base64 encoded)

### 4. Configure database connection

Cloud Run needs Cloud SQL Proxy:

The Terraform template includes this annotation:
```yaml
"run.googleapis.com/cloudsql-instances": "connection-name"
```

### 5. Test endpoints

```bash
# Signup
curl -X POST https://your-cloud-run-url/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"pass123"}'

# List images
curl -X GET https://your-cloud-run-url/api/v1/images/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Monitoring

### View logs

```bash
gcloud run services logs read photo-vault-backend --region us-central1 --limit 50
```

### Check metrics

In GCP Console:
- Cloud Run → photo-vault-backend → Metrics
- See requests, latency, errors

### Set up alerts

In GCP Console:
- Monitoring → Alerting → Create Alert Policy
- Alert when errors > 5%
- Alert when latency > 1s

---

## Scaling

Cloud Run auto-scales based on traffic.

To adjust:

```bash
gcloud run services update photo-vault-backend \
  --region us-central1 \
  --max-instances 100 \
  --min-instances 1 \
  --memory 1Gi \
  --cpu 2
```

---

## Cost Optimization

1. **Use lighter image sizes**
   - Multi-stage Docker builds
   - Alpine base image

2. **Set appropriate resources**
   - Start: 512MB RAM, 1 CPU
   - Scale up only if needed

3. **Set timeout appropriately**
   - Default 300s is fine
   - Reduce if possible

4. **Use spot instances** (if available)
   - Lower cost, less reliable

---

## Rollback

If deployment fails:

```bash
# List revisions
gcloud run revisions list --service photo-vault-backend --region us-central1

# Route traffic to previous revision
gcloud run services update-traffic photo-vault-backend \
  --region us-central1 \
  --to-revisions REVISION_NAME=100
```

---

## Environment-Specific Deployments

### Staging

```bash
gcloud run deploy photo-vault-backend-staging \
  --image YOUR_IMAGE \
  --region us-central1 \
  --set-env-vars ENVIRONMENT=staging
```

### Production

```bash
gcloud run deploy photo-vault-backend \
  --image YOUR_IMAGE \
  --region us-central1 \
  --set-env-vars ENVIRONMENT=production
```

---

## Database Backups

Cloud SQL automatically backs up daily.

Manual backup:

```bash
gcloud sql backups create \
  --instance photo-vault-postgres \
  --description "Pre-deployment backup"
```

---

## Disaster Recovery

### Restore from backup

```bash
gcloud sql backups restore BACKUP_ID \
  --backup-instance photo-vault-postgres
```

### Recreate from Terraform

```bash
terraform destroy
terraform apply
```

---

## Troubleshooting

### Service won't start
- Check logs: `gcloud run services logs read photo-vault-backend`
- Verify environment variables
- Check Cloud SQL connection

### Database connection error
- Verify DATABASE_URL is correct
- Check service account has Cloud SQL Client role
- Ensure Cloud SQL instance is running

### Out of memory
- Increase memory allocation
- Check for memory leaks in code
- Optimize database queries

### Timeout errors
- Increase timeout setting
- Optimize slow endpoints
- Check Vision AI response times

---

## Cleanup

Remove all resources:

```bash
# Using Terraform
terraform destroy

# Or manually
gcloud run services delete photo-vault-backend --region us-central1
gcloud storage buckets delete gs://aivaultphotosgcp-images
gcloud sql instances delete photo-vault-postgres
gcloud bigquery datasets delete photo_vault_analytics
```

---

## Next Steps

1. Set up monitoring and alerts
2. Configure CDN for frontend (Cloud Storage + Cloud CDN)
3. Set up domain name (Cloud DNS)
4. Enable HTTPS (automatic with Cloud Run)
5. Set up automated backups

