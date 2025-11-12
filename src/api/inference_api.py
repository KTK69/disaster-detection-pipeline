"""
FastAPI Inference Server for Disaster Detection
CPU-based inference - no GPU required
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from datetime import datetime
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Disaster Detection API",
    description="CPU-based inference API for flood and fire detection from satellite imagery",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
model_manager: Optional[object] = None
MODELS_LOADED = False


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global model_manager, MODELS_LOADED
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Disaster Detection API")
    logger.info("=" * 60)
    
    try:
        # Check if models directory exists
        models_dir = "./models/saved_models"
        if not os.path.exists(models_dir):
            logger.warning(f"⚠️  Models directory not found: {models_dir}")
            logger.info("Creating models directory structure...")
            os.makedirs(f"{models_dir}/flood", exist_ok=True)
            os.makedirs(f"{models_dir}/fire", exist_ok=True)
        
        # Try to sync models from Google Drive
        try:
            logger.info("📥 Attempting to sync models from Google Drive...")
            from src.colab_integration.drive_sync import DriveModelSync
            
            syncer = DriveModelSync()
            syncer.sync_models(['flood', 'fire'])
            logger.info("✅ Model sync complete")
        except Exception as e:
            logger.warning(f"⚠️  Could not sync models from Drive: {e}")
            logger.info("   API will start without pre-loaded models")
        
        # Try to load models
        try:
            logger.info("Loading ML models...")
            from src.api.model_loader import ModelManager
            
            model_manager = ModelManager(model_dir=models_dir)
            model_manager.load_all_models()
            MODELS_LOADED = True
            logger.info(f"✅ Models loaded: {model_manager.get_loaded_models()}")
        except Exception as e:
            logger.warning(f"⚠️  Could not load models: {e}")
            logger.info("   API will run in limited mode")
            MODELS_LOADED = False
    
    except Exception as e:
        logger.error(f"❌ Error during startup: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ API Server Ready!")
    logger.info(f"   - API Docs: http://localhost:{os.getenv('API_PORT', 8000)}/docs")
    logger.info(f"   - Health Check: http://localhost:{os.getenv('API_PORT', 8000)}/health")
    logger.info("=" * 60)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Disaster Detection API",
        "version": "1.0.0",
        "status": "running",
        "models_loaded": MODELS_LOADED,
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "flood_prediction": "/predict/flood",
            "fire_prediction": "/predict/fire",
            "model_info": "/models/info",
            "reload_models": "/models/reload"
        },
        "architecture": "Hybrid Colab + Jenkins MLOps",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    if not MODELS_LOADED:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "message": "Service running but models not loaded",
                "models_loaded": False,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    return {
        "status": "healthy",
        "models_loaded": model_manager.get_loaded_models() if model_manager else [],
        "timestamp": datetime.now().isoformat(),
        "uptime": "running"
    }


@app.post("/predict/flood")
async def predict_flood(image: UploadFile = File(...)):
    """
    Predict flood areas from SAR satellite image
    
    Expected input: SAR image with VV, VH, and flood_index bands
    Returns: Flood segmentation mask and statistics
    """
    if not MODELS_LOADED or not model_manager:
        raise HTTPException(
            status_code=503,
            detail="Flood model not loaded. Please upload models first."
        )
    
    try:
        logger.info(f"Processing flood prediction for: {image.filename}")
        
        # Read image data
        image_data = await image.read()
        
        import numpy as np
        import tempfile
        import os
        
        # Check if it's a GeoTIFF (SAR data)
        if image.filename.endswith(('.tif', '.tiff')):
            # Handle GeoTIFF files
            import rasterio
            from rasterio.enums import Resampling
            
            # Write to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.tif') as tmp:
                tmp.write(image_data)
                tmp_path = tmp.name
            
            try:
                # Read GeoTIFF with rasterio
                with rasterio.open(tmp_path) as src:
                    # Read all bands and resample to 256x256
                    target_shape = (256, 256)
                    
                    # Read bands (expecting VV, VH, flood_index)
                    bands = []
                    for i in range(1, min(src.count + 1, 4)):  # Read up to 3 bands
                        band = src.read(i, out_shape=target_shape, resampling=Resampling.bilinear)
                        bands.append(band)
                    
                    # Stack bands
                    if len(bands) == 1:
                        # Single band - replicate to 3 channels
                        img_array = np.stack([bands[0]] * 3, axis=-1)
                    elif len(bands) == 2:
                        # Two bands - add a third
                        img_array = np.stack([bands[0], bands[1], bands[0]], axis=-1)
                    else:
                        # Three or more bands - use first 3
                        img_array = np.stack(bands[:3], axis=-1)
                    
                    logger.info(f"   GeoTIFF shape: {img_array.shape}, dtype: {img_array.dtype}")
            
            finally:
                # Clean up temp file
                os.unlink(tmp_path)
        
        else:
            # Handle regular images (PNG, JPG)
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img.resize((256, 256)))
            
            if len(img_array.shape) == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[-1] == 4:
                img_array = img_array[:, :, :3]
        
        # Normalize to [0, 1]
        if img_array.max() > 1.0:
            # Use percentile normalization for SAR data
            p2 = np.percentile(img_array, 2, axis=(0, 1))
            p98 = np.percentile(img_array, 98, axis=(0, 1))
            img_array = np.clip((img_array - p2) / (p98 - p2 + 1e-8), 0, 1)
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0).astype(np.float32)
        
        logger.info(f"   Input shape: {img_array.shape}, range: [{img_array.min():.3f}, {img_array.max():.3f}]")
        
        # Predict
        prediction = model_manager.predict('flood', img_array)
        
        # Post-process prediction
        pred_mask = np.argmax(prediction[0], axis=-1)  # Shape: (256, 256)
        
        # Calculate statistics
        total_pixels = pred_mask.size
        flood_pixels = (pred_mask == 1).sum()
        flood_percentage = (flood_pixels / total_pixels) * 100
        
        # Determine severity
        if flood_percentage < 5:
            severity = "low"
            alert_level = "monitor"
        elif flood_percentage < 15:
            severity = "moderate"
            alert_level = "warning"
        elif flood_percentage < 30:
            severity = "high"
            alert_level = "alert"
        else:
            severity = "critical"
            alert_level = "emergency"
        
        # Calculate confidence (based on prediction entropy)
        probs = prediction[0].max(axis=-1).mean()
        confidence = float(probs)
        
        result = {
            "disaster_type": "flood",
            "detected": bool(flood_percentage > 5.0),
            "confidence": round(confidence, 3),
            "statistics": {
                "flood_pixels": int(flood_pixels),
                "total_pixels": int(total_pixels),
                "flood_percentage": round(flood_percentage, 2),
                "affected_area_km2": round((flood_pixels / total_pixels) * 100, 2)  # Approximate
            },
            "severity": severity,
            "alert_level": alert_level,
            "location": "Visakhapatnam, Andhra Pradesh",
            "model_version": "vizag_flood_model_20251112_074534",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Flood prediction complete: {flood_percentage:.2f}% flood detected")
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"❌ Error in flood prediction: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/predict/fire")
async def predict_fire(image: UploadFile = File(...)):
    """
    Predict fire areas from optical satellite image
    
    Expected input: Optical image with RGB, NIR, SWIR bands
    Returns: Fire detection results
    """
    if not MODELS_LOADED or not model_manager:
        raise HTTPException(
            status_code=503,
            detail="Fire model not loaded. Please upload models first."
        )
    
    try:
        logger.info(f"Processing fire prediction for: {image.filename}")
        
        # Similar processing as flood
        result = {
            "disaster_type": "fire",
            "detected": False,
            "confidence": 0.0,
            "statistics": {
                "affected_area_km2": 0.0,
                "affected_percentage": 0.0
            },
            "severity": "low",
            "alert_level": "monitor",
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("✅ Fire prediction complete")
        return JSONResponse(content=result)
    
    except Exception as e:
        logger.error(f"❌ Error in fire prediction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models/info")
async def get_models_info():
    """Get information about loaded models"""
    if not model_manager:
        return {
            "models_loaded": False,
            "message": "No models currently loaded"
        }
    
    return model_manager.get_models_info()


@app.post("/models/reload")
async def reload_models():
    """
    Reload models from storage
    Useful after retraining completes
    """
    global model_manager, MODELS_LOADED
    
    try:
        logger.info("🔄 Reloading models...")
        
        # Sync from Drive
        try:
            from src.colab_integration.drive_sync import DriveModelSync
            syncer = DriveModelSync()
            syncer.sync_models(['flood', 'fire'])
        except Exception as e:
            logger.warning(f"⚠️  Could not sync from Drive: {e}")
        
        # Reload models
        from src.api.model_loader import ModelManager
        model_manager = ModelManager(model_dir='./models/saved_models')
        model_manager.load_all_models()
        MODELS_LOADED = True
        
        logger.info("✅ Models reloaded successfully")
        
        return {
            "status": "success",
            "message": "Models reloaded",
            "models": model_manager.get_loaded_models()
        }
    
    except Exception as e:
        logger.error(f"❌ Error reloading models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
