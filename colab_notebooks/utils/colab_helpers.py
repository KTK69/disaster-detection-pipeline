"""
Helper functions for Google Colab notebooks
Handles authentication, Drive mounting, and GEE initialization
"""

def setup_colab_environment():
    """
    One-time setup for Colab notebooks
    Call this at the start of every notebook
    """
    print("🚀 Setting up Colab environment...")
    
    # Mount Google Drive
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=False)
        print("✅ Google Drive mounted")
    except Exception as e:
        print(f"⚠️ Could not mount Drive: {e}")
    
    # Install required packages
    print("📦 Installing required packages...")
    import subprocess
    import sys
    
    packages = [
        'earthengine-api',
        'geemap',
        'evidently',
        'rasterio',
        'scikit-image'
    ]
    
    for package in packages:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', package])
    
    print("✅ Packages installed")
    
    # Authenticate Earth Engine
    try:
        import ee
        ee.Authenticate()
        ee.Initialize()
        print("✅ Earth Engine initialized")
    except Exception as e:
        print(f"⚠️ Earth Engine initialization failed: {e}")
        print("   Please authenticate manually with ee.Authenticate()")
    
    print("✅ Colab environment ready!")


def get_drive_paths():
    """
    Return standard paths in Google Drive
    Modify based on your Drive structure
    """
    return {
        'data': '/content/drive/MyDrive/disaster_detection/data',
        'models': '/content/drive/MyDrive/disaster_detection/models',
        'logs': '/content/drive/MyDrive/disaster_detection/logs',
        'baseline': '/content/drive/MyDrive/disaster_detection/baseline'
    }


def ensure_drive_directories():
    """Create necessary directories in Google Drive"""
    import os
    paths = get_drive_paths()
    
    all_paths = [
        paths['data'],
        f"{paths['data']}/sar_training",
        f"{paths['data']}/optical_training",
        f"{paths['data']}/retraining",
        f"{paths['models']}/flood",
        f"{paths['models']}/fire",
        f"{paths['models']}/flood/checkpoints",
        f"{paths['models']}/fire/checkpoints",
        paths['logs'],
        paths['baseline']
    ]
    
    for path in all_paths:
        os.makedirs(path, exist_ok=True)
    
    print("✅ Drive directories created")


def load_model_from_drive(model_name, model_type='flood'):
    """
    Load trained model from Google Drive
    
    Args:
        model_name: Name of model file (e.g., 'flood_model_v1.h5')
        model_type: 'flood' or 'fire'
    
    Returns:
        Loaded TensorFlow model
    """
    import tensorflow as tf
    paths = get_drive_paths()
    model_path = f"{paths['models']}/{model_type}/{model_name}"
    
    try:
        model = tf.keras.models.load_model(model_path)
        print(f"✅ Loaded model from: {model_path}")
        return model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        raise


def save_model_to_drive(model, model_name, model_type='flood'):
    """
    Save trained model to Google Drive
    
    Args:
        model: TensorFlow/Keras model
        model_name: Name for saved model file
        model_type: 'flood' or 'fire'
    
    Returns:
        Path where model was saved
    """
    import os
    paths = get_drive_paths()
    save_dir = f"{paths['models']}/{model_type}"
    os.makedirs(save_dir, exist_ok=True)
    
    model_path = f"{save_dir}/{model_name}"
    
    try:
        model.save(model_path)
        print(f"✅ Model saved to: {model_path}")
        return model_path
    except Exception as e:
        print(f"❌ Error saving model: {e}")
        raise


def save_metrics_to_drive(metrics_dict, model_path):
    """
    Save training metrics alongside model
    
    Args:
        metrics_dict: Dictionary of metrics
        model_path: Path where model was saved
    """
    import json
    
    metrics_path = model_path.replace('.h5', '_metrics.json')
    
    try:
        with open(metrics_path, 'w') as f:
            json.dump(metrics_dict, f, indent=2)
        print(f"✅ Metrics saved to: {metrics_path}")
        return metrics_path
    except Exception as e:
        print(f"❌ Error saving metrics: {e}")
        raise


