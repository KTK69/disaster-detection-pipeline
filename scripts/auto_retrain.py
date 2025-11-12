"""
Automated Model Retraining Script
Triggers retraining via Google Colab or local training
Integrates with Jenkins CI/CD pipeline
"""
import os
import json
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutoRetrainer:
    """
    Manages automated model retraining
    Supports: Colab triggering, local training, metrics tracking
    """
    
    def __init__(self, model_type: str = 'flood'):
        self.model_type = model_type
        self.models_dir = Path('models/saved_models') / model_type
        self.data_dir = Path('data/retraining')
        self.logs_dir = Path('logs')
        self.metrics_file = self.logs_dir / f'{model_type}_retrain_metrics.json'
        
        # Create directories
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"🤖 Retrainer initialized for {model_type} model")
    
    def check_retraining_conditions(self) -> Dict[str, any]:
        """
        Check if retraining should be triggered
        
        Returns:
            Dict with condition checks and trigger decision
        """
        conditions = {
            'timestamp': datetime.now().isoformat(),
            'model_type': self.model_type,
            'should_retrain': False,
            'reasons': [],
            'warnings': []
        }
        
        # Check 1: New training data available
        if self._has_new_training_data():
            conditions['reasons'].append('New training data detected')
            conditions['should_retrain'] = True
        else:
            conditions['warnings'].append('No new training data found')
        
        # Check 2: Model performance degraded
        if self._check_performance_degradation():
            conditions['reasons'].append('Model performance degraded')
            conditions['should_retrain'] = True
        
        # Check 3: Data drift detected
        if self._check_drift():
            conditions['reasons'].append('Data drift detected')
            conditions['should_retrain'] = True
        
        # Check 4: Time-based trigger (e.g., weekly retrain)
        if self._check_schedule():
            conditions['reasons'].append('Scheduled retraining time')
            conditions['should_retrain'] = True
        
        logger.info(f"\n📋 Retraining Conditions Check:")
        logger.info(f"   Model: {self.model_type}")
        logger.info(f"   Should Retrain: {conditions['should_retrain']}")
        if conditions['reasons']:
            for reason in conditions['reasons']:
                logger.info(f"   ✅ {reason}")
        if conditions['warnings']:
            for warning in conditions['warnings']:
                logger.info(f"   ⚠️  {warning}")
        
        return conditions
    
    def _has_new_training_data(self) -> bool:
        """Check if new training data exists"""
        if not self.data_dir.exists():
            return False
        
        # Check for .tif, .tiff, or .npy files
        files = list(self.data_dir.glob('*.tif*')) + list(self.data_dir.glob('*.npy'))
        
        if files:
            logger.info(f"   Found {len(files)} new training images")
            return True
        
        return False
    
    def _check_performance_degradation(self) -> bool:
        """Check if latest model performance is below acceptable threshold"""
        try:
            metadata_files = sorted(
                self.models_dir.glob('model_metadata_*.json'),
                reverse=True
            )
            
            if not metadata_files:
                return False
            
            latest = metadata_files[0]
            with open(latest, 'r') as f:
                metadata = json.load(f)
            
            accuracy = metadata.get('final_val_acc', 1.0)
            iou = metadata.get('iou', 1.0)
            
            # Threshold for retraining
            if accuracy < 0.85 or iou < 0.35:
                logger.info(f"   Performance degraded: ACC={accuracy:.4f}, IoU={iou:.4f}")
                return True
            
        except Exception as e:
            logger.warning(f"   Could not check performance: {e}")
        
        return False
    
    def _check_drift(self) -> bool:
        """Check if data drift alert exists"""
        drift_marker = Path('data/drift_alert.txt')
        
        if drift_marker.exists():
            logger.info("   Drift alert detected")
            drift_marker.unlink()  # Remove after reading
            return True
        
        return False
    
    def _check_schedule(self) -> bool:
        """Check if scheduled retraining time (e.g., every 7 days)"""
        try:
            metrics = self._load_metrics()
            
            if not metrics or 'last_retrain' not in metrics:
                logger.info("   First time retraining - no schedule history")
                return True
            
            from datetime import timedelta
            last_retrain = datetime.fromisoformat(metrics['last_retrain'])
            days_since = (datetime.now() - last_retrain).days
            
            # Retrain every 7 days by default
            if days_since >= 7:
                logger.info(f"   Scheduled retrain due: {days_since} days since last")
                return True
            
        except Exception as e:
            logger.warning(f"   Could not check schedule: {e}")
        
        return False
    
    def trigger_colab_retraining(
        self,
        notebook_path: str = 'colab_notebooks/02_flood_model_training.ipynb',
        drive_folder_id: Optional[str] = None
    ) -> bool:
        """
        Trigger retraining via Google Colab
        
        Uses Google Colab API / nbconvert to run notebook
        """
        try:
            logger.info(f"\n🚀 Triggering Colab Retraining")
            logger.info(f"   Notebook: {notebook_path}")
            
            # Method 1: Check if using nbconvert
            cmd = [
                'jupyter', 'nbconvert',
                '--to', 'notebook',
                '--execute',
                notebook_path,
                '--output', notebook_path
            ]
            
            logger.info("   Attempting to run notebook...")
            result = subprocess.run(cmd, capture_output=True, timeout=3600)
            
            if result.returncode == 0:
                logger.info("✅ Colab notebook executed successfully")
                return True
            else:
                logger.warning(f"⚠️  Notebook execution failed: {result.stderr.decode()}")
                logger.info("   Hint: Run notebook manually in Colab")
                return False
                
        except FileNotFoundError:
            logger.warning("⚠️  Jupyter not found - install with: pip install jupyter")
            logger.info("   Manual Colab workflow required")
            return False
        except subprocess.TimeoutExpired:
            logger.error("❌ Notebook execution timed out (>1 hour)")
            return False
        except Exception as e:
            logger.error(f"❌ Error triggering Colab: {e}")
            return False
    
    def trigger_local_retraining(self) -> bool:
        """
        Trigger local model retraining
        Useful as fallback if Colab not available
        """
        try:
            logger.info(f"\n🚀 Triggering Local Retraining")
            
            # Run local training script
            cmd = [
                'python', '-c',
                '''
import os
os.chdir(".")
exec(open("colab_notebooks/utils/colab_helpers.py").read())
# Load and retrain model
exec(open("colab_notebooks/02_flood_model_training.ipynb").read())
'''
            ]
            
            logger.info("   Starting local training process...")
            result = subprocess.run(cmd, capture_output=True, timeout=1800)
            
            if result.returncode == 0:
                logger.info("✅ Local retraining completed successfully")
                return True
            else:
                logger.error(f"❌ Local training failed: {result.stderr.decode()}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Local training timed out (>30 min)")
            return False
        except Exception as e:
            logger.error(f"❌ Error in local retraining: {e}")
            return False
    
    def trigger_jenkins_retraining(
        self,
        jenkins_url: str = 'http://localhost:8080',
        job_name: str = 'disaster-detection-pipeline'
    ) -> bool:
        """
        Trigger Jenkins pipeline for retraining
        
        Args:
            jenkins_url: Jenkins server URL
            job_name: Name of retraining job
        
        Returns:
            True if successfully triggered
        """
        try:
            import requests
            
            logger.info(f"\n🚀 Triggering Jenkins Retraining")
            logger.info(f"   Jenkins URL: {jenkins_url}")
            logger.info(f"   Job: {job_name}")
            
            # Build trigger URL
            trigger_url = f"{jenkins_url}/job/{job_name}/build"
            
            # Optional: Include build parameters
            params = {
                'TRIGGER_REASON': 'automated_drift_detected',
                'MODEL_TYPE': self.model_type,
                'TIMESTAMP': datetime.now().isoformat()
            }
            
            # Attempt trigger
            response = requests.post(trigger_url, params=params, timeout=10)
            
            if response.status_code in [200, 201]:
                logger.info("✅ Jenkins build triggered successfully")
                return True
            else:
                logger.error(f"❌ Jenkins trigger failed: HTTP {response.status_code}")
                return False
                
        except ImportError:
            logger.warning("⚠️  requests library not installed")
            logger.info("   Install with: pip install requests")
            return False
        except Exception as e:
            logger.error(f"❌ Error triggering Jenkins: {e}")
            return False
    
    def verify_retrained_model(self) -> bool:
        """
        Verify that a new model was created after retraining
        """
        try:
            logger.info(f"\n✅ Verifying Retrained Model")
            
            # Find latest model file
            model_files = sorted(self.models_dir.glob('*.keras'), key=os.path.getmtime)
            
            if not model_files:
                logger.error("❌ No model files found!")
                return False
            
            latest_model = model_files[-1]
            logger.info(f"   Latest Model: {latest_model.name}")
            logger.info(f"   Size: {latest_model.stat().st_size / 1024 / 1024:.2f} MB")
            logger.info(f"   Modified: {datetime.fromtimestamp(latest_model.stat().st_mtime)}")
            
            # Check metadata
            metadata_file = self.models_dir / f"model_metadata_{latest_model.stem.split('_')[-1]}.json"
            
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                logger.info(f"\n   📊 Model Metrics:")
                logger.info(f"      Accuracy: {metadata.get('final_val_acc', 'N/A')}")
                logger.info(f"      IoU: {metadata.get('iou', 'N/A')}")
                logger.info(f"      Loss: {metadata.get('final_val_loss', 'N/A')}")
            
            logger.info("✅ Model verification passed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Model verification failed: {e}")
            return False
    
    def record_retrain_event(self, success: bool, method: str):
        """
        Record retraining event in metrics file
        """
        try:
            metrics = self._load_metrics()
            
            event = {
                'timestamp': datetime.now().isoformat(),
                'model_type': self.model_type,
                'method': method,
                'success': success
            }
            
            if 'retrain_history' not in metrics:
                metrics['retrain_history'] = []
            
            metrics['retrain_history'].append(event)
            metrics['last_retrain'] = datetime.now().isoformat()
            metrics['retrain_count'] = metrics.get('retrain_count', 0) + (1 if success else 0)
            
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            logger.info(f"✅ Retrain event recorded: {method} ({'SUCCESS' if success else 'FAILED'})")
            
        except Exception as e:
            logger.error(f"❌ Could not record retrain event: {e}")
    
    def _load_metrics(self) -> Dict:
        """Load metrics from file"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {}
    
    def generate_retrain_report(self) -> str:
        """Generate summary report of retraining status"""
        metrics = self._load_metrics()
        
        report = f"""
