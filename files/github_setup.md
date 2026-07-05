# GitHub Setup Guide for Photo Vault

Complete step-by-step guide to upload your project to GitHub and enable CI/CD.

---

## STEP 1: Create GitHub Repository

1. Go to: https://github.com/new
2. Enter:
   - Repository name: `photo-vault`
   - Description: "AI-powered photo management platform with Vision AI integration"
   - Public: Yes (for portfolio)
   - Add README: No (we'll create custom one)
   - Add .gitignore: Python
3. Click "Create repository"

---

## STEP 2: Initialize Local Git

Open Command Prompt in your project folder:

```bash
cd C:\Google project GCP\ai-smart-photo-vault\ai-smart-photo-vault

git init
git config user.name "Your Name"
git config user.email "your@email.com"
git add .
git commit -m "Initial commit: Photo Vault full-stack application"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/photo-vault.git
git push -u origin main
```

---

## STEP 3: Create .gitignore File

Create file: `.gitignore` in project root

Content:
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
.pytest_cache/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
Thumbs.db

# Environment
.env
.env.local
.env.*.local
firebase-credentials.json

# Node
node_modules/
npm-debug.log
yarn-error.log

# Docker
.docker/

# Terraform
terraform.tfvars
.terraform/
.terraform.lock.hcl
*.tfstate
*.tfstate.*

# Logs
*.log
logs/
```

---

## STEP 4: Create GitHub Workflows Folder

Create folder structure:
```
.github/
  workflows/
    deploy.yml
    test.yml
    lint.yml
```

Copy the workflow files into `.github/workflows/`

---

## STEP 5: Create Comprehensive README

Create: `README.md` (in project root)

---

## STEP 6: Create DEPLOYMENT Guide

Create: `DEPLOYMENT.md` with Cloud Run instructions

---

## STEP 7: Set Up GitHub Secrets

These are needed for CI/CD to work.

1. Go to your GitHub repo
2. Click Settings → Secrets and variables → Actions
3. Click "New repository secret"

Add these secrets:

### For Cloud Run Deployment:
- `GCP_PROJECT_ID`: aivaultphotosgcp
- `GCS_BUCKET`: aivaultphotosgcp-images
- `DATABASE_URL`: postgresql://user:pass@hostname/database
- `REDIS_URL`: redis://hostname:6379
- `CLOUD_RUN_SERVICE_ACCOUNT`: photo-vault-app@aivaultphotosgcp.iam.gserviceaccount.com

### For Workload Identity (Optional but recommended):
- `WIF_PROVIDER`: (from Google Cloud setup)
- `WIF_SERVICE_ACCOUNT`: (from Google Cloud setup)

---

## STEP 8: Google Cloud Authentication

Set up GitHub to authenticate with Google Cloud:

```bash
# In Google Cloud Console:
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

gcloud iam service-accounts add-iam-policy-binding \
  github-actions@aivaultphotosgcp.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "principalSet://iam.googleapis.com/projects/YOUR_PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/YOUR_USERNAME/photo-vault"
```

---

## STEP 9: Push Workflow Files

```bash
git add .github/
git commit -m "Add CI/CD workflows (deploy, test, lint)"
git push origin main
```

---

## STEP 10: Test Deployment

1. Go to GitHub repo → Actions tab
2. You should see workflows running
3. Click on a workflow to see logs
4. Check if deployment succeeded

---

## STEP 11: Add Project Topics

Go to repo Settings → About

Add Topics:
- python
- fastapi
- gcp
- cloud-run
- vision-api
- docker
- terraform
- ci-cd

---

## File Structure (Final)

```
photo-vault/
├── .github/
│   └── workflows/
│       ├── deploy.yml
│       ├── test.yml
│       └── lint.yml
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── config.py
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── index.html
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── terraform.tfvars.example
├── docker-compose.yml
├── Dockerfile
├── README.md
├── DEPLOYMENT.md
├── CHALLENGES.md
└── firebase-credentials.json (in .gitignore)
```

---

## Common Git Commands

```bash
# See changes
git status

# Add specific file
git add filename

# Add all changes
git add .

# Commit
git commit -m "Description of changes"

# Push to GitHub
git push origin main

# Pull latest
git pull origin main

# Create new branch
git checkout -b feature-name

# Switch branch
git checkout main

# Delete branch
git branch -d feature-name
```

---

## Troubleshooting

### "fatal: could not read Username"
- Use GitHub token instead of password
- Create at: https://github.com/settings/tokens

### Workflow not running
- Check `.github/workflows/` folder exists
- Verify YAML syntax (check Actions tab for errors)
- Ensure branch is `main` (not `master`)

### Deployment fails
- Check GitHub Secrets are set correctly
- Verify Google Cloud permissions
- Check Cloud Run logs in GCP Console

---

## Next Steps

1. Push to GitHub: `git push origin main`
2. Watch Actions tab for workflow execution
3. Share GitHub link on LinkedIn
4. Add to resume
5. Apply to jobs with GitHub link

---

## GitHub Link Format

After setup, your repo will be at:
```
https://github.com/YOUR_USERNAME/photo-vault
```

Share this on:
- LinkedIn profile
- Resume portfolio section
- Job applications
- Portfolio website
