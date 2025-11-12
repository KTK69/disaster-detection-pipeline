# 🧪 How to Test Automated Retraining

## Overview

The disaster detection pipeline currently has **two retraining mechanisms**:

1. **Manual Retraining** (via Google Colab)
2. **Drift-Triggered Retraining** (via Jenkins + Drift Detection)

This guide shows you how to test if both are working.

---

## ✅ Test 1: Check Current Retraining Setup

### **Step 1: Review Jenkinsfile Pipeline Stages**

```powershell
# View the Jenkins pipeline
cat Jenkinsfile
```

**What to look for:**
- Stage: `📊 Check Model Performance` → Validates model accuracy
- Stage: `🔍 Drift Detection` → Checks for data drift
- Stage: `🐳 Build Docker Image` → Rebuilds if changes detected
- Stage: `🚀 Deploy` → Deploys updated model

**Current Status**: ✅ Pipeline has model validation

---

## 🔄 Test 2: Trigger a Manual Retraining Test

### **Method A: Via Google Colab (Full Training)**

1. **Open the Training Notebook**
   ```
   Open: colab_notebooks/02_flood_model_training.ipynb
   ```

2. **Run all cells in sequence**
   - Cell 1: Setup & imports
   - Cell 2: Load Sentinel-1 SAR data from Earth Engine
   - Cell 3: Preprocess data
   - Cell 4: Build U-Net model
   - Cell 5: Train model
   - Cell 6: Evaluate and save

3. **Expected Output**
   ```
   Epoch 21/50: loss=0.15, val_loss=0.18
   ✅ Model training complete!
   📊 Validation Accuracy: 96.71%
   💾 Model saved to: vizag_flood_model_TIMESTAMP.keras
   ```

4. **New Model Saved**
   - Location: `models/saved_models/flood/vizag_flood_model_YYYYMMDD_HHMMSS.keras`
   - Automatically synced to Google Drive

### **Method B: Via Jenkins Build (Deployment Only)**

1. **Trigger Jenkins Build**
   ```
   Visit: http://localhost:8080/job/disaster-detection-pipeline
   Click: "Build Now"
   ```

2. **Monitor Build Progress**
   - Check build console
   - Should complete in ~3-5 minutes

3. **Expected Stages**
   ```
   ✅ 🔍 Checkout - Pull code from GitHub
   ✅ 🧪 Environment - Verify Python
   ⚠️ 📥 Sync Models - Attempt Drive sync
   ✅ 🐳 Build Docker - Build new image
   ✅ 🚀 Deploy - Run container
   ✅ ✅ Health Check - Verify API
   ```

---

## 📊 Test 3: Verify Model Performance Tracking

### **Step 1: Check Model Metadata**

```powershell
# View model info via API
curl http://localhost:8000/models/info

# Expected response:
# {
#   "flood": {
#     "model_name": "vizag_flood_model_20251112_074534",
#     "version": "1.0",
#     "accuracy": 0.9671,
#     "iou": 0.4095,
#     "last_updated": "2025-11-12T14:13:58"
#   }
# }
```

### **Step 2: Check Model File Metadata**

```powershell
# List models by creation time (newest first)
Get-ChildItem C:\Docs\project\DevOps\models\saved_models\flood\ -Filter "*.keras" | Sort-Object LastWriteTime -Descending | Select-Object Name, LastWriteTime, Length

# Example output:
# vizag_flood_model_20251112_074534.keras (118 MB, latest)
# vizag_flood_model_20251111_123456.keras (116 MB, previous)
```

### **Step 3: Check Validation Metrics**

```powershell
# Look for metadata JSON file
Get-ChildItem C:\Docs\project\DevOps\models\saved_models\flood\ -Filter "*.json"

# View metadata
cat .\models\saved_models\flood\model_metadata_20251112_074534.json
```

---

## 🚨 Test 4: Trigger Drift Detection (Optional)

### **Step 1: Create Baseline Data**

```powershell
# Create baseline from current model predictions
python scripts/create_baseline.py

# Expected output:
# ✅ Baseline created: data/baseline/
# ✅ Reference metrics saved
# 📊 Drift threshold: 0.5
```

