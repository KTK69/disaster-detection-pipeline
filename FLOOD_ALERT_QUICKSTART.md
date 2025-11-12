# 🚀 Flood Alert System - Quick Start (5 minutes)

## What You're Getting

A **Real-Time Flood Alert System** that:
- 🌊 Detects floods from satellite images
- 📍 Calculates distance to each city/area
- 🚨 Generates alerts (MONITOR → WARNING → ALERT → EMERGENCY)
- 📊 Shows "how far away" the flood is
- 📋 Provides evacuation recommendations

---

## ⚡ Quick Start

### Step 1: Your System Already Has This!

No new installation needed! The flood alert system is built into your existing API:

✅ `src/api/flood_alert_system.py` - Core alert logic
✅ Updated `src/api/inference_api.py` - Integrated into API
✅ Web dashboard at `http://localhost:8000`

### Step 2: Start the API

```powershell
cd c:\Docs\project\DevOps

# Using Docker (recommended)
docker-compose up -d detection-api

# Or locally (if TensorFlow installed)
python -m uvicorn src.api.inference_api:app --reload --host 0.0.0.0 --port 8000
```

**Verify it's running**:
```powershell
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", ...}`

### Step 3: Open Web Dashboard

Go to: `http://localhost:8000`

You'll see:
```
🌊 Real-Time Flood Alert System
📡 Upload SAR Image for Flood Detection
[Drag and drop image here]
```

### Step 4: Test with an Image

1. Click upload area
2. Select any satellite image (`.tif`, `.tiff`, or `.png`)
3. Click "🚀 Analyze Image"
4. See results with distance to each area!

---

## 📊 What You'll See

After uploading an image:

```
🟠 ALERT: High flood risk detected (22.5% area affected)
⚡ URGENT: Downtown Vizag is in critical zone (3.2 km away)

FLOOD STATISTICS:
- Flood Coverage: 22.5%
- Confidence: 85.7%
- Affected Area: 22.5 km²

AREA PROXIMITY ANALYSIS:
Downtown Vizag    3.2 km    🔴 CRITICAL
Port Area        12.4 km    🟠 HIGH
Waltair          18.5 km    🟡 MODERATE
Gajuwaka         42.1 km    🟢 LOW

RECOMMENDATIONS:
✓ PREPARE TO EVACUATE immediately
✓ Move to higher ground
✓ Take important documents
✓ Inform local authorities
✓ Evacuation zone: Downtown Vizag
```

---

## 🎯 Distance Meanings

| Distance | Threat | Action | Time |
|----------|--------|--------|------|
| < 5 km | 🔴 CRITICAL | Evacuate NOW | 30 min |
| 5-15 km | 🟠 HIGH | Prepare to evacuate | 2 hours |
| 15-30 km | 🟡 MODERATE | Monitor closely | 6 hours |
| > 30 km | 🟢 LOW | Keep watching | 12+ hours |

---

## 🧪 Test the API

### Option 1: Web Interface (Easiest)
```
1. Open: http://localhost:8000
2. Upload image
3. Click "Analyze"
```

### Option 2: Command Line

```powershell
# Upload image and get alert
curl -X POST http://localhost:8000/api/alert/detect `
  -F "image=@test_image.tif"
```

### Option 3: Python

```python
import requests

# Upload image
with open('test_image.tif', 'rb') as f:
    files = {'image': f}
    response = requests.post(
        'http://localhost:8000/api/alert/detect',
        files=files
    )

# Get alert data
alert = response.json()

print(f"Alert Level: {alert['alert_type']}")
print(f"Flood Coverage: {alert['statistics']['flood_percentage']}%")
print(f"Closest Area: {alert['proximity_analysis']['closest_area']['area']}")
print(f"Distance: {alert['proximity_analysis']['closest_area']['distance_km']} km")
print(f"Threat: {alert['proximity_analysis']['closest_area']['threat_level']}")
```

---

## 🗺️ Areas Being Monitored

Your system tracks these populated areas in Visakhapatnam:

1. **Downtown Vizag** - 500,000 people (Commercial/Residential hub)
2. **Port Area** - 100,000 people (Industrial/Shipping)
3. **Waltair** - 200,000 people (Residential)
4. **Gajuwaka** - 150,000 people (Residential)
5. **Visakhapatnam Port** - 50,000 people (Industrial)

**Total Protected Population**: ~1,000,000 people

---

## 🚨 Alert Levels Explained

### 🟢 MONITOR (Green)
- Flood detected but < 5% coverage
- All areas > 30 km away
- **Action**: Keep watching, prepare

### 🟡 WARNING (Yellow)
- Flood 5-15% coverage
- Some areas 15-30 km away
- **Action**: Alert public, prepare evacuation

### 🟠 ALERT (Orange)
- Flood 15-30% coverage
- Closest areas 5-15 km away
- **Action**: Issue evacuation orders

### 🔴 EMERGENCY (Red)
- Flood > 30% coverage
- Closest areas < 5 km away
- **Action**: EVACUATE IMMEDIATELY

---

## 📱 API Endpoints

```
GET  /                          → Web Dashboard
POST /api/alert/detect          → Upload image & get alert
GET  /api/alert/history         → Recent alerts
GET  /api/alert/status          → Current status
GET  /api/health                → System health
```

---

## 🔧 How It Works

```
1. You upload satellite image
   ↓
2. System analyzes flood coverage %
   ↓
3. Calculates distance to 5 populated areas
   ↓
4. Determines threat level for each area
   ↓
