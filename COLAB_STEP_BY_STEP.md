# 🚀 Google Colab Step-by-Step Guide
## Training Your Flood Detection Model with Free GPU

This guide walks you through **exactly what to do** in Google Colab to train your first model.

---

## 📋 Prerequisites (Do This First!)

### 1. Get Google Cloud Credentials
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Create a new project or select existing
- Enable **Google Earth Engine API** and **Google Drive API**
- Create Service Account → Download `service-account-key.json`
- Save it to `c:\Docs\project\DevOps\service-account-key.json`

### 2. Authenticate Earth Engine
Run this **ONCE** on your local machine:
```powershell
python -c "import ee; ee.Authenticate()"
```
This will open a browser - sign in with your Google account and authorize.

### 3. Upload Files to Google Drive
Create this folder structure in your Google Drive:
```
MyDrive/
└── disaster_detection/
    ├── models/
    │   └── flood/
    ├── data/
    │   └── baseline/
    └── notebooks/
        └── utils/
```

Upload these files:
- `colab_notebooks/02_flood_model_training.ipynb` → `MyDrive/disaster_detection/notebooks/`
- `colab_notebooks/utils/colab_helpers.py` → `MyDrive/disaster_detection/notebooks/utils/`

---

## 🎯 Step-by-Step Execution in Colab

### **STEP 1: Open Notebook in Colab**

