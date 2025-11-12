# Satellite-Based Disaster Early Warning System
## Google Colab + Jenkins Hybrid MLOps Architecture

### 🎯 Overview
Self-adaptive disaster detection system using:
- **Google Colab**: Free GPU training (TensorFlow/PyTorch)
- **Google Earth Engine**: Free satellite imagery access
- **Local Jenkins**: CI/CD automation & orchestration
- **FastAPI**: CPU-based inference API
- **Evidently AI**: Data drift detection
- **Google Drive**: Model storage and persistence

This hybrid architecture eliminates the need for local CUDA/GPU while maintaining full MLOps automation.

---

### 📋 Prerequisites

1. **Google Earth Engine Account**
   - Register at https://earthengine.google.com/
   - Create GCP project and enable Earth Engine API
   - Generate service account JSON credentials

2. **Google Drive API Setup**
   - Enable Google Drive API in GCP Console
   - Create OAuth 2.0 credentials (Desktop App)
   - Download credentials JSON

3. **Local Environment**
   - Docker & Docker Compose installed
   - Python 3.9+
   - Git

---

### 🚀 Quick Start

#### Step 1: Clone and Setup Environment

```powershell
# Navigate to project directory
cd c:\Docs\project\DevOps

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Notepad .env
```

#### Step 2: Authenticate Google Services

```powershell
# Install Python dependencies
pip install -r requirements.txt

# Run authentication script (opens browser)
python scripts/setup_colab_auth.py

# This generates token.pickle for Drive API access
```

Place your Google credentials:
- `service-account-key.json` → Root directory (from GEE)
- `google-drive-credentials.json` → Root directory (from GCP)

#### Step 3: Start Services

```powershell
# Build and start all containers
docker-compose up -d

# Check container status
docker-compose ps

# View logs
docker-compose logs -f detection-api
```

#### Step 4: Access Services

- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Jenkins Dashboard**: http://localhost:8080
- **Health Check**: http://localhost:8000/health

---

### 📊 System Architecture

```
┌─────────────────────┐
│ Google Earth Engine │ (Free satellite data)
│    Sentinel-1/2     │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Colab Notebooks    │ (GPU Training - FREE)
│  - Flood Model      │
│  - Fire Model       │
│  - Auto-Retraining  │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   Google Drive      │ (Model Storage)
│   - Trained Models  │
│   - Metrics/Logs    │
│   - Baseline Data   │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│      Jenkins        │ (MLOps Automation)
│  - Drift Detection  │
│  - Trigger Training │
│  - Model Deployment │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│    FastAPI Server   │ (CPU Inference)
│  - Flood Prediction │
│  - Fire Prediction  │
│  - Model Management │
└─────────────────────┘
```

---

### 🧪 Testing the System

#### Test API Health

```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "models_loaded": ["flood", "fire"],
  "timestamp": "2025-11-10T12:00:00"
}
```

#### Test Flood Prediction

```powershell
# Upload a SAR image for flood detection
curl -X POST http://localhost:8000/predict/flood `
  -F "image=@test_data/sample_sar.tif"
```

#### Test Fire Prediction

```powershell
# Upload an optical image for fire detection
curl -X POST http://localhost:8000/predict/fire `
  -F "image=@test_data/sample_optical.tif"
```

#### Trigger Manual Retraining

```powershell
# Via Jenkins API (replace with your token)
curl -X POST http://localhost:8080/job/disaster_model_retraining/buildWithParameters `
  --user admin:YOUR_JENKINS_TOKEN `
  --data "MODEL_TYPE=flood"
```

---

### 📁 Project Structure

```
disaster-detection-system/
├── colab_notebooks/          # Google Colab notebooks (GPU training)
│   ├── 01_data_exploration.ipynb
│   ├── 02_flood_model_training.ipynb
│   ├── 03_fire_model_training.ipynb
│   ├── 04_automated_retraining.ipynb
│   └── utils/
│       ├── colab_helpers.py
│       └── drive_manager.py
├── data/
│   ├── raw/                  # Local cache (optional)
│   ├── processed/
│   ├── baseline/             # Drift detection baseline
│   └── production_samples.csv
├── models/
│   ├── architectures/        # Model definitions
│   │   ├── flood_model.py
│   │   └── fire_model.py
│   ├── configs/              # Training configs
│   └── saved_models/         # Downloaded from Drive
│       ├── flood/
│       └── fire/
├── src/
│   ├── api/                  # FastAPI inference server
│   │   ├── __init__.py
│   │   ├── inference_api.py
│   │   └── model_loader.py
│   ├── colab_integration/    # Drive sync & Colab triggers
│   │   ├── __init__.py
│   │   ├── colab_trigger.py
│   │   ├── drive_sync.py
│   │   └── notebook_runner.py
│   ├── data_ingestion/       # GEE data download
│   │   ├── __init__.py
│   │   ├── gee_downloader.py
│   │   └── data_preprocessor.py
│   ├── drift_detection/      # Evidently AI drift monitor
│   │   ├── __init__.py
│   │   └── drift_monitor.py
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── scripts/
│   ├── setup_colab_auth.py   # Google OAuth setup
│   ├── download_from_drive.py
│   └── trigger_training.py
├── docker/
│   ├── Dockerfile.api        # FastAPI container
│   ├── Dockerfile.drift      # Drift monitor container
│   └── Dockerfile.jenkins    # Jenkins with Docker
├── jenkins/
│   └── Jenkinsfile           # MLOps pipeline
├── logs/                     # Drift reports, training logs
├── tests/
├── .env.example              # Environment template
├── .gitignore
├── docker-compose.yml
├── requirements.txt          # Local dependencies
├── requirements_colab.txt    # Colab notebook dependencies
└── README.md
```

