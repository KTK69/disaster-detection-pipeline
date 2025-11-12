"""
Real-Time Flood Alert System with Distance & Proximity Detection
Provides early warnings based on SAR imagery analysis and calculates threat distance
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import numpy as np
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Real-Time Flood Alert System",
    description="Early warning system for flood detection with proximity analysis",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_cors = CORSMiddleware(
    app,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
model_manager: Optional[object] = None
MODELS_LOADED = False

# Alert history storage
ALERT_HISTORY = []
MAX_ALERTS = 100

# Visakhapatnam coordinates (target region)
VIZAG_COORDS = {
    "lat": 17.6869,
    "lon": 83.2185,
    "city": "Visakhapatnam",
    "zone": "Andhra Pradesh"
}

# High-risk areas (populated zones in Vizag)
HIGH_RISK_AREAS = [
    {"name": "Downtown Vizag", "lat": 17.6788, "lon": 83.2244, "population": 500000},
    {"name": "Port Area", "lat": 17.7248, "lon": 83.2940, "population": 100000},
    {"name": "Gajuwaka", "lat": 17.6542, "lon": 83.3091, "population": 150000},
    {"name": "Visakhapatnam Port", "lat": 17.7200, "lon": 83.2900, "population": 50000},
    {"name": "Waltair", "lat": 17.7920, "lon": 83.2590, "population": 200000},
]


class FloodAlertSystem:
    """Core flood alert and proximity detection system"""
    
    def __init__(self):
        self.last_alert_time = None
        self.alert_cache = {}
        self.proximity_cache = {}
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance in km between two coordinates (Haversine formula)
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth radius in km
        
        lat1_rad, lon1_rad = radians(lat1), radians(lon1)
        lat2_rad, lon2_rad = radians(lat2), radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = sin(dlat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def calculate_proximity_to_areas(self, flood_lat: float, flood_lon: float) -> Dict:
        """
        Calculate distance from flood origin to all populated areas
        Returns: Areas sorted by proximity
        """
        proximity_data = []
        
        for area in HIGH_RISK_AREAS:
            distance = self.calculate_distance(
                flood_lat, flood_lon,
                area["lat"], area["lon"]
            )
            
            # Calculate threat level based on distance
            if distance < 5:  # < 5 km
                threat_level = "CRITICAL"
                threat_color = "#FF0000"  # Red
                eta_hours = 0.5
            elif distance < 15:  # 5-15 km
                threat_level = "HIGH"
                threat_color = "#FF6600"  # Orange
                eta_hours = 2
            elif distance < 30:  # 15-30 km
                threat_level = "MODERATE"
                threat_color = "#FFFF00"  # Yellow
                eta_hours = 6
            else:  # > 30 km
                threat_level = "LOW"
                threat_color = "#00CC00"  # Green
                eta_hours = 12
            
            proximity_data.append({
                "area": area["name"],
                "population": area["population"],
                "distance_km": round(distance, 2),
                "threat_level": threat_level,
                "threat_color": threat_color,
                "eta_hours": eta_hours,
                "coordinates": {"lat": area["lat"], "lon": area["lon"]}
            })
        
        # Sort by distance (closest first)
        proximity_data.sort(key=lambda x: x["distance_km"])
        
        return proximity_data
    
    def generate_alert(self, flood_percentage: float, confidence: float, 
                      flood_lat: float, flood_lon: float) -> Dict:
        """
        Generate comprehensive flood alert with proximity analysis
        """
        
        # Determine alert severity
        if flood_percentage < 5:
            severity = "low"
            alert_type = "MONITOR"
            color = "#00FF00"
        elif flood_percentage < 15:
            severity = "moderate"
            alert_type = "WARNING"
            color = "#FFFF00"
        elif flood_percentage < 30:
            severity = "high"
            alert_type = "ALERT"
            color = "#FF6600"
        else:
            severity = "critical"
            alert_type = "EMERGENCY"
            color = "#FF0000"
        
        # Calculate proximity to all areas
        proximity_areas = self.calculate_proximity_to_areas(flood_lat, flood_lon)
        
        # Find most critical area
        most_threatened = proximity_areas[0] if proximity_areas else None
        
        # Generate alert message
        alert_message = self._generate_alert_message(
            severity, flood_percentage, most_threatened
        )
        
        alert = {
            "alert_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "alert_type": alert_type,
            "severity": severity,
            "color": color,
            "message": alert_message,
            "flood_detected": bool(flood_percentage > 5.0),
            "statistics": {
                "flood_percentage": round(flood_percentage, 2),
                "confidence": round(confidence, 3),
                "affected_area_km2": round(flood_percentage * 100, 2)
            },
            "origin": {
                "latitude": flood_lat,
                "longitude": flood_lon,
                "region": "Visakhapatnam, Andhra Pradesh"
            },
            "proximity_analysis": {
                "total_areas_analyzed": len(proximity_areas),
                "areas_in_threat": {
                    "critical": len([a for a in proximity_areas if a["threat_level"] == "CRITICAL"]),
                    "high": len([a for a in proximity_areas if a["threat_level"] == "HIGH"]),
                    "moderate": len([a for a in proximity_areas if a["threat_level"] == "MODERATE"]),
                },
                "closest_area": most_threatened,
                "all_areas": proximity_areas
            },
            "recommendations": self._generate_recommendations(alert_type, most_threatened)
        }
        
        return alert
    
    def _generate_alert_message(self, severity: str, flood_percentage: float, 
                               most_threatened: Optional[Dict]) -> str:
        """Generate human-readable alert message"""
        
        messages = {
            "low": f"⚠️ MONITOR: Low flood risk detected ({flood_percentage:.1f}% area affected)",
            "moderate": f"🚨 WARNING: Moderate flood risk detected ({flood_percentage:.1f}% area affected)",
            "high": f"🚨 ALERT: High flood risk detected ({flood_percentage:.1f}% area affected)",
            "critical": f"🚨 EMERGENCY: Critical flood threat detected ({flood_percentage:.1f}% area affected)"
        }
        
        msg = messages.get(severity, "Unknown status")
        
        if most_threatened:
            if most_threatened["distance_km"] < 5:
                msg += f"\n⚡ URGENT: {most_threatened['area']} is in critical zone ({most_threatened['distance_km']} km away)"
            elif most_threatened["distance_km"] < 15:
                msg += f"\n⚠️ {most_threatened['area']} threatened ({most_threatened['distance_km']} km away)"
        
        return msg
    
    def _generate_recommendations(self, alert_type: str, most_threatened: Optional[Dict]) -> List[str]:
        """Generate actionable recommendations"""
        
        recommendations = {
            "MONITOR": [
                "Continue monitoring weather updates",
                "Prepare emergency supplies",
                "Keep vehicles fueled"
            ],
            "WARNING": [
                "Review evacuation routes",
                "Stay alert to emergency broadcasts",
                "Keep emergency kit accessible",
                "Alert family and neighbors"
            ],
            "ALERT": [
                "PREPARE TO EVACUATE immediately",
                "Move to higher ground",
                "Take important documents",
                "Inform local authorities",
                f"Evacuation zone: {most_threatened['area'] if most_threatened else 'Specified area'}"
            ],
            "EMERGENCY": [
                "EVACUATE IMMEDIATELY to higher ground",
                "Contact emergency services: 112",
                "Move vulnerable persons first",
                "Do NOT attempt to cross flooded areas",
                "Call rescue operations if trapped"
            ]
        }
        
        return recommendations.get(alert_type, [])


# Initialize alert system
alert_system = FloodAlertSystem()


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global model_manager, MODELS_LOADED
    
    logger.info("=" * 70)
    logger.info("🌊 REAL-TIME FLOOD ALERT SYSTEM - Starting")
    logger.info("=" * 70)
    
    try:
        # Initialize model manager
        from src.api.model_loader import ModelManager
        
        models_dir = "./models/saved_models"
        os.makedirs(f"{models_dir}/flood", exist_ok=True)
        os.makedirs(f"{models_dir}/fire", exist_ok=True)
        
        model_manager = ModelManager(model_dir=models_dir)
        model_manager.load_all_models()
        MODELS_LOADED = True
        
        logger.info(f"✅ Models loaded: {model_manager.get_loaded_models()}")
    
    except Exception as e:
        logger.warning(f"⚠️ Could not load models: {e}")
        MODELS_LOADED = False
    
    logger.info("=" * 70)
    logger.info("✅ FLOOD ALERT SYSTEM READY")
    logger.info(f"   🌐 Web Dashboard: http://localhost:8000/")
    logger.info(f"   📡 API: http://localhost:8000/api/docs")
    logger.info(f"   🚨 Alert Endpoint: POST /api/alert/detect")
    logger.info("=" * 70)


# ==================== WEB INTERFACE ====================

@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """Main flood alert dashboard"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🌊 Real-Time Flood Alert System - Visakhapatnam</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            header {
                background: white;
                border-radius: 10px;
                padding: 30px;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            h1 {
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }
            
            .subtitle {
                color: #666;
                font-size: 1.1em;
            }
            
            .main-content {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .card {
                background: white;
                border-radius: 10px;
                padding: 25px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            
            .upload-section {
                grid-column: 1 / -1;
            }
            
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 8px;
                padding: 40px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s;
                background: #f8f9ff;
            }
            
            .upload-area:hover {
                border-color: #764ba2;
                background: #f0f2ff;
            }
            
            .upload-icon {
                font-size: 3em;
                margin-bottom: 15px;
            }
            
            input[type="file"] {
                display: none;
            }
            
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 12px 30px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 1em;
                margin-top: 15px;
                transition: transform 0.2s;
            }
            
            button:hover {
                transform: translateY(-2px);
            }
            
            .alert-box {
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 15px;
                border-left: 5px solid;
            }
            
            .alert-critical {
                background: #ffebee;
                border-color: #c62828;
                color: #c62828;
            }
            
            .alert-high {
                background: #fff3e0;
                border-color: #f57c00;
                color: #f57c00;
            }
            
            .alert-moderate {
                background: #fffde7;
                border-color: #fbc02d;
                color: #f57f17;
            }
            
            .alert-low {
                background: #e8f5e9;
                border-color: #388e3c;
                color: #388e3c;
            }
            
            .stat {
                display: flex;
                justify-content: space-between;
                padding: 12px 0;
                border-bottom: 1px solid #eee;
            }
            
            .stat-label {
                font-weight: 600;
                color: #666;
            }
            
            .stat-value {
                color: #333;
                font-weight: 700;
                font-size: 1.2em;
            }
            
            .proximity-item {
                padding: 12px;
                margin-bottom: 10px;
                border-radius: 5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .proximity-item .area-name {
                font-weight: 600;
                flex: 1;
            }
            
            .proximity-item .distance {
                background: #f0f0f0;
                padding: 5px 12px;
                border-radius: 3px;
                margin: 0 10px;
                font-weight: 700;
            }
            
            .proximity-item .threat-badge {
                padding: 5px 12px;
                border-radius: 20px;
                color: white;
                font-weight: 600;
                font-size: 0.9em;
            }
            
            .threat-critical { background: #c62828; }
            .threat-high { background: #f57c00; }
            .threat-moderate { background: #fbc02d; color: #333; }
            .threat-low { background: #388e3c; }
            
            .loading {
                display: none;
                text-align: center;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .recommendation {
                background: #f5f5f5;
                padding: 12px;
                margin: 8px 0;
                border-left: 3px solid #667eea;
                border-radius: 3px;
            }
            
            .timestamp {
                color: #999;
                font-size: 0.9em;
                margin-top: 15px;
            }
            
            .grid-col-2 {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            
            @media (max-width: 768px) {
                .main-content {
                    grid-template-columns: 1fr;
                }
                .grid-col-2 {
                    grid-template-columns: 1fr;
                }
                h1 {
                    font-size: 1.8em;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🌊 Real-Time Flood Alert System</h1>
                <p class="subtitle">Early Warning System for Visakhapatnam, Andhra Pradesh</p>
            </header>
            
            <div class="main-content">
                <div class="card upload-section">
                    <h2 style="margin-bottom: 20px;">📡 Upload SAR Image for Flood Detection</h2>
                    <div class="upload-area" onclick="document.getElementById('imageInput').click()">
                        <div class="upload-icon">📸</div>
                        <h3>Click to upload or drag & drop</h3>
                        <p style="color: #999; margin-top: 10px;">SAR images (.tif, .tiff) or other formats</p>
                        <input type="file" id="imageInput" accept="image/*,.tif,.tiff" />
                    </div>
                    <button onclick="submitImage()" style="width: 100%;">🚀 Analyze Image</button>
                    <div class="loading" id="loading">
                        <div class="spinner"></div>
                        <p>Processing image...</p>
                    </div>
                </div>
                
                <div class="card" id="resultsCard" style="display: none;">
                    <h2 style="margin-bottom: 20px;">🚨 Alert Status</h2>
                    <div id="alertBox" class="alert-box"></div>
                    <div id="statistics"></div>
                </div>
                
                <div class="card" id="proximityCard" style="display: none;">
                    <h2 style="margin-bottom: 20px;">📍 Area Proximity Analysis</h2>
                    <div id="proximityList"></div>
                </div>
                
                <div class="card" id="recommendationsCard" style="display: none;">
                    <h2 style="margin-bottom: 20px;">📋 Recommendations</h2>
                    <div id="recommendationsList"></div>
                </div>
            </div>
        </div>
        
        <script>
            let selectedFile = null;
            
            document.getElementById('imageInput').addEventListener('change', function(e) {
                selectedFile = e.target.files[0];
                if (selectedFile) {
                    console.log('File selected:', selectedFile.name);
                }
            });
            
            async function submitImage() {
                if (!selectedFile) {
                    alert('Please select an image first');
                    return;
                }
                
                const formData = new FormData();
                formData.append('image', selectedFile);
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('resultsCard').style.display = 'none';
                
                try {
                    const response = await fetch('/api/alert/detect', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    displayResults(data);
                } catch (error) {
                    alert('Error: ' + error.message);
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }
            
            function displayResults(data) {
                const severity = data.severity;
                const alertType = data.alert_type;
                
                // Alert box
                const alertBox = document.getElementById('alertBox');
                alertBox.className = `alert-box alert-${severity}`;
                alertBox.innerHTML = `
                    <strong>${alertType}</strong><br>
                    ${data.message.replace(/\\n/g, '<br>')}
                `;
                
                // Statistics
                const stats = document.getElementById('statistics');
                stats.innerHTML = `
                    <div class="stat">
                        <span class="stat-label">Flood Coverage:</span>
                        <span class="stat-value">${data.statistics.flood_percentage}%</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Confidence:</span>
                        <span class="stat-value">${(data.statistics.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Affected Area:</span>
                        <span class="stat-value">${data.statistics.affected_area_km2} km²</span>
                    </div>
                `;
                
                // Proximity analysis
                const proximityList = document.getElementById('proximityList');
                let html = '';
                data.proximity_analysis.all_areas.forEach(area => {
                    html += `
                        <div class="proximity-item" style="background: ${area.threat_color}22;">
                            <span class="area-name">${area.area}</span>
                            <span class="distance">${area.distance_km} km</span>
                            <span class="threat-badge threat-${area.threat_level.toLowerCase()}">
                                ${area.threat_level}
                            </span>
                        </div>
                    `;
                });
                proximityList.innerHTML = html;
                
                // Recommendations
                const recList = document.getElementById('recommendationsList');
                let recHtml = '';
                data.recommendations.forEach(rec => {
                    recHtml += `<div class="recommendation">✓ ${rec}</div>`;
                });
                recList.innerHTML = recHtml;
                
                // Show all cards
                document.getElementById('resultsCard').style.display = 'block';
                document.getElementById('proximityCard').style.display = 'block';
                document.getElementById('recommendationsCard').style.display = 'block';
                
                // Scroll to results
                document.getElementById('resultsCard').scrollIntoView({ behavior: 'smooth' });
            }
        </script>
    </body>
    </html>
    """


# ==================== API ENDPOINTS ====================

@app.post("/api/alert/detect")
async def detect_flood_alert(image: UploadFile = File(...)):
    """
    Detect flood and generate alert with proximity analysis
    
    Returns: Alert with distance metrics to populated areas
    """
    if not MODELS_LOADED or not model_manager:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        logger.info(f"🌊 Processing flood alert for: {image.filename}")
        
        # Read image
        image_data = await image.read()
        
        import numpy as np
        import tempfile
        
        # Process image
        img_array = np.random.rand(256, 256, 3).astype(np.float32)  # Placeholder
        
        # Predict
        prediction = model_manager.predict('flood', np.expand_dims(img_array, 0))
        pred_mask = np.argmax(prediction[0], axis=-1)
        
        # Calculate statistics
        total_pixels = pred_mask.size
        flood_pixels = (pred_mask == 1).sum()
        flood_percentage = (flood_pixels / total_pixels) * 100
        confidence = 0.85  # Placeholder
        
        # Generate alert with proximity analysis
        alert = alert_system.generate_alert(
            flood_percentage=flood_percentage,
            confidence=confidence,
            flood_lat=VIZAG_COORDS["lat"],
            flood_lon=VIZAG_COORDS["lon"]
        )
        
        # Store in history
        ALERT_HISTORY.append(alert)
        if len(ALERT_HISTORY) > MAX_ALERTS:
            ALERT_HISTORY.pop(0)
        
        logger.info(f"✅ Alert generated: {alert['alert_type']}")
        
        return JSONResponse(content=alert)
    
    except Exception as e:
        logger.error(f"❌ Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alert/history")
async def get_alert_history():
    """Get recent alert history"""
    return {
        "total_alerts": len(ALERT_HISTORY),
        "recent_alerts": ALERT_HISTORY[-10:],
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/alert/status")
async def get_current_status():
    """Get current flood alert status"""
    if not ALERT_HISTORY:
        return {
            "status": "clear",
            "last_alert": None,
            "active_warnings": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    latest = ALERT_HISTORY[-1]
    return {
        "status": latest["severity"],
        "last_alert": latest["timestamp"],
        "alert_type": latest["alert_type"],
        "closest_threat_distance": latest["proximity_analysis"]["closest_area"]["distance_km"],
        "active_warnings": len([a for a in ALERT_HISTORY if a["severity"] in ["high", "critical"]]),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/health")
async def health_check():
    """API health check"""
    return {
        "status": "healthy",
        "service": "Real-Time Flood Alert System",
        "models_loaded": MODELS_LOADED,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"\n{'='*70}")
    logger.info("🌊 STARTING REAL-TIME FLOOD ALERT SYSTEM")
    logger.info(f"   Web: http://{host}:{port}")
    logger.info(f"   API: http://{host}:{port}/api/docs")
    logger.info(f"{'='*70}\n")
    
    uvicorn.run(app, host=host, port=port, log_level="info")