╔════════════════════════════════════════════════════╗
║   RETRAINING STATUS REPORT - {self.model_type.upper()}              ║
╚════════════════════════════════════════════════════╝

📊 Metrics:
   Total Retrains: {metrics.get('retrain_count', 0)}
   Last Retrain: {metrics.get('last_retrain', 'Never')}
   
📋 Recent History:
"""
        history = metrics.get('retrain_history', [])[-5:]  # Last 5
        
        for event in reversed(history):
            status = '✅' if event['success'] else '❌'
            report += f"   {status} {event['timestamp']} - {event['method']}\n"
        
        report += f"""
🎯 Next Actions:
   1. Monitor model accuracy (target: >85%)
   2. Check data drift periodically
   3. Review retraining logs in ./logs/
   4. Verify deployed model via API

"""
        return report


def main():
    """Main entry point for automated retraining"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Automated Model Retraining')
    parser.add_argument('--check', action='store_true', help='Check retraining conditions')
    parser.add_argument('--trigger', choices=['colab', 'local', 'jenkins'], 
                       help='Trigger retraining method')
    parser.add_argument('--model', default='flood', choices=['flood', 'fire'],
                       help='Model type to retrain')
    parser.add_argument('--verify', action='store_true', help='Verify retrained model')
    parser.add_argument('--report', action='store_true', help='Show retrain report')
    
    args = parser.parse_args()
    
    retrainer = AutoRetrainer(model_type=args.model)
    
    # Check conditions
    if args.check:
        conditions = retrainer.check_retraining_conditions()
        print(json.dumps(conditions, indent=2))
        return
    
    # Trigger retraining
    if args.trigger:
        success = False
        
        if args.trigger == 'colab':
            success = retrainer.trigger_colab_retraining()
        elif args.trigger == 'local':
            success = retrainer.trigger_local_retraining()
        elif args.trigger == 'jenkins':
            success = retrainer.trigger_jenkins_retraining()
        
        retrainer.record_retrain_event(success, args.trigger)
        
        if args.verify:
            retrainer.verify_retrained_model()
        
        return
    
    # Verify model
    if args.verify:
        retrainer.verify_retrained_model()
        return
    
    # Show report
    if args.report:
        print(retrainer.generate_retrain_report())
        return
    
    # Default: Check conditions and show report
    conditions = retrainer.check_retraining_conditions()
    
    if conditions['should_retrain']:
        print("\n🚨 RETRAINING TRIGGERED")
        print(f"Reasons: {', '.join(conditions['reasons'])}")
        print("\n💡 To trigger retraining:")
        print("   python scripts/auto_retrain.py --trigger colab")
        print("   python scripts/auto_retrain.py --trigger jenkins")
    else:
        print("\n✅ No retraining needed at this time")
    
    print(retrainer.generate_retrain_report())


if __name__ == '__main__':
    main()
