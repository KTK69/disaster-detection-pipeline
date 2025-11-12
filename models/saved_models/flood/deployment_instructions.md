# Vizag Flood Detection Model - Deployment Guide

## Model Information
- Model Name: vizag_flood_model_20251112_074534.keras
- Training Date: 2025-11-12
- Location: Visakhapatnam, Andhra Pradesh
- Validation Accuracy: 96.71%
- IoU Score: 0.4095

## Files Included
1. vizag_flood_model_20251112_074534.keras - Trained U-Net model (118 MB)
2. model_metadata.json - Training configuration and metrics
3. deployment_instructions.md - This file

## Quick Start (Local Deployment)

### 1. Install Dependencies

pip install tensorflow numpy pillow rasterio fastapi uvicorn

### 2. Create FastAPI Server (app.py)
Save this as app.py in the same directory as your model:

from fastapi import FastAPI, UploadFile, File
from tensorflow import keras
import numpy as np
from PIL import Image
import io

app = FastAPI()
model = keras.models.load_model("vizag_flood_model_20251112_074534.keras")

@app.post("/predict")
async def predict_flood(file: UploadFile = File(...)):
    image_data = await file.read()
    image = Image.open(io.BytesIO(image_data))
    image = image.resize((256, 256))
    
    img_array = np.array(image)
    if img_array.ndim == 2:
        img_array = np.stack([img_array] * 3, axis=-1)
    elif img_array.shape[-1] == 4:
        img_array = img_array[:, :, :3]
    
    img_array = img_array / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    
    prediction = model.predict(img_array)
    flood_mask = np.argmax(prediction[0], axis=-1)
    flood_percentage = (flood_mask == 1).sum() / flood_mask.size * 100
    
    return {
        "flood_detected": bool(flood_percentage > 5),
        "flood_percentage": float(flood_percentage),
        "confidence": "high" if flood_percentage > 20 else "medium"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

### 3. Run Server
python app.py

### 4. Test API
curl http://localhost:8000/health
curl -X POST http://localhost:8000/predict -F "file=@image.tif"

## Docker Deployment
Create Dockerfile:
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

Build and run:
docker build -t flood-detection .
docker run -p 8000:8000 flood-detection

## .env Configuration
Add to your .env file:
MODEL_PATH=models/flood/vizag_flood_model_20251112_074534.keras
MODEL_VALIDATION_ACCURACY=0.9671
MODEL_VALIDATION_IOU=0.4095

## Support
Email: tanveerkrishna@gmail.com
