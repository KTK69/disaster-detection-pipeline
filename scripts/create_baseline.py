"""
Create baseline data for drift detection from training data
"""
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

def create_baseline_from_training():
    """
    Create baseline features from training metadata
    """
    print("📊 Creating Drift Detection Baseline")
    print("=" * 60)
    
    # Paths
    baseline_dir = Path("data/baseline")
    baseline_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_path = Path("models/saved_models/flood/model_metadata_20251112_074534.json")
    
    if not metadata_path.exists():
        print("⚠️ Model metadata not found")
        return
    
    # Load metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    print(f"✅ Loaded metadata from: {metadata_path}")
    print(f"   Training samples: {metadata.get('training_samples', 'N/A')}")
    print(f"   Validation accuracy: {metadata.get('final_val_acc', 'N/A')}")
    print(f"   IoU: {metadata.get('iou', 'N/A')}")
    
    # Create baseline features (simplified - you can enhance this)
    baseline_features = {
        'mean_intensity': [],
        'std_intensity': [],
        'vv_mean': [],
        'vh_mean': [],
        'flood_index_mean': [],
        'timestamp': []
    }
    
    # Generate synthetic baseline (replace with actual data if available)
    n_samples = metadata.get('validation_samples', 2)
    
    for i in range(n_samples):
        baseline_features['mean_intensity'].append(np.random.uniform(50, 150))
        baseline_features['std_intensity'].append(np.random.uniform(20, 60))
        baseline_features['vv_mean'].append(np.random.uniform(60, 120))
        baseline_features['vh_mean'].append(np.random.uniform(40, 90))
        baseline_features['flood_index_mean'].append(np.random.uniform(10, 40))
        baseline_features['timestamp'].append(datetime.now().isoformat())
    
    # Save baseline
    baseline_df = pd.DataFrame(baseline_features)
    baseline_path = baseline_dir / "flood_baseline_features.csv"
    baseline_df.to_csv(baseline_path, index=False)
    
    print(f"\n✅ Baseline created: {baseline_path}")
    print(f"\n📈 Baseline Statistics:")
    print(baseline_df.describe())
    
    # Create configuration file
    config = {
        'model_name': metadata.get('model_path', 'vizag_flood_model_20251112_074534.keras'),
        'created_at': datetime.now().isoformat(),
        'baseline_samples': len(baseline_df),
        'drift_threshold': 0.5,
        'training_location': metadata.get('location', 'Visakhapatnam'),
        'model_accuracy': metadata.get('final_val_acc', 0.0),
        'model_iou': metadata.get('iou', 0.0)
    }
    
    config_path = baseline_dir / "drift_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration saved: {config_path}")
    
    print("\n" + "=" * 60)
    print("✅ Drift detection baseline ready!")
    print("\n💡 Next steps:")
    print("   1. Run drift monitor: python -m src.drift_detection.drift_monitor")
    print("   2. Set up cron job for continuous monitoring")
    print("   3. Configure alerts in Jenkins")

if __name__ == "__main__":
    create_baseline_from_training()
