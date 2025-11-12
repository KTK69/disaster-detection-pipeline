from fastapi import FastAPI, UploadFile, File
from tensorflow import keras
import numpy as np
from PIL import Image
import io

app = FastAPI(title="Vizag Flood Detection API")

# Load model
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
        "confidence": "high" if flood_percentage > 20 else "medium",
        "location": "Visakhapatnam"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "vizag_flood_20251112"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
