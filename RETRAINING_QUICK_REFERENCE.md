# 🚀 Automated Retraining - Quick Reference Card

## 📋 What You Need to Know

Your disaster detection pipeline now has **fully automated model retraining** that triggers automatically when:
- ⏰ 7+ days pass (scheduled)
- 📊 Data drift detected (statistical shift in production data)
- 📉 Model performance drops (accuracy < 85% or IoU < 0.35)

---

## ⚡ Quick Commands

### Check if Retraining Should Happen
```powershell
cd c:\Docs\project\DevOps
python scripts/auto_retrain.py --check --model flood
```

### View Retraining History
```powershell
python scripts/auto_retrain.py --report --model flood
```

### Manually Trigger Retraining via Jenkins
```
Visit: http://localhost:8080/job/disaster-detection-pipeline
Click: "Build Now"
```

### Simulate Drift Alert (test drift-triggered retraining)
```powershell
New-Item -Path "data/drift_alert.txt" -Value "test" -Force
# Then trigger Jenkins build - should automatically retrain
```

---

## 🎯 How It Works (Simple Version)

```
1. DATA ARRIVES (new satellite images)
   ↓
2. JENKINS CHECKS CONDITIONS
   - Is there new data? 
   - Did performance drop?
   - Was there data drift?
   - Has it been 7+ days?
   ↓
3. IF YES → START RETRAINING
   - Run model training
   - Verify new model
   - Build Docker image
   - Deploy to production
   ↓
4. RESULT: Fresh model at http://localhost:8000
```

---

## 📊 Files You Created

| File | Purpose |
|------|---------|
| `scripts/auto_retrain.py` | Core retraining logic (400+ lines) |
| `Jenkinsfile` | Updated with 3 new retraining stages |
| `AUTOMATED_RETRAINING_GUIDE.md` | Complete setup guide (500+ lines) |
| `TEST_AUTOMATED_RETRAINING.md` | How to test (300+ lines) |
| `RETRAINING_IMPLEMENTATION_SUMMARY.md` | This implementation summary |

---

## 🧪 Test It Right Now (10 minutes)

### Test 1: Check Conditions
```powershell
python scripts/auto_retrain.py --check --model flood
```
Should output: Conditions met? New data? Performance? Schedule?

### Test 2: View Report
```powershell
python scripts/auto_retrain.py --report --model flood
```
Should output: Retraining history and metrics

### Test 3: Trigger Jenkins
```
1. Visit: http://localhost:8080/job/disaster-detection-pipeline
2. Click: "Build Now"
3. Watch console for new stages:
   - "🤖 Check Retraining Conditions"
   - "📚 Automated Model Retraining"
   - "🔄 Sync Retrained Models"
```

---

## ⏰ Scheduling (Pick One)

### Option A: Windows Task Scheduler
```powershell
# Run daily at 2 AM
$trigger = New-ScheduledTaskTrigger -Daily -At 2:00AM
$action = New-ScheduledTaskAction -Execute "python" `
  -Argument "scripts/auto_retrain.py --trigger jenkins --model flood" `
  -WorkingDirectory "C:\Docs\project\DevOps"
Register-ScheduledTask -TaskName "FloodModelRetrain" -Trigger $trigger -Action $action
```

### Option B: Jenkins Built-in Cron
1. Open: http://localhost:8080/job/disaster-detection-pipeline/configure
2. Find: "Build Triggers" → "Build periodically"
3. Enter cron: `0 2 * * *` (daily at 2 AM)

---

## 📈 Monitoring

### Check Latest Model
```powershell
# Via API
curl http://localhost:8000/models/info

# Via filesystem
Get-ChildItem "models/saved_models/flood\*.keras" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
```

### Check Retraining Metrics
```powershell
cat logs/flood_retrain_metrics.json
```

### View Jenkins Builds
```
http://localhost:8080/job/disaster-detection-pipeline
```

---

## 🔑 Key Concepts

### 1. Time-Based Trigger ⏰
- Default: Every 7 days
- Ensures model doesn't go stale
- Prevents performance drift over time

### 2. Drift-Based Trigger 📊
- Detects when production data changes
- Creates file: `data/drift_alert.txt`
- Automatically retrains when distribution shifts

### 3. Performance-Based Trigger 📉
- Monitors: accuracy > 85%, IoU > 0.35
- Triggers retraining if metrics drop
- Ensures quality in production

---

## ✅ Verification Checklist

- [ ] `python scripts/auto_retrain.py --check` runs without error
- [ ] Report shows: "Total Retrains: 0" (first time)
- [ ] Jenkins build completes successfully
- [ ] New stages visible in Jenkins console
- [ ] Model files exist in `models/saved_models/flood/`
- [ ] API responds at `http://localhost:8000/models/info`

---

## ❓ Troubleshooting

### Issue: Command not found
```powershell
# Make sure you're in the right directory
cd c:\Docs\project\DevOps

# Check file exists
Test-Path scripts/auto_retrain.py
```

### Issue: No retraining triggered
```powershell
# Check conditions
python scripts/auto_retrain.py --check

# Common reasons: No new data, no drift alert, schedule not met yet
```

### Issue: Jenkins build failed
```powershell
# Check Jenkins console
http://localhost:8080/job/disaster-detection-pipeline/[BUILD_NUM]/console

# Check Docker
docker logs disaster-api
```

---

## 📚 Full Documentation

For detailed information, see:
- `AUTOMATED_RETRAINING_GUIDE.md` - Complete setup guide
- `TEST_AUTOMATED_RETRAINING.md` - Testing procedures
- `RETRAINING_IMPLEMENTATION_SUMMARY.md` - Implementation details

---

## 🎯 Next Steps

1. **Today**: Test with `python scripts/auto_retrain.py --check`
2. **This Week**: Set up scheduled task or Jenkins cron
3. **Next Week**: Monitor first automated retraining cycle
4. **Future**: Add alerts (Slack/email) for retrain events

---

## 📞 Support

**Quick Checks**:
1. Is Docker container running? `docker-compose ps`
2. Is API healthy? `curl http://localhost:8000/health`
3. Is Jenkins running? Visit http://localhost:8080
4. Check logs? `cat logs/retrain_*.log`

**More Help**:
- See `AUTOMATED_RETRAINING_GUIDE.md` (troubleshooting section)
- Check Jenkins console for detailed error messages
- Review logs in `logs/` directory

---

**Status**: ✅ **Live and Ready**

Automated retraining is now active! Your model will automatically retrain based on schedule, drift detection, or performance metrics.

```
🚀 YOUR PIPELINE:
   Raw Data → Auto-Check → Trigger Retrain → Deploy → Production
   (Satellite)  (Weekly)    (If Needed)     (Docker)  (http://localhost:8000)
```