5. Generates alert with recommendations
   ↓
6. Displays on web dashboard + API
```

---

## 💡 Real-World Example

**Scenario**: Cyclone approaching Visakhapatnam coast

**Time 8 PM** - First detection
```
Satellite Image: Shows rain systems 200 km away
Alert: 🟢 MONITOR - <1% coverage, 150 km away
Action: Activate weather monitoring
```

**Time 11 PM** - Getting closer
```
Image: Shows organized storm pattern, 100 km away  
Alert: 🟡 WARNING - 5% coverage, 80 km away
Action: Alert public, open emergency centers
```

**Time 2 AM** - Very close
```
Image: Heavy rain bands, flooding visible at coast
Alert: 🟠 ALERT - 18% coverage, 25 km from Downtown
Action: Evacuation order issued
```

**Time 4 AM** - Flood hitting city
```
Image: Massive flooding, breached embankments
Alert: 🔴 EMERGENCY - 35% coverage, 3.2 km from Downtown
Action: EVACUATE NOW, rescue operations activated
```

---

## ✅ Verification

Run this to make sure everything works:

```powershell
# 1. Check API running
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}

# 2. Check API docs
# Open: http://localhost:8000/api/docs
# Should show all endpoints

# 3. Check web dashboard
# Open: http://localhost:8000
# Should show upload interface

# 4. Check Docker container
docker-compose ps
# Should show: disaster-api ... Up
```

---

## 🎯 Use Cases

### 1. **Real-Time Monitoring**
Monitor satellite feeds continuously, alert when flood detected

### 2. **Emergency Response**
Authorities get alerts + proximity data for resource allocation

### 3. **Public Information**
Share alerts with citizens via web/mobile/SMS

### 4. **Historical Analysis**
Track all alerts in history for post-event analysis

### 5. **Training & Drills**
Practice evacuation procedures with realistic distance data

---

## 📊 Key Metrics Explained

```json
{
  "alert_type": "ALERT",           // Level: MONITOR/WARNING/ALERT/EMERGENCY
  "severity": "high",              // Severity: low/moderate/high/critical
  "flood_percentage": 22.5,        // % of area affected by flood
  "confidence": 0.857,             // Model confidence (0-1)
  "affected_area_km2": 22.5,       // Estimated area in km²
  
  "closest_area": {
    "area": "Downtown Vizag",      // Closest populated area
    "distance_km": 3.2,            // Distance in kilometers
    "threat_level": "CRITICAL",    // Threat based on distance
    "eta_hours": 0.5               // Hours until impact
  }
}
```

---

## 🔗 Integration Examples

### With Emergency Services

```
IF alert_type == "EMERGENCY":
   - Call 112 automatically
   - Send SMS to all registered residents
   - Alert police/fire/medical
   - Open emergency shelters
   - Deploy rescue teams
```

### With Media

```
IF alert_type == "ALERT" or "EMERGENCY":
   - Send press release
   - Update emergency broadcast system
   - Alert local media channels
   - Post on official websites
```

### With Mobile App

```
IF distance_km < 30:
   - Send push notification
   - Show alert on home screen
   - Provide evacuation route
   - Link to emergency hotline
```

---

## 🎓 What This Demonstrates

Your system shows:
1. **Satellite Image Analysis** - Flood detection from SAR data
2. **Geospatial Computing** - Distance calculations (Haversine formula)
3. **Real-Time Alerting** - Event-driven notifications
4. **API Design** - RESTful web services
5. **Web UI/UX** - Interactive dashboard
6. **Emergency Management** - Crisis response workflow

---

## 🚀 Next Level: Enhancements

### Short Term (Days)
- [ ] Connect to live Sentinel-1 data
- [ ] Set up automatic daily image download
- [ ] Add SMS alerting

### Medium Term (Weeks)
- [ ] Mobile app with push notifications
- [ ] Integration with 112 emergency center
- [ ] Historical trend analysis dashboard

### Long Term (Months)
- [ ] Add fire/landslide detection
- [ ] Multi-city coverage
- [ ] GIS visualization
- [ ] Government agency integration

---

## 📞 Quick Help

**Q: Image upload fails?**
A: Check file format (.tif, .tiff, .png), size should be reasonable

**Q: No flood detected?**
A: That means no flooding in the image - working correctly!

**Q: Distances seem wrong?**
A: Verify image coordinates match Visakhapatnam (17.68°N, 83.21°E)

**Q: API not responding?**
A: Restart with `docker-compose restart detection-api`

**Q: Want to add custom areas?**
A: Edit `HIGH_RISK_AREAS` list in `src/api/flood_alert_system.py`

---

## 💾 Commits to GitHub

```bash
git add src/api/flood_alert_system.py
git add src/api/inference_api.py  
git add FLOOD_ALERT_USER_GUIDE.md
git add FLOOD_ALERT_QUICKSTART.md
git commit -m "feat: Add real-time flood alert system with proximity analysis"
git push origin main
```

---

## 🌊 Summary

Your system now provides:

✅ **Flood Detection** from satellite imagery
✅ **Proximity Analysis** to populated areas  
✅ **Distance Metrics** in kilometers
✅ **Real-Time Alerts** with threat levels
✅ **Evacuation Recommendations** based on distance
✅ **Web Dashboard** for public access
✅ **REST API** for integration

**Ready to save lives!** 🚀🌊

---

**Time to get started: 5 minutes**
**Time to deploy: 1 day**
**Lives potentially saved: Thousands**

Open http://localhost:8000 and start saving lives! 💙
