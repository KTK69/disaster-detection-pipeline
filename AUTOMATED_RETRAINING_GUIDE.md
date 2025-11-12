# 🤖 Automated Model Retraining Setup Guide

## Overview

This guide explains how to set up **automated model retraining** with 3 different trigger methods:

1. **Time-Based**: Retrain on a schedule (e.g., weekly)
2. **Data Drift**: Retrain when drift detected in production data
3. **Performance-Based**: Retrain if model accuracy drops

---

## 🔧 Updated Pipeline Architecture

The Jenkins pipeline now includes **3 NEW STAGES** for automated retraining:

```
Pipeline Execution Flow:
├─ 🔍 Checkout (Pull code)
├─ 🧪 Environment Setup (Check Python)
├─ 📥 Sync Models (Pull latest from Drive)
├─ 🔬 Run Tests (Optional)
├─ 📊 Check Model Performance (Validate accuracy)
├─ 🔍 Drift Detection (Check for data drift)
│
├─ 🤖 Check Retraining Conditions ⭐ NEW
│   └─ Determines if retraining is needed
│
├─ 📚 Automated Model Retraining ⭐ NEW
│   └─ Triggers retraining if conditions met
│   └─ Verifies new model created
│
├─ 🔄 Sync Retrained Models ⭐ NEW
│   └─ Uploads new models to Google Drive
│
├─ 🐳 Build Docker Image (Rebuild with new model)
├─ 🚀 Deploy (Start container with latest model)
├─ ✅ Health Check (Verify API working)
└─ 📊 Post-Deployment Tests (Test endpoints)
```

---

## ✅ Quick Start (5 minutes)

### Step 1: Verify Scripts are in Place

```powershell
# Check that auto_retrain.py exists
Test-Path C:\Docs\project\DevOps\scripts\auto_retrain.py

# Should output: True
```

### Step 2: Test Retraining Check

```powershell
cd C:\Docs\project\DevOps

# Check if retraining should be triggered
python scripts/auto_retrain.py --check --model flood

# Output example:
# {
#   "timestamp": "2025-11-12T15:30:45.123456",
#   "model_type": "flood",
#   "should_retrain": true,
#   "reasons": ["New training data detected"],
#   "warnings": []
# }
```

### Step 3: View Retrain Report

```powershell
# See retraining history and status
python scripts/auto_retrain.py --report --model flood

# Output example:
# ╔════════════════════════════════════════════════════╗
# ║   RETRAINING STATUS REPORT - FLOOD                ║
# ╚════════════════════════════════════════════════════╝
#
# 📊 Metrics:
#    Total Retrains: 2
#    Last Retrain: 2025-11-12T14:22:33.456789
#    
# 📋 Recent History:
#    ✅ 2025-11-12T14:22:33 - jenkins
#    ✅ 2025-11-12T13:15:22 - colab
```

---

## 🎯 How to Trigger Automated Retraining

### Method 1: Via Jenkins (Recommended)

**Automatic Trigger** (on every build):
```powershell
# Visit Jenkins
http://localhost:8080/job/disaster-detection-pipeline

# Click: "Build Now"

# Pipeline will:
# 1. Check retraining conditions
# 2. If triggered, automatically retrain
# 3. Verify new model
# 4. Deploy new version
```

**What Triggers Retraining**:
- ✅ New training data in `data/retraining/`
- ✅ Model accuracy < 85%
- ✅ Data drift detected (drift_alert.txt exists)
- ✅ Weekly schedule (7+ days since last retrain)

### Method 2: Manual Trigger via Script

**Trigger Colab Retraining** (interactive):
```powershell
python scripts/auto_retrain.py --trigger colab --model flood --verify

# What happens:
# 1. Opens notebook for manual execution
# 2. You run cells in Colab
# 3. Script verifies new model created
# 4. Records retrain event
```

**Trigger Local Retraining** (fast, requires dependencies):
```powershell
python scripts/auto_retrain.py --trigger local --model flood --verify

# What happens:
# 1. Runs training locally (if dependencies available)
# 2. Creates new model in models/saved_models/flood/
# 3. Verifies metrics
# 4. Records retrain event
```

**Trigger Jenkins Retraining** (via REST API):
```powershell
python scripts/auto_retrain.py --trigger jenkins --model flood --verify

# What happens:
# 1. Calls Jenkins API
# 2. Queues build job
# 3. Monitors for completion
# 4. Verifies new model deployed
```

---

