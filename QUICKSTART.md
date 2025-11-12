# Disaster Detection System - Quick Start Guide

## 🎯 Overview

This hybrid Colab + Jenkins system provides:
- **Free GPU training** on Google Colab
- **Automated MLOps** with Jenkins
- **Production API** for real-time inference
- **Drift detection** and auto-retraining

---

## ⚡ Quick Setup (5 Steps)

### Step 1: Install Dependencies

```powershell
# Navigate to project
cd c:\Docs\project\DevOps

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Get Google Credentials

You need two credential files:

**A. Earth Engine Service Account**
1. Go to https://console.cloud.google.com/
2. Create/select project
3. Enable Earth Engine API
4. Create Service Account
5. Download JSON key → save as `service-account-key.json`

**B. Google Drive OAuth**
1. In same GCP project
2. Enable Google Drive API
3. Create OAuth 2.0 Client (Desktop App)
4. Download credentials → save as `google-drive-credentials.json`

### Step 3: Run Authentication Script

```powershell
python scripts\setup_colab_auth.py
```

This will:
- Open browser for Google authentication
- Generate `token.pickle` for Drive access
- Create directory structure
- Verify credentials

### Step 4: Configure Environment

```powershell
# .env already created from .env.example
# Edit with your actual values
notepad .env
```

**Required values:**
```env
GEE_SERVICE_ACCOUNT=your-sa@project.iam.gserviceaccount.com
GEE_PROJECT_ID=your-project-id
DRIVE_FOLDER_ID=your-drive-folder-id
```

### Step 5: Start Services

```powershell
# Build and start all containers
docker-compose up -d

# Check status
docker-compose ps

# View API logs
docker-compose logs -f detection-api
```

**Access points:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Jenkins: http://localhost:8080

---

## 🧪 Testing

### Test API Health

```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "models_loaded": ["flood", "fire"],
  "timestamp": "2025-11-10T..."
}
```

### Test Prediction (with sample image)

```powershell
# Create test directory
mkdir test_data

# Test flood prediction
curl -X POST http://localhost:8000/predict/flood `
  -F "image=@test_data/sample.tif"
```

---

## 📊 Next Steps

### 1. Upload Colab Notebooks

- Upload notebooks from `colab_notebooks/` to Google Drive
- Note the Drive file IDs
- Add to `.env`:
  ```env
  COLAB_NOTEBOOK_FLOOD=1abc...xyz
  COLAB_NOTEBOOK_FIRE=1def...xyz
  ```

### 2. Train Initial Models

- Open flood training notebook in Colab
- Run all cells to train first model
- Model will be saved to Drive
- Baseline features generated

### 3. Sync Models to Local

```powershell
# Manual sync (or wait for API startup)
python -c "from src.colab_integration.drive_sync import DriveModelSync; DriveModelSync().sync_models()"
```

### 4. Configure Jenkins

- Access Jenkins at http://localhost:8080
- Create pipeline job
- Point to `jenkins/Jenkinsfile`
- Add credentials for Docker Hub (optional)

---

## 🔧 Troubleshooting

### Issue: "Models not loaded"

**Solution:**
```powershell
# Check if models exist in Drive
python -c "from src.colab_integration.drive_sync import DriveModelSync; print(DriveModelSync().list_models('flood'))"

# Force reload
curl -X POST http://localhost:8000/models/reload
```

### Issue: "Drive authentication failed"

**Solution:**
```powershell
# Re-run authentication
python scripts\setup_colab_auth.py

# Check token exists
ls token.pickle
```

### Issue: Docker build fails

**Solution:**
```powershell
# Check Docker is running
docker --version

# Rebuild with no cache
docker-compose build --no-cache

# Check logs
docker-compose logs
```

---

## 📁 Important Files

- **`.env`** - Your credentials (DO NOT commit!)
- **`token.pickle`** - Drive API token (DO NOT commit!)
- **`service-account-key.json`** - GEE credentials (DO NOT commit!)
- **`requirements.txt`** - Python dependencies
- **`docker-compose.yml`** - Service orchestration

---

## 🚀 Production Workflow

```
1. New satellite imagery arrives
   ↓
2. API makes predictions
   ↓
3. Drift monitor checks data distribution (every 6 hours)
   ↓
4. If drift detected → Trigger Jenkins
   ↓
5. Jenkins downloads new data from GEE
   ↓
6. Jenkins triggers Colab notebook (GPU training)
   ↓
7. New model saved to Drive
   ↓
8. Jenkins downloads model
   ↓
9. API reloaded with new model
   ↓
10. Updated baseline for drift detection
```

---

## 📚 Resources

- **FastAPI Docs**: http://localhost:8000/docs
- **Google Earth Engine**: https://earthengine.google.com/
- **Colab**: https://colab.research.google.com/
- **Jenkins**: http://localhost:8080

---

## 🤝 Support

If you encounter issues:

1. Check logs: `docker-compose logs -f`
2. Verify credentials in `.env`
3. Ensure Google APIs are enabled
4. Check Drive folder permissions

---

**Ready to detect disasters! 🌍🛰️**
