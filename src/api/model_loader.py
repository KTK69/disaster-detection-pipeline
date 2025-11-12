"""
Model loader and manager for inference API
Handles loading models from disk and caching in memory
"""
import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path
import tensorflow as tf
from tensorflow import keras

logger = logging.getLogger(__name__)


# Define custom IoU metric class (matches the one used during training)
class IoUMetric(keras.metrics.Metric):
    """Custom IoU metric for flood detection"""
    
    def __init__(self, name='iou', **kwargs):
        super(IoUMetric, self).__init__(name=name, **kwargs)
        self.iou_sum = self.add_weight(name='iou_sum', initializer='zeros')
        self.count = self.add_weight(name='count', initializer='zeros')
    
    def update_state(self, y_true, y_pred, sample_weight=None):
        # Convert predictions to class labels
        y_pred = tf.argmax(y_pred, axis=-1)
        y_true = tf.cast(y_true, tf.int64)
        
        # Flatten tensors
        y_true_flat = tf.reshape(y_true, [-1])
        y_pred_flat = tf.reshape(y_pred, [-1])
        
        # Calculate IoU for flood class (class 1)
        y_true_flood = tf.cast(tf.equal(y_true_flat, 1), tf.float32)
        y_pred_flood = tf.cast(tf.equal(y_pred_flat, 1), tf.float32)
        
        intersection = tf.reduce_sum(y_true_flood * y_pred_flood)
        union = tf.reduce_sum(y_true_flood) + tf.reduce_sum(y_pred_flood) - intersection
        
        iou = tf.where(union > 0, intersection / union, 1.0)
        
        self.iou_sum.assign_add(iou)
        self.count.assign_add(1.0)
    
    def result(self):
        return self.iou_sum / self.count
    
    def reset_state(self):
        self.iou_sum.assign(0.0)
        self.count.assign(0.0)
    
    def get_config(self):
        """Serialize metric configuration"""
        config = super().get_config()
        return config


class ModelManager:
    """
    Manages loading and caching of ML models
    """
    
    def __init__(self, model_dir: str = './models/saved_models'):
        self.model_dir = Path(model_dir)
        self.models: Dict[str, object] = {}
        self.model_info: Dict[str, Dict] = {}
        
        logger.info(f"Initializing ModelManager with directory: {model_dir}")
    
    def load_all_models(self):
        """Load all available models"""
        model_types = ['flood', 'fire']
        
        for model_type in model_types:
            try:
                self.load_model(model_type)
            except FileNotFoundError as e:
                logger.warning(f"⚠️  No {model_type} model found: {e}")
            except Exception as e:
                logger.error(f"❌ Failed to load {model_type} model: {e}")
    
    def load_model(self, model_type: str):
        """
        Load a specific model type
        
        Args:
            model_type: 'flood' or 'fire'
        
        Returns:
            Loaded model object
        """
        model_path = self._get_latest_model_path(model_type)
        
        if not model_path:
            raise FileNotFoundError(f"No model found for type: {model_type}")
        
        logger.info(f"Loading {model_type} model from: {model_path}")
        
        try:
            # Try TensorFlow/Keras first
            import tensorflow as tf
            
            # Load model with custom objects
            custom_objects = {'IoUMetric': IoUMetric}
            model = tf.keras.models.load_model(str(model_path), custom_objects=custom_objects, compile=False)
            
            # Re-compile for CPU optimization
            model.compile(
                optimizer='adam',
                loss='sparse_categorical_crossentropy',
                metrics=['accuracy', IoUMetric()]
            )
            
            logger.info(f"✅ Loaded TensorFlow model: {model_type}")
            logger.info(f"   Input shape: {model.input_shape}")
            logger.info(f"   Output shape: {model.output_shape}")
            
        except Exception as tf_error:
            logger.warning(f"Could not load as TensorFlow model: {tf_error}")
            
            # Try PyTorch
            try:
                import torch
                model = torch.load(str(model_path), map_location='cpu')
                model.eval()
                logger.info(f"✅ Loaded PyTorch model: {model_type}")
            except Exception as torch_error:
                logger.error(f"Could not load as PyTorch model: {torch_error}")
                raise RuntimeError(f"Failed to load model: {model_path}")
        
        # Cache model
        self.models[model_type] = model
        
        # Load metadata
        metadata_path = str(model_path).replace('.keras', '_metadata.json').replace('.h5', '_metrics.json').replace('.pt', '_metrics.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                self.model_info[model_type] = json.load(f)
            logger.info(f"   Loaded metadata from: {metadata_path}")
        
        return model
    
    def _get_latest_model_path(self, model_type: str) -> Optional[Path]:
        """Find the latest model file for a given type"""
        model_dir = self.model_dir / model_type
        
        if not model_dir.exists():
            logger.warning(f"Model directory not found: {model_dir}")
            return None
        
        # Look for .keras (new format), .h5 (Keras) or .pt (PyTorch) files
        model_files = list(model_dir.glob("*.keras")) + list(model_dir.glob("*.h5")) + list(model_dir.glob("*.pt"))
        
        if not model_files:
            logger.warning(f"No model files found in: {model_dir}")
            return None
        
        # Sort by modification time, get latest
        model_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        latest = model_files[0]
        logger.info(f"   Latest model: {latest.name}")
        
        return latest
    
    def predict(self, model_type: str, input_data):
        """
        Make prediction using specified model
        
        Args:
            model_type: 'flood' or 'fire'
            input_data: Preprocessed input array
        
        Returns:
            Model prediction
        """
        if model_type not in self.models:
            raise ValueError(f"Model not loaded: {model_type}")
        
        model = self.models[model_type]
        
        # Check if TensorFlow or PyTorch
        try:
            import tensorflow as tf
            if isinstance(model, tf.keras.Model):
                prediction = model.predict(input_data, verbose=0)
                return prediction
        except:
            pass
        
        try:
            import torch
            if isinstance(model, torch.nn.Module):
                with torch.no_grad():
                    input_tensor = torch.from_numpy(input_data).float()
                    prediction = model(input_tensor)
                    return prediction.numpy()
        except:
            pass
        
        raise RuntimeError(f"Unknown model type for: {model_type}")
    
    def get_loaded_models(self) -> list:
        """Get list of currently loaded models"""
        return list(self.models.keys())
    
    def get_models_info(self) -> Dict:
        """Get metadata about loaded models"""
        info = {}
        
        for model_type in self.models.keys():
            model_path = self._get_latest_model_path(model_type)
            
            info[model_type] = {
                "loaded": True,
                "model_path": str(model_path) if model_path else None,
                "last_modified": datetime.fromtimestamp(
                    model_path.stat().st_mtime
                ).isoformat() if model_path else None,
                "metadata": self.model_info.get(model_type, {})
            }
        
        return info
