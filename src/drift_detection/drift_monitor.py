"""
Data drift detection system using Evidently AI
Monitors incoming predictions for distribution shifts
Triggers retraining when significant drift detected
"""
import pandas as pd
import numpy as np
import os
import json
import logging
from datetime import datetime
from typing import Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class DriftDetector:
    """
    Detects data drift in production satellite imagery
    Uses Evidently AI for statistical drift detection
    """
    
    def __init__(
        self,
        baseline_path: str,
        threshold: float = 0.5,
        model_type: str = 'flood'
    ):
        self.baseline_path = Path(baseline_path)
        self.threshold = threshold
        self.model_type = model_type
        self.baseline_data = None
        self.current_data = []
        
        try:
            self.baseline_data = self._load_baseline()
        except FileNotFoundError:
            logger.warning(f"⚠️  No baseline found for {model_type}")
            logger.info("   Train initial model to generate baseline")
    
    def _load_baseline(self) -> pd.DataFrame:
        """Load baseline feature data from CSV"""
        baseline_file = self.baseline_path / f'{self.model_type}_baseline_features.csv'
        
        if not baseline_file.exists():
            raise FileNotFoundError(f"Baseline file not found: {baseline_file}")
        
        df = pd.read_csv(baseline_file)
        logger.info(f"✅ Loaded baseline: {len(df)} samples")
        
        return df
    
    def add_current_sample(self, features: Dict):
        """
        Add a new production sample for drift monitoring
        
        Args:
            features: Dict of extracted features from production image
        """
        self.current_data.append(features)
    
    def detect_drift(self) -> Tuple[bool, float, Dict]:
        """
        Check for data drift between baseline and current production data
        
        Returns:
            (drift_detected, drift_score, detailed_report)
        """
        if self.baseline_data is None:
            logger.warning("No baseline data available")
            return False, 0.0, {"message": "No baseline"}
        
        if len(self.current_data) < 30:
            logger.warning(f"Insufficient current data: {len(self.current_data)} samples")
            logger.info("   Need at least 30 samples for drift detection")
            return False, 0.0, {"message": "Insufficient data"}
        
        try:
            from evidently.report import Report
            from evidently.metrics import DatasetDriftMetric, DataDriftTable
            
            # Convert current data to DataFrame
            current_df = pd.DataFrame(self.current_data)
            
            logger.info(f"Running drift detection...")
            logger.info(f"  Baseline: {len(self.baseline_data)} samples")
            logger.info(f"  Current: {len(current_df)} samples")
            
            # Create Evidently report
            report = Report(metrics=[
                DatasetDriftMetric(),
                DataDriftTable()
            ])
            
            # Run drift detection
            report.run(
                reference_data=self.baseline_data,
                current_data=current_df
            )
            
            # Extract results
            report_dict = report.as_dict()
            
            # Get drift metrics
            dataset_drift = report_dict['metrics'][0]['result']['dataset_drift']
            drift_score = report_dict['metrics'][0]['result']['drift_share']
            
            # Detailed column-wise drift
            drift_details = {}
            if len(report_dict['metrics']) > 1:
                drift_by_columns = report_dict['metrics'][1]['result'].get('drift_by_columns', {})
                drift_details = drift_by_columns
            
            # Determine if retraining needed
            drift_detected = dataset_drift or (drift_score > self.threshold)
            
            logger.info(f"\n📊 Drift Detection Results:")
            logger.info(f"   Dataset Drift: {dataset_drift}")
            logger.info(f"   Drift Score: {drift_score:.4f}")
            logger.info(f"   Threshold: {self.threshold}")
            logger.info(f"   {'🚨 DRIFT DETECTED' if drift_detected else '✅ No significant drift'}")
            
            return drift_detected, drift_score, {
                'dataset_drift': dataset_drift,
                'drift_score': drift_score,
                'drift_details': drift_details,
                'samples_analyzed': len(current_df),
                'timestamp': datetime.now().isoformat()
            }
            
        except ImportError:
            logger.error("❌ Evidently AI not installed")
            logger.info("   Install with: pip install evidently")
            return False, 0.0, {"message": "Evidently not installed"}
        
        except Exception as e:
            logger.error(f"❌ Error in drift detection: {e}")
            return False, 0.0, {"message": str(e)}
    
    def save_drift_report(self, report_data: Dict, output_dir: str = './logs'):
        """Save drift detection report to JSON"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        report_file = output_path / f'drift_report_{self.model_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"✅ Drift report saved: {report_file}")
        
        return report_file
    
    def reset_current_data(self):
        """Clear current data collection after retraining"""
        self.current_data = []
        logger.info("Current data buffer reset")


def extract_features_from_image(image_array: np.ndarray) -> Dict:
    """
    Extract statistical features from satellite image for drift detection
    
    Args:
        image_array: Preprocessed image array
    
    Returns:
        Dictionary of features
    """
    features = {
        'mean_intensity': float(np.mean(image_array)),
        'std_intensity': float(np.std(image_array)),
        'min_intensity': float(np.min(image_array)),
        'max_intensity': float(np.max(image_array)),
        'median_intensity': float(np.median(image_array)),
    }
    
    # Channel-wise statistics if multi-channel
    if len(image_array.shape) == 3 and image_array.shape[2] > 1:
        for i in range(min(image_array.shape[2], 3)):  # Max 3 channels
            channel = image_array[:, :, i]
            features[f'channel_{i}_mean'] = float(np.mean(channel))
            features[f'channel_{i}_std'] = float(np.std(channel))
    
    return features


def trigger_jenkins_retraining(
    jenkins_url: str,
    job_name: str,
    auth_token: str,
    model_type: str
) -> bool:
    """
    Trigger Jenkins retraining pipeline via REST API
    
    Args:
        jenkins_url: Jenkins server URL
        job_name: Name of the Jenkins job to trigger
        auth_token: Jenkins API token
        model_type: 'flood' or 'fire'
    
    Returns:
        True if successful
    """
    try:
        import requests
        
        # Jenkins API endpoint
        trigger_url = f"{jenkins_url}/job/{job_name}/buildWithParameters"
        
        # Parameters to pass to Jenkins
        params = {
            'MODEL_TYPE': model_type,
            'TRIGGERED_BY': 'drift_detection',
            'TIMESTAMP': datetime.now().isoformat()
        }
        
        # Get credentials from environment
        jenkins_user = os.getenv('JENKINS_USER', 'admin')
        
        logger.info(f"Triggering Jenkins job: {job_name}")
        logger.info(f"  URL: {trigger_url}")
        logger.info(f"  Model: {model_type}")
        
        # Make request
        response = requests.post(
            trigger_url,
            params=params,
            auth=(jenkins_user, auth_token),
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"✅ Jenkins job triggered successfully")
            return True
        else:
            logger.error(f"❌ Failed to trigger Jenkins: HTTP {response.status_code}")
            logger.error(f"   Response: {response.text}")
            return False
            
    except ImportError:
        logger.error("❌ requests library not installed")
        return False
    except Exception as e:
        logger.error(f"❌ Error triggering Jenkins: {e}")
        return False


if __name__ == '__main__':
    # Example usage / testing
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("Testing Drift Detection")
    print("=" * 60)
    
    detector = DriftDetector(
        baseline_path='./data/baseline',
        threshold=0.5,
        model_type='flood'
    )
    
    # Simulate adding production samples
    print("\nSimulating production data...")
    for i in range(50):
        sample_features = {
            'mean_intensity': np.random.normal(0.5, 0.1),
            'std_intensity': np.random.normal(0.2, 0.05),
            'channel_0_mean': np.random.normal(0.4, 0.1),
            'channel_1_mean': np.random.normal(0.3, 0.1),
        }
        detector.add_current_sample(sample_features)
    
    # Check for drift
    drift_detected, score, report = detector.detect_drift()
    
    if drift_detected:
        print("\n🚨 Drift detected! Would trigger retraining...")
        detector.save_drift_report(report)
    else:
        print("\n✅ No drift detected")