## 📊 Test: Simulate Drift-Triggered Retraining

### Scenario: Production detects data drift → Auto-retrain

**Step 1: Create Drift Alert**
```powershell
# Simulate drift detection
New-Item -Path "c:\Docs\project\DevOps\data\drift_alert.txt" -Value "drift_detected_$(Get-Date -Format 'yyyyMMdd_HHmmss')" -Force

Write-Host "✅ Drift alert created"
```

**Step 2: Trigger Jenkins Build**
```powershell
# Visit Jenkins
http://localhost:8080/job/disaster-detection-pipeline

# Click: "Build Now"

# Monitor: Watch console for:
# Stage: 🤖 Check Retraining Conditions
# Output: "🚨 Retraining should be triggered!"
# Stage: 📚 Automated Model Retraining
# Output: "🚀 AUTOMATED RETRAINING TRIGGERED!"
```

**Step 3: Verify New Model Created**
```powershell
# Check for new model file
$models = Get-ChildItem "C:\Docs\project\DevOps\models\saved_models\flood\*.keras" | Sort-Object LastWriteTime -Descending

Write-Host "Latest Models:"
$models | Select-Object -First 3 | ForEach-Object {
    Write-Host "  - $($_.Name) ($(Get-Date $_.LastWriteTime -Format 'yyyy-MM-dd HH:mm:ss'))"
}

# If timestamps are recent, retraining worked! ✅
```

---

## 🔄 Test: Simulate Performance-Based Retraining

### Scenario: Model accuracy drops → Auto-retrain

**Step 1: Modify Model Metadata** (simulate degraded performance):
```powershell
# Update latest metadata to show low accuracy
$metadataPath = "C:\Docs\project\DevOps\models\saved_models\flood\model_metadata_20251112_074534.json"

if (Test-Path $metadataPath) {
    $metadata = Get-Content $metadataPath | ConvertFrom-Json
    $metadata.final_val_acc = 0.80  # Below 85% threshold
    $metadata | ConvertTo-Json | Set-Content $metadataPath
    Write-Host "✅ Updated metadata with low accuracy"
}
```

**Step 2: Trigger Jenkins Build**
```powershell
http://localhost:8080/job/disaster-detection-pipeline
# Click: "Build Now"
```

**Step 3: Monitor Retraining**
```powershell
# Watch console output for:
# "Check Retraining Conditions"
# "✅ Model performance degraded"
# "🚀 AUTOMATED RETRAINING TRIGGERED!"
```

**Step 4: Verify**
```powershell
# Check retrain metrics
cat "C:\Docs\project\DevOps\logs\flood_retrain_metrics.json"

# Should show recent retrain event with "success": true
```

---

## 📋 Test: Simulate Time-Based Retraining

### Scenario: Scheduled retraining every 7 days

**Step 1: Check Retrain Schedule**
```powershell
python scripts/auto_retrain.py --check --model flood

# Look for output:
# "Scheduled retraining time" → triggers retrain
# "No new training data" → no trigger
```

**Step 2: Force Schedule Check**
```powershell
# Delete metrics to reset schedule
Remove-Item "C:\Docs\project\DevOps\logs\flood_retrain_metrics.json" -Force

# Next check will trigger (first-time retraining)
python scripts/auto_retrain.py --check --model flood

# Output: "First time retraining - no schedule history"
# should_retrain: true
```

---

## 🚀 Automating Retraining with Cron/Task Scheduler

### Option 1: Windows Task Scheduler (Recommended for Windows)

**Create Scheduled Task for Daily Retraining Check**:

```powershell
# PowerShell (run as Administrator)

$taskName = "DisasterDetectionAutoRetrain"
$taskPath = "C:\Docs\project\DevOps"
$scriptPath = "$taskPath\scripts\auto_retrain.py"

# Create trigger (daily at 2 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM

# Create action
$action = New-ScheduledTaskAction -Execute "python" -Argument "$scriptPath --trigger jenkins --model flood --verify" -WorkingDirectory $taskPath

# Register task
Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -RunLevel Highest

Write-Host "✅ Scheduled task created: $taskName"
Write-Host "   Trigger: Daily at 2:00 AM"
Write-Host "   Action: Auto-retrain flood model"
```

**Verify Task Created**:
```powershell
Get-ScheduledTask -TaskName "DisasterDetectionAutoRetrain"

# Output should show the task
```