### **Step 2: Simulate New Data**

```powershell
# Copy test imagery to data/retraining/ directory
# (This simulates new inference data collected in production)
cp test_images/*.tif data/retraining/
```

### **Step 3: Run Drift Monitor**

```powershell
# Check for drift in new data
python src/drift_detection/drift_monitor.py

# Expected output:
# 📊 Checking for drift...
# ✅ Drift Status: NO_DRIFT (score: 0.23)
# or
# ⚠️ Drift Detected! (score: 0.67) → Trigger Retrain
```

---

## 🔍 Test 5: Verify Automated Retraining Trigger

### **Scenario: Drift Detected → Auto-Retrain**

**Step 1: Manually Trigger Drift Alert**

```powershell
# Simulate drift detection by creating a trigger file
New-Item -Path "data/drift_alert.txt" -Value "drift_detected" -Force

# This would normally trigger Jenkins to retrain
```

**Step 2: Check Jenkins Logs**

```
Visit: http://localhost:8080/job/disaster-detection-pipeline
Look for: New build triggered by drift alert
```

**Step 3: Verify Model Updated**

```powershell
# Check if new model was created
Get-ChildItem C:\Docs\project\DevOps\models\saved_models\flood\ -Filter "*.keras" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

---

## 📋 Test Checklist

### **Quick Test (5 minutes)**

- [ ] Run: `curl http://localhost:8000/health` → ✅ Responds
- [ ] Run: `curl http://localhost:8000/models/info` → ✅ Shows model
- [ ] Visit: http://localhost:8080 → ✅ Jenkins accessible
- [ ] Check: Latest build status → ✅ Build #4 successful

### **Full Retraining Test (30 minutes)**

- [ ] Open Colab notebook: `02_flood_model_training.ipynb`
- [ ] Run all training cells
- [ ] Verify new model created in `models/saved_models/flood/`
- [ ] Check new model filename (should have new timestamp)
- [ ] Verify model synced to Google Drive

### **Drift Monitoring Test (optional)**

- [ ] Run: `python scripts/create_baseline.py`
- [ ] Check: `data/baseline/` directory created
- [ ] Run drift monitor: `python src/drift_detection/drift_monitor.py`
- [ ] Verify drift metrics logged

### **CI/CD Pipeline Test (5 minutes)**

- [ ] Visit: http://localhost:8080/job/disaster-detection-pipeline
- [ ] Click: "Build Now"
- [ ] Monitor: Build console output
- [ ] Verify: Build #N completes successfully
- [ ] Check: API still responding at http://localhost:8000/health

---

## 🎯 Success Criteria

### **✅ Automated Retraining IS Working If:**

1. **Model Validation Stage**
   - Jenkinsfile checks model accuracy ✅
   - Build fails if accuracy drops below threshold ✅

2. **Model Sync**
   - New trained models sync from Google Drive ✅
   - Latest model is deployed ✅

3. **Docker Deployment**
   - New model is copied into Docker image ✅
   - API serves the latest model version ✅

4. **Health Checks**
   - API health check passes after deployment ✅
   - Model info endpoint shows current version ✅

5. **Build Consistency**
   - Jenkins builds complete successfully ✅
   - Build logs show all 9 stages executing ✅

### **❌ Issues to Watch For:**

- Build fails at "Sync Models from Drive" → Credentials missing
- Build fails at "Environment Setup" → Python not found
- Build fails at "Health Check" → Previous container blocking port
- Model files not in Docker image → Volume mount issue
- API returns wrong model version → Cache not cleared

---

## 🔧 Troubleshooting Retraining

### **Issue: Build Fails at Model Validation**

```powershell
# Check model metadata file exists
Test-Path .\models\saved_models\flood\model_metadata_*.json

# View model accuracy
cat .\models\saved_models\flood\model_metadata_*.json | findstr "accuracy"

# If missing, update Jenkinsfile to skip validation
```

### **Issue: Model Not Updating After Retraining**

