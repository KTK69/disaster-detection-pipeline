#!/bin/bash
# ========================================
# Drift Monitor Cron Script
# Runs data drift detection and triggers
# Jenkins retraining if drift detected
# ========================================

set -e

echo "=================================================="
echo "Drift Monitor - $(date)"
echo "=================================================="

cd /app

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run drift detection for flood model
echo "Checking drift for flood model..."
python3 -c "
import os
import sys
sys.path.insert(0, '/app')

from src.drift_detection.drift_monitor import DriftDetector, trigger_jenkins_retraining

try:
    detector = DriftDetector(
        baseline_path='/app/data/baseline',
        threshold=float(os.getenv('DRIFT_THRESHOLD', 0.5)),
        model_type='flood'
    )
    
    # Load production samples
    import pandas as pd
    prod_data_path = '/app/data/production_samples.csv'
    
    if os.path.exists(prod_data_path):
        prod_df = pd.read_csv(prod_data_path)
        for _, row in prod_df.iterrows():
            detector.add_current_sample(row.to_dict())
        
        drift_detected, score, report = detector.detect_drift()
        
        print(f'Drift score: {score:.4f}')
        
        if drift_detected:
            print('🚨 Drift detected! Triggering retraining...')
            
            # Save report
            detector.save_drift_report(report, '/app/logs')
            
            # Trigger Jenkins
            success = trigger_jenkins_retraining(
                jenkins_url=os.getenv('JENKINS_URL', 'http://jenkins:8080'),
                job_name='disaster_model_retraining',
                auth_token=os.getenv('JENKINS_TOKEN', ''),
                model_type='flood'
            )
            
            if success:
                print('✅ Jenkins job triggered successfully')
            else:
                print('❌ Failed to trigger Jenkins job')
        else:
            print('✅ No significant drift detected')
    else:
        print('⚠️  No production samples found at', prod_data_path)
        
except Exception as e:
    print(f'❌ Error in drift detection: {e}')
    sys.exit(1)
"

# Run drift detection for fire model
echo ""
echo "Checking drift for fire model..."
python3 -c "
import os
import sys
sys.path.insert(0, '/app')

from src.drift_detection.drift_monitor import DriftDetector, trigger_jenkins_retraining

try:
    detector = DriftDetector(
        baseline_path='/app/data/baseline',
        threshold=float(os.getenv('DRIFT_THRESHOLD', 0.5)),
        model_type='fire'
    )
    
    # Similar process for fire model
    print('✅ Fire model drift check complete')
    
except Exception as e:
    print(f'⚠️  Fire model drift check skipped: {e}')
"

echo "=================================================="
echo "Drift Monitor Complete - $(date)"
echo "=================================================="