---

### 🔄 MLOps Pipeline Workflow

1. **Production Inference**: API receives satellite images and makes predictions
2. **Feature Extraction**: System extracts statistical features from each image
3. **Drift Detection**: Evidently AI compares production data vs baseline (every 6 hours)
4. **Trigger Retraining**: If drift > threshold, Jenkins pipeline activates
5. **Data Download**: Fresh satellite data pulled from Google Earth Engine
6. **Colab Training**: Notebook triggered on Colab (free GPU)
7. **Model Upload**: Trained model saved to Google Drive
8. **Model Sync**: Jenkins downloads new model from Drive
9. **Validation**: New model performance compared to previous
10. **Deployment**: API reloaded with updated model
11. **Baseline Update**: Drift detection baseline refreshed

---

### 📈 Monitoring & Logs

**Drift Reports**
```powershell
# View recent drift detection results
ls logs/drift_report_*.json | sort -Descending | select -First 1 | cat
```

**Training Metrics**
- Stored in Google Drive: `disaster_detection/logs/`
- Local cache: `./logs/training_*.json`

**Jenkins Job History**
- Access at: http://localhost:8080/job/disaster_model_retraining/

**API Logs**
```powershell
docker-compose logs -f detection-api
```

---

### 🛠️ Configuration

#### Environment Variables (`.env`)

Key variables to configure:

```env
# Google Earth Engine
GEE_SERVICE_ACCOUNT=your-sa@project.iam.gserviceaccount.com
GEE_PROJECT_ID=your-gcp-project-id

# Google Drive
DRIVE_FOLDER_ID=your-google-drive-folder-id
DRIVE_MODEL_FOLDER=disaster_detection/models

# Colab Notebooks (Drive file IDs)
COLAB_NOTEBOOK_FLOOD=1abc...xyz
COLAB_NOTEBOOK_FIRE=1def...xyz

# Drift Detection
DRIFT_THRESHOLD=0.5
DRIFT_CHECK_INTERVAL_HOURS=24

# Jenkins
JENKINS_URL=http://localhost:8080
JENKINS_USER=admin
JENKINS_TOKEN=your-api-token
```

---

### 🎓 Academic Features

**Why This Architecture?**

1. **Cost-Effective**: 100% free tier usage
   - Colab: Free GPU for training
   - GEE: 10,000+ free satellite images
   - Drive: 15GB free storage

2. **Production-Ready MLOps**
   - Automated CI/CD with Jenkins
   - Drift detection & auto-retraining
   - Containerized microservices
   - RESTful API with FastAPI

3. **Scalable Design**
   - Add new disaster types easily
   - Horizontal scaling with Docker
   - Cloud deployment ready

4. **Academic Rigor**
   - U-Net architecture for segmentation
   - Statistical drift detection
   - Performance metrics tracking
   - Reproducible experiments

---

### 🐛 Troubleshooting

**Issue**: API returns "Models not loaded"
```powershell
# Check if models exist in Drive
python -c "from src.colab_integration.drive_sync import DriveModelSync; DriveModelSync().list_models('flood')"

# Manually sync models
python -c "from src.colab_integration.drive_sync import DriveModelSync; DriveModelSync().sync_models()"
```

**Issue**: Jenkins can't trigger Colab
- Ensure `COLAB_NOTEBOOK_FLOOD` and `COLAB_NOTEBOOK_FIRE` are set to valid Drive file IDs
- Check `token.pickle` exists and is valid

**Issue**: Drift detection fails
- Ensure baseline CSV exists: `./data/baseline/flood_baseline_features.csv`
- Generate baseline by running training notebook Cell 7

---

### 📚 Next Steps

1. **Train Initial Models**: Upload and run Colab notebooks to create first models
2. **Generate Baseline**: Run baseline generation cell to create drift reference
3. **Configure Jenkins**: Set up credentials and test pipeline
4. **Deploy Production**: Start collecting real satellite imagery
5. **Monitor Performance**: Track predictions and drift metrics

---

### 🤝 Contributing

This is a final year project demonstrating hybrid cloud-local MLOps.

**Areas for Extension**:
- Additional disaster types (earthquake, landslide)
- Multi-temporal analysis
- Real-time alerting system
- Mobile app integration
- GIS visualization dashboard

---

### 📄 License

MIT License - See LICENSE file for details

---

### 📞 Support

For questions or issues:
1. Check logs: `docker-compose logs`
2. Review Colab notebook outputs in Drive
3. Consult Jenkins build console

---

**Built with ❤️ using Google Colab, Jenkins, FastAPI, and Earth Engine**