1. Go to [Google Colab](https://colab.research.google.com/)
2. Click **File → Open notebook**
3. Select **Google Drive** tab
4. Navigate to `MyDrive/disaster_detection/notebooks/02_flood_model_training.ipynb`
5. Click to open

### **STEP 2: Enable GPU (CRITICAL!)**

1. In Colab, click **Runtime → Change runtime type**
2. Set **Hardware accelerator** to **GPU**
3. Click **Save**
4. Verify GPU: Run this in a cell:
   ```python
   import tensorflow as tf
   print(tf.config.list_physical_devices('GPU'))
   ```
   You should see `[PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]`

### **STEP 3: Mount Google Drive**

Run this cell **FIRST**:
```python
# Mount Google Drive
from google.colab import drive
drive.mount('/content/drive')

# Verify
import os
print(os.listdir('/content/drive/MyDrive/disaster_detection'))
# Should show: ['models', 'data', 'notebooks']
```

**What happens:**
- Browser popup asks for permission
- Click your Google account
- Click "Allow"
- Drive is now accessible at `/content/drive/MyDrive/`

### **STEP 4: Install Dependencies**

Run this cell:
```python
# Install required packages
!pip install -q earthengine-api geemap rasterio scikit-learn evidently

# Authenticate Earth Engine
import ee
ee.Authenticate()  # Follow the prompt
ee.Initialize()

print("✅ All dependencies installed!")
```

**What happens:**
- Installs Earth Engine SDK, geemap (for visualizations), rasterio (for satellite data)
- Browser popup for Earth Engine auth - sign in and copy code back
- Takes ~2-3 minutes

### **STEP 5: Run Setup Cell (Cell 1)**

Click **Run** on the first code cell:
```python
# Cell 1: Setup Colab Environment
```

**What happens:**
- Adds `utils` folder to Python path
- Imports helper functions from `colab_helpers.py`
- Sets up TensorFlow and Earth Engine
- Prints GPU confirmation

**Expected Output:**
```
🚀 Setting up Colab environment for Flood Model Training
============================================================
✅ TensorFlow version: 2.15.0
✅ GPU Available: [PhysicalDevice(name='/physical_device:GPU:0', device_type='GPU')]
✅ Earth Engine initialized
============================================================
```

### **STEP 6: Download SAR Training Data (Cells 2-3)**

**Cell 2** - Visualize Area of Interest:
```python
# Cell 2: Download SAR Training Data
```

**What happens:**
- Defines Mumbai flood-prone region (you can change coordinates)
- Creates interactive map showing the area
- Map appears below the cell

**Cell 3** - Actually Download Data:
```python
# Cell 3: Download Function
```

**What happens:**
- Queries Sentinel-1 SAR satellite imagery from 2023-2024
- Downloads up to 30 images (takes ~5-10 minutes)
- Saves to `/content/drive/MyDrive/disaster_detection/data/sar_training/`

**Expected Output:**
```
📥 Downloading SAR training data from Google Earth Engine...
Found 47 SAR images
  Processing image 1/30
  Processing image 2/30
  ...
✅ Downloaded 30 images to /content/drive/MyDrive/disaster_detection/data/sar_training
```

### **STEP 7: Build the U-Net Model (Cell 4)**

Run Cell 4:
```python
# Cell 4: Build U-Net Model
```

**What happens:**
- Constructs U-Net architecture (encoder-decoder for image segmentation)
- Compiles with Adam optimizer and binary cross-entropy loss
- Prints model architecture summary

**Expected Output:**
```
✅ U-Net model created
Model: "model"
_________________________________________________________________
Layer (type)                 Output Shape              Param #   
=================================================================
input_1 (InputLayer)         [(None, 256, 256, 3)]     0         
conv2d (Conv2D)              (None, 256, 256, 64)      1792      
...
Total params: 31,031,685
Trainable params: 31,031,685
Non-trainable params: 0
```

### **STEP 8: Train the Model (Cell 5) - THIS IS THE MAIN EVENT! 🔥**

Run Cell 5:
```python
# Cell 5: Training
```

**What happens:**
- Loads the SAR images you downloaded (or uses dummy data if download failed)
- Trains U-Net model on Colab's **FREE GPU**
- Takes **30-60 minutes** depending on data size
- Auto-saves checkpoints to Drive every epoch

**Expected Output:**
```
🔥 Starting model training...
⚠️  Using dummy data for demonstration
Epoch 1/50
5/5 [==============================] - 12s 2s/step - loss: 0.6854 - accuracy: 0.5234 - mean_io_u: 0.2567 - val_loss: 0.6789 - val_accuracy: 0.5456 - val_mean_io_u: 0.2789
Epoch 2/50
5/5 [==============================] - 10s 2s/step - loss: 0.6421 - accuracy: 0.5987 - mean_io_u: 0.3123 - val_loss: 0.6234 - val_accuracy: 0.6123 - val_mean_io_u: 0.3456
...
Epoch 45/50
5/5 [==============================] - 10s 2s/step - loss: 0.1234 - accuracy: 0.9456 - mean_io_u: 0.8789 - val_loss: 0.1456 - val_accuracy: 0.9234 - val_mean_io_u: 0.8567
Restoring model weights from the end of the best epoch: 35.
✅ Training complete!
```

**Important Notes:**
- ⏰ **Don't close the browser** - training will stop!
- 💾 Checkpoints auto-save to Drive - you can resume if interrupted
- 📊 Watch the `val_loss` - it should decrease over time
- 🎯 Training stops automatically if validation loss stops improving (Early Stopping)

### **STEP 9: Evaluate and Save Final Model (Cell 6)**

Run Cell 6:
```python
# Cell 6: Evaluate and Save
```

**What happens:**
- Evaluates final model on validation set
- Saves model to Drive with timestamp: `flood_model_20250112_143052.h5`
- Saves metrics JSON file with accuracy, IoU, etc.

**Expected Output:**
```
📊 Validation Metrics:
   Loss: 0.1456
   Accuracy: 0.9234
   IoU: 0.8567

✅ Model and metrics saved!
   Model: /content/drive/MyDrive/disaster_detection/models/flood/flood_model_20250112_143052.h5
```

**🎉 YOUR MODEL IS NOW IN GOOGLE DRIVE!** 🎉

### **STEP 10: Create Baseline for Drift Detection (Cell 7)**

Run Cell 7:
```python
# Cell 7: Create Baseline for Drift Detection
```

**What happens:**
- Extracts statistical features from validation data
- Creates `flood_baseline_features.csv` with mean intensity, std, etc.
- Saves to Drive for drift monitoring

**Expected Output:**
```
📊 Creating baseline features for drift detection...
✅ Baseline saved to: /content/drive/MyDrive/disaster_detection/data/baseline/flood_baseline_features.csv

📈 Baseline Statistics:
       mean_intensity  std_intensity    vv_mean    vh_mean  flood_index_mean
count        5.000000       5.000000   5.000000   5.000000          5.000000
mean         0.234567       0.456789   0.123456   0.234567          0.345678
std          0.023456       0.034567   0.012345   0.023456          0.034567
min          0.210000       0.420000   0.110000   0.210000          0.310000
max          0.260000       0.490000   0.140000   0.260000          0.380000
```

---

## ✅ Verification - Check Your Drive

After completing all steps, verify in Google Drive:

```
MyDrive/disaster_detection/
├── models/flood/
│   ├── flood_model_20250112_143052.h5  ← YOUR TRAINED MODEL
│   ├── flood_model_20250112_143052_metrics.json
│   └── checkpoints/
│       └── model_35_0.1456.h5
├── data/
│   ├── sar_training/  ← Downloaded SAR images
│   └── baseline/
│       └── flood_baseline_features.csv  ← Drift detection baseline
└── notebooks/
    └── (your notebook)
```

---

## 🔄 What Happens Next (Automatic!)

Once you have a trained model in Drive:

1. **Your local Jenkins** checks Drive every hour (cron job)
2. Jenkins finds new model → downloads it
3. FastAPI server **auto-reloads** with new model
4. Drift monitor uses baseline CSV to detect data shifts
5. When drift detected → Jenkins triggers **THIS NOTEBOOK AGAIN**
6. Colab auto-retrains with new data → uploads to Drive
7. Loop continues! ♻️

---

## 🐛 Troubleshooting

### "RuntimeError: GPU out of memory"
**Solution:** Reduce batch size in Cell 5:
```python
batch_size=2  # Instead of 4
```

### "ModuleNotFoundError: No module named 'colab_helpers'"
**Solution:** 
1. Check `colab_helpers.py` is uploaded to Drive
2. Verify path in Cell 1 matches your Drive structure

### "Earth Engine initialization failed"
**Solution:**
```python
# In a new cell, run:
import ee
ee.Authenticate()
ee.Initialize(project='your-gcp-project-id')
```

### "Training is too slow"
**Solution:**
- Verify GPU is enabled (Runtime → Change runtime type)
- Reduce `max_images` in Cell 3 (try 10-20 images for testing)
- Use smaller image patches (128x128 instead of 256x256)

### "Colab disconnected during training"
**Solution:**
- Checkpoints are saved to Drive - you can resume
- Install Colab Auto-Clicker extension to prevent disconnection
- Consider upgrading to Colab Pro ($10/month) for longer sessions

---

## 📝 Quick Reference - Cell Order

| Cell # | What It Does | Time | Required |
|--------|-------------|------|----------|
| Mount Drive | Connect to Google Drive | 10s | ✅ Yes |
| Install Deps | Install packages + auth | 2-3min | ✅ Yes |
| Cell 1 | Setup environment | 30s | ✅ Yes |
| Cell 2 | Visualize AOI | 5s | ⚠️ Optional |
| Cell 3 | Download SAR data | 5-10min | ✅ Yes |
| Cell 4 | Build U-Net model | 10s | ✅ Yes |
| Cell 5 | **TRAIN MODEL** | 30-60min | ✅ **CRITICAL** |
| Cell 6 | Save model + metrics | 30s | ✅ Yes |
| Cell 7 | Create baseline | 20s | ✅ Yes |

---

## 🎯 Success Criteria

You're done when you see:
- ✅ Model file in Drive (`.h5` file, ~100MB)
- ✅ Metrics JSON file with accuracy > 0.85
- ✅ Baseline CSV file with features
- ✅ No error messages in any cell

**Total Time:** ~45-90 minutes (mostly training time)

---

## 🚀 Next Steps After Training

1. **Go back to your local machine**
2. **Test Drive sync:**
   ```powershell
   curl -X POST http://localhost:8000/models/reload
   ```
3. **Check API loads model:**
   ```powershell
   curl http://localhost:8000/health
   ```
4. **Make prediction:**
   ```powershell
   curl -X POST http://localhost:8000/predict/flood -F "image=@test_image.tif"
   ```

Your automation is now **UNLOCKED**! 🎉