**Test Run**:
```powershell
Start-ScheduledTask -TaskName "DisasterDetectionAutoRetrain"

# Check logs
Get-ScheduledTaskInfo -TaskName "DisasterDetectionAutoRetrain"
```

### Option 2: Jenkins Pipeline Schedule

**Add Periodic Build Trigger**:

1. Open Jenkins Job: http://localhost:8080/job/disaster-detection-pipeline/configure
2. Find: "Build Triggers" section
3. Enable: "Build periodically"
4. Set cron expression:

```
# Daily at 2 AM
0 2 * * *

# Weekly on Monday at 2 AM
0 2 * * 1

# Every 6 hours
0 */6 * * *

# Every 30 minutes
*/30 * * * *
```

### Option 3: Bash Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line (daily retrain at 2 AM):
0 2 * * * cd /path/to/DevOps && python scripts/auto_retrain.py --trigger jenkins --model flood --verify

# View crons
crontab -l
```

---

## 📊 Monitoring Retraining

### Check Retrain History

```powershell
# View full retrain metrics
cat "C:\Docs\project\DevOps\logs\flood_retrain_metrics.json"

# Expected output:
# {
#   "retrain_count": 2,
#   "last_retrain": "2025-11-12T14:22:33.123456",
#   "retrain_history": [
#     {
#       "timestamp": "2025-11-12T14:22:33",
#       "model_type": "flood",
#       "method": "jenkins",
#       "success": true
#     }
#   ]
# }
```

### View Retrain Logs

```powershell
# Check latest retrain log
Get-ChildItem "C:\Docs\project\DevOps\logs\retrain_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Read log
cat (Get-ChildItem "C:\Docs\project\DevOps\logs\retrain_*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName

# Look for:
# ✅ Model training complete
# ✅ New model created
# ✅ Model verification passed
```

### Monitor Jenkins Builds

```powershell
# View recent builds
curl http://localhost:8080/job/disaster-detection-pipeline/api/json | ConvertFrom-Json | Select-Object -ExpandProperty builds | Select-Object number, result, duration -First 10

# View specific build console
curl http://localhost:8080/job/disaster-detection-pipeline/[BUILD_NUMBER]/consoleText
```

### Check Deployed Model Version

```powershell
# Get current model info via API
curl http://localhost:8000/models/info

# Expected response with latest model:
# {
#   "flood": {
#     "model_name": "vizag_flood_model_20251112_074534",
#     "version": "1.0",
#     "accuracy": 0.9671,
#     "iou": 0.4095,
#     "last_updated": "2025-11-12T14:22:33"
#   }
# }
```

---

## 🎨 Example: Complete Automated Retraining Workflow

**Scenario**: Weekly Monday morning retrain with drift detection

### Step 1: Set Up Weekly Schedule

```powershell
# Windows Task Scheduler
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 6:00AM
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "scripts/auto_retrain.py --trigger jenkins --model flood --verify" `
  -WorkingDirectory "C:\Docs\project\DevOps"
Register-ScheduledTask -TaskName "WeeklyFloodModelRetrain" -Trigger $trigger -Action $action
```

### Step 2: Collect Production Data

```powershell
# During the week, copy new Sentinel-1 imagery to:
Copy-Item "path/to/new/data/*.tif" "C:\Docs\project\DevOps\data\retraining\"

# Track metrics for drift detection
# (API logs incoming predictions automatically)
```

### Step 3: Monday Morning - Automated Retraining

**6:00 AM**: Task Scheduler triggers:
```
① Check retraining conditions
   - New data in data/retraining/? ✅ YES
   - Performance degraded? Check previous metrics
   - Drift detected? Check logs
   - Schedule trigger? ✅ YES (weekly)
   
   Result: should_retrain = true

② Trigger Jenkins build
   - Pull latest code
   - Validate models
   - **START RETRAINING** (new stage!)
   - Build Docker image with new model
   - Deploy to http://localhost:8000
   - Run health checks
   
③ Verify deployment
   - New model metrics: accuracy > 85%?
   - API responding? ✅
   - Model updated? ✅
   
④ Record event
   - metrics file updated
   - Logs created
   - Ready for production
```

### Step 4: Verify Success

```powershell
# Monday at 7:00 AM - Check results
python scripts/auto_retrain.py --report --model flood

# Output:
# ╔════════════════════════════════════════════════════╗
# ║   RETRAINING STATUS REPORT - FLOOD                ║
# ╚════════════════════════════════════════════════════╝
#
# 📊 Metrics:
#    Total Retrains: 3
#    Last Retrain: 2025-11-12T06:15:33.456789 ⭐ NEW
```

---

## 🔐 Production Best Practices

### 1. Backup Before Retraining

```powershell
# Automatic backup of current model
$backupDir = "models/backups/$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $backupDir -Force

Copy-Item "models/saved_models/flood/*.keras" $backupDir/
Copy-Item "models/saved_models/flood/*.json" $backupDir/

Write-Host "✅ Backup created: $backupDir"
```

### 2. Validation Gates

```powershell
# Only deploy if:
# - Model accuracy > 85%
# - IoU > 0.35
# - No decrease in performance vs previous
# - Health checks pass
```

### 3. Rollback Plan

```powershell
# If new model fails
# 1. Check backup models
$backups = Get-ChildItem "models/backups/" | Sort-Object LastWriteTime -Descending

# 2. Restore previous model
Copy-Item "$($backups[0].FullName)/*.keras" "models/saved_models/flood/"

# 3. Rebuild Docker image
docker-compose down
docker-compose build detection-api
docker-compose up -d detection-api

# 4. Verify health
curl http://localhost:8000/health
```

---

## ❓ Troubleshooting

### Issue: "Retraining check skipped"

```powershell
# Cause: Python not found in Docker container
# Solution:
docker-compose ps  # Verify container running

docker exec disaster-api python --version  # Check Python

# If not working, rebuild:
docker-compose down
docker-compose build detection-api
docker-compose up -d detection-api
```

### Issue: "Drift alert not detected"

```powershell
# Check if drift_alert.txt exists
Test-Path "C:\Docs\project\DevOps\data\drift_alert.txt"

# If missing, create it
New-Item -Path "C:\Docs\project\DevOps\data\drift_alert.txt" -Force
```

### Issue: "New model not deployed"

```powershell
# Check Docker logs
docker logs disaster-api

# Check if model file exists
Get-ChildItem "C:\Docs\project\DevOps\models\saved_models\flood\*.keras" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

# Rebuild Docker image
docker-compose build --no-cache detection-api
docker-compose up -d detection-api
```

---

## 📈 Metrics Dashboard (Optional)

### Create Grafana Dashboard

Create `monitoring/docker-compose.yml`:

```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
```

Add metrics to retrain script:

```python
# Log retraining metrics to Prometheus
from prometheus_client import Counter, Gauge

retrain_counter = Counter('model_retrains_total', 'Total model retrains')
model_accuracy = Gauge('model_accuracy', 'Latest model accuracy')
model_iou = Gauge('model_iou', 'Latest model IoU score')

# Update when retrain completes
retrain_counter.inc()
model_accuracy.set(new_model.accuracy)
model_iou.set(new_model.iou)
```

---

## ✅ Verification Checklist

- [ ] `auto_retrain.py` script exists in `scripts/`
- [ ] Jenkinsfile has 3 new retraining stages
- [ ] Can run: `python scripts/auto_retrain.py --check`
- [ ] Can view: `python scripts/auto_retrain.py --report`
- [ ] Jenkins build completes successfully
- [ ] No model retraining happens on first build (expected)
- [ ] Scheduled task created (Windows) or cron configured (Linux)
- [ ] Can manually trigger: `python scripts/auto_retrain.py --trigger jenkins`
- [ ] New models appear after retraining
- [ ] API serves updated model after build
- [ ] Logs show retraining events

---

## 🎯 Summary

**You now have**:
✅ Automated retraining triggered by:
  - Data drift detection
  - Performance degradation
  - Time-based schedule
  
✅ Three trigger methods:
  - Jenkins (via REST API)
  - Colab (manual + automated)
  - Local (fast fallback)
  
✅ Full pipeline integration:
  - Automatic condition checking
  - Model verification
  - Deployment verification
  - Metrics tracking

✅ Production-ready:
  - Backup system
  - Rollback capability
  - Health checks
  - Comprehensive logging

---

## 🚀 Next Steps

1. **Immediate**: Test with `python scripts/auto_retrain.py --check`
2. **Today**: Set up Windows Task Scheduler or Jenkins cron
3. **This Week**: Monitor first automated retraining cycle
4. **Next**: Add Prometheus/Grafana for monitoring
5. **Future**: Add email/Slack alerts for retraining events

---

**Questions?** Check the logs:
- Retraining logs: `logs/retrain_*.log`
- Metrics: `logs/flood_retrain_metrics.json`
- Jenkins console: http://localhost:8080