def list_available_models(model_type='flood'):
    """
    List all available models in Drive for a given type
    
    Args:
        model_type: 'flood' or 'fire'
    
    Returns:
        List of model file paths
    """
    import os
    import glob
    
    paths = get_drive_paths()
    model_dir = f"{paths['models']}/{model_type}"
    
    model_files = glob.glob(f"{model_dir}/*.h5")
    model_files.sort(key=os.path.getmtime, reverse=True)
    
    print(f"\n📋 Available {model_type} models ({len(model_files)}):")
    for i, model_file in enumerate(model_files, 1):
        filename = os.path.basename(model_file)
        size_mb = os.path.getsize(model_file) / (1024 * 1024)
        print(f"   {i}. {filename} ({size_mb:.2f} MB)")
    
    return model_files


def download_drive_file(file_id, destination_path):
    """
    Download a file from Google Drive by file ID
    
    Args:
        file_id: Google Drive file ID
        destination_path: Local path to save file
    """
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    import io
    
    # This requires Drive API credentials to be set up
    # For Colab, files are usually accessed via mounted Drive
    print(f"⚠️ For Colab, use mounted Drive paths instead")
    print(f"   Example: /content/drive/MyDrive/...")


def get_latest_model_path(model_type='flood'):
    """
    Get path to the latest trained model
    
    Args:
        model_type: 'flood' or 'fire'
    
    Returns:
        Path to latest model file
    """
    models = list_available_models(model_type)
    
    if not models:
        raise FileNotFoundError(f"No {model_type} models found in Drive")
    
    return models[0]


# Visualization helpers
def plot_training_history(history, save_path=None):
    """
    Plot training history
    
    Args:
        history: Keras History object
        save_path: Optional path to save plot
    """
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 4))
    
    # Loss
    axes[0].plot(history.history['loss'], label='Train Loss')
    axes[0].plot(history.history['val_loss'], label='Val Loss')
    axes[0].set_title('Loss')
    axes[0].set_xlabel('Epoch')
    axes[0].set_ylabel('Loss')
    axes[0].legend()
    axes[0].grid(True)
    
    # Accuracy
    axes[1].plot(history.history['accuracy'], label='Train Accuracy')
    axes[1].plot(history.history['val_accuracy'], label='Val Accuracy')
    axes[1].set_title('Accuracy')
    axes[1].set_xlabel('Epoch')
    axes[1].set_ylabel('Accuracy')
    axes[1].legend()
    axes[1].grid(True)
    
    # IoU (if available)
    if 'mean_io_u' in history.history:
        axes[2].plot(history.history['mean_io_u'], label='Train IoU')
        axes[2].plot(history.history['val_mean_io_u'], label='Val IoU')
        axes[2].set_title('IoU')
        axes[2].set_xlabel('Epoch')
        axes[2].set_ylabel('IoU')
        axes[2].legend()
        axes[2].grid(True)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"✅ Plot saved to: {save_path}")
    
    plt.show()


def visualize_predictions(model, X_sample, y_sample, num_samples=3):
    """
    Visualize model predictions
    
    Args:
        model: Trained model
        X_sample: Input images
        y_sample: Ground truth masks
        num_samples: Number of samples to visualize
    """
    import matplotlib.pyplot as plt
    import numpy as np
    
    predictions = model.predict(X_sample[:num_samples])
    
    fig, axes = plt.subplots(num_samples, 3, figsize=(12, 4 * num_samples))
    
    if num_samples == 1:
        axes = axes.reshape(1, -1)
    
    for i in range(num_samples):
        # Input image
        axes[i, 0].imshow(X_sample[i, :, :, 0], cmap='gray')
        axes[i, 0].set_title('Input Image')
        axes[i, 0].axis('off')
        
        # Ground truth
        axes[i, 1].imshow(y_sample[i, :, :, 0], cmap='Reds', alpha=0.6)
        axes[i, 1].set_title('Ground Truth')
        axes[i, 1].axis('off')
        
        # Prediction
        axes[i, 2].imshow(predictions[i, :, :, 0], cmap='Reds', alpha=0.6)
        axes[i, 2].set_title('Prediction')
        axes[i, 2].axis('off')
    
    plt.tight_layout()
    plt.show()


# Print helper info when imported
print("✅ Colab helpers loaded")
print("   Available functions:")
print("   - setup_colab_environment()")
print("   - get_drive_paths()")
print("   - save_model_to_drive(model, name, type)")
print("   - load_model_from_drive(name, type)")
print("   - plot_training_history(history)")