```powershell
# Check if new model file was created
Get-ChildItem .\models\saved_models\flood\ -Filter "*.keras" | Sort-Object LastWriteTime -Descending | Select-Object -First 3

# If old model still being used, clear Docker cache
docker-compose down
docker image prune -f
docker-compose up -d detection-api
```

### **Issue: Drift Detection Not Triggering**

```powershell
# Verify baseline exists
Test-Path .\data\baseline\

# If not, create it
python scripts/create_baseline.py

# Check drift monitor script
cat src/drift_detection/drift_monitor.py
```

---

## 📊 Monitoring Commands

### **Check Current Model Info**

```powershell
# Via API
curl http://localhost:8000/models/info

# Via filesystem
$latestModel = Get-ChildItem .\models\saved_models\flood\ -Filter "*.keras" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Write-Host "Latest Model: $($latestModel.Name)"
Write-Host "Size: $($latestModel.Length) bytes"
Write-Host "Created: $($latestModel.LastWriteTime)"
```

### **Track Retraining History**

```powershell
# List all trained models by date
Get-ChildItem .\models\saved_models\flood\ -Filter "*.keras" | Sort-Object LastWriteTime -Descending | ForEach-Object {
    Write-Host "$($_.Name) - $($_.LastWriteTime)"
}
```

### **Monitor Jenkins Builds**

```powershell
# View build history
curl http://localhost:8080/job/disaster-detection-pipeline/api/json | ConvertFrom-Json | Select-Object -ExpandProperty builds | Select-Object number, result

# View specific build console
curl http://localhost:8080/job/disaster-detection-pipeline/4/consoleText
```

---

## 🎓 How Automated Retraining Works

```
┌─────────────────────────────────────────────────────┐
│          AUTOMATED RETRAINING WORKFLOW              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Manual Training in Colab                       │
│     └─ Train new model on fresh data               │
│     └─ Save to models/saved_models/flood/          │
│     └─ Sync to Google Drive                        │
│                                                     │
│  2. GitHub Push Trigger                            │
│     └─ Commit code changes                         │
│     └─ Push to main branch                         │
│     └─ Webhook notifies Jenkins                    │
│                                                     │
│  3. Jenkins Pipeline Execution                     │
│     └─ Checkout latest code                        │
│     └─ Sync latest models from Drive               │
│     └─ Validate model performance                  │
│     └─ Check for data drift                        │
│     └─ Build Docker image with new model           │
│     └─ Deploy to http://localhost:8000             │
│     └─ Health check API endpoints                  │
│                                                     │
│  4. API Live with New Model                        │
│     └─ Predictions use latest trained model        │
│     └─ Metrics logged for drift monitoring         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 📝 Test Report Template

Use this to document your retraining tests:

```
TEST: Automated Retraining Verification
DATE: __________
TESTER: __________

1. Model Validation
   - Jenkinsfile checks accuracy? [YES/NO]
   - Current model accuracy: _____%
   - Threshold: 85%
   - Status: [PASS/FAIL]

2. Model Deployment
   - New model deployed? [YES/NO]
   - API returns latest model? [YES/NO]
   - Build time: _____ minutes
   - Status: [PASS/FAIL]

3. Drift Monitoring
   - Baseline created? [YES/NO]
   - Drift detector working? [YES/NO]
   - Status: [PASS/FAIL]

OVERALL: [✅ WORKING / ⚠️ PARTIAL / ❌ BROKEN]

Notes:
_______________________________________________________
_______________________________________________________
```

---

## 🚀 Summary

**To test if automated retraining is working:**

1. **Quick Check** (5 min):
   - Visit Jenkins: http://localhost:8080
   - Click "Build Now" on pipeline
   - Verify all stages complete ✅

2. **Full Test** (30 min):
   - Run Colab training notebook
   - Trigger Jenkins build
   - Verify new model deployed
   - Test API with curl

3. **Monitor** (Ongoing):
   - Check build history
   - Track model versions
   - Monitor drift metrics

---

**Status**: ✅ **Ready to Test**

Next: Run the quick check and let me know results! 🎯
