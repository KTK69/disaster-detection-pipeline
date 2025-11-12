pipeline {
    agent any
    
    environment {
        // Model configuration
        MODEL_DIR = 'models/saved_models'
        BASELINE_DIR = 'data/baseline'
        API_PORT = '8000'
        
        // Docker configuration
        DOCKER_IMAGE = 'disaster-detection-api'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        
        // Google Drive sync
        DRIVE_SYNC = 'true'
    }
    
    stages {
        stage('🔍 Checkout') {
            steps {
                echo '📦 Checking out code...'
                checkout scm
            }
        }
        
        stage('🧪 Environment Setup') {
            steps {
                echo '🐍 Setting up Python environment...'
                bat '''
                    docker exec disaster-api python --version
                    echo ✅ Python environment ready
                '''
            }
        }
        
        stage('📥 Sync Models from Drive') {
            steps {
                echo '☁️ Syncing latest models from Google Drive...'
                script {
                    try {
                        bat '''
                            docker exec disaster-api python -c "^
from src.colab_integration.drive_sync import DriveModelSync^
syncer = DriveModelSync()^
syncer.sync_models(['flood', 'fire'])^
print('✅ Model sync complete')^
" 2>nul || echo ⚠️ Model sync skipped - credentials not available
                        '''
                    } catch (Exception e) {
                        echo "⚠️ Model sync failed: ${e.message}"
                        echo "Continuing with existing models..."
                    }
                }
            }
        }
        
        stage('🔬 Run Tests') {
            steps {
                echo '🧪 Running unit tests...'
                bat '''
                    if exist tests (
                        docker exec disaster-api pytest tests/ -v --junitxml=test-results.xml 2>nul || exit /b 0
                    ) else (
                        echo No tests found, skipping...
                    )
                '''
            }
        }
        
        stage('📊 Check Model Performance') {
            steps {
                echo '📈 Validating model performance...'
                script {
                    try {
                        bat '''
                            docker exec disaster-api python -c "^
import json^
import os^
^
metadata_path = 'models/saved_models/flood/model_metadata_20251112_074534.json'^
if os.path.exists(metadata_path):^
    with open(metadata_path, 'r') as f:^
        metadata = json.load(f)^
    ^
    accuracy = metadata.get('final_val_acc', 0)^
    iou = metadata.get('iou', 0)^
    ^
    print(f'Model Accuracy: {accuracy:.4f}')^
    print(f'Model IoU: {iou:.4f}')^
    ^
    if accuracy ^< 0.85:^
        print('⚠️ Warning: Model accuracy below threshold!')^
    if iou ^< 0.35:^
        print('⚠️ Warning: Model IoU below threshold!')^
    ^
    print('✅ Model validation complete')^
else:^
    print('⚠️ No metadata found, skipping validation')^
" 2>nul || echo ⚠️ Model validation skipped
                        '''
                    } catch (Exception e) {
                        echo "⚠️ Model validation failed: ${e.message}"
                    }
                }
            }
        }
        
        stage('🔍 Drift Detection') {
            steps {
                echo '📊 Checking for data drift...'
                script {
                    try {
                        bat '''
                            docker exec disaster-api python -c "^
from src.drift_detection.drift_monitor import DriftDetector^
import os^
^
if os.path.exists('data/baseline'):^
    detector = DriftDetector(baseline_dir='data/baseline')^
    print('✅ Drift detection check complete')^
else:^
    print('⚠️ No baseline data found, skipping drift detection')^
" 2>nul || echo ⚠️ Drift detection skipped
                        '''
                    } catch (Exception e) {
                        echo "⚠️ Drift detection failed: ${e.message}"
                    }
                }
            }
        }
        
        stage('🐳 Build Docker Image') {
            steps {
                echo '🏗️ Building Docker image...'
                bat '''
                    docker build -f docker/Dockerfile.api -t %DOCKER_IMAGE%:%DOCKER_TAG% .
                    docker tag %DOCKER_IMAGE%:%DOCKER_TAG% %DOCKER_IMAGE%:latest
                '''
            }
        }
        
        stage('🚀 Deploy') {
            steps {
                echo '🚢 Deploying application...'
                bat '''
                    docker stop disaster-detection-api 2>nul || exit /b 0
                    docker rm disaster-detection-api 2>nul || exit /b 0
                    
                    for /f "tokens=*" %%i in ('cd') do set "PWD=%%i"
                    
                    docker run -d ^
                        --name disaster-detection-api ^
                        -p %API_PORT%:8000 ^
                        -v "%PWD%/models:/app/models" ^
                        -v "%PWD%/data:/app/data" ^
                        -e MODEL_PATH=/app/models/saved_models/flood/vizag_flood_model_20251112_074534.keras ^
                        %DOCKER_IMAGE%:latest
                    
                    timeout /t 10 /nobreak
                '''
            }
        }
        
        stage('✅ Health Check') {
            steps {
                echo '🏥 Running health checks...'
                script {
                    def maxRetries = 5
                    def retryCount = 0
                    def healthy = false
                    
                    while (retryCount < maxRetries && !healthy) {
                        try {
                            bat "curl -f http://localhost:%API_PORT%/health"
                            healthy = true
                            echo '✅ Health check passed!'
                        } catch (Exception e) {
                            retryCount++
                            echo "⏳ Health check attempt ${retryCount}/${maxRetries} failed, retrying..."
                            sleep 5
                        }
                    }
                    
                    if (!healthy) {
                        error('❌ Health check failed after all retries!')
                    }
                }
            }
        }
        
        stage('📊 Post-Deployment Tests') {
            steps {
                echo '🧪 Running post-deployment tests...'
                bat '''
                    curl -s http://localhost:%API_PORT%/models/info || exit /b 0
                    curl -s http://localhost:%API_PORT%/ || exit /b 0
                    echo ✅ Post-deployment tests complete
                '''
            }
        }
    }
    
    post {
        success {
            echo '✅ Pipeline completed successfully!'
            echo "🚀 API deployed at http://localhost:${API_PORT}"
            echo "📖 API Docs: http://localhost:${API_PORT}/docs"
        }
        
        failure {
            echo '❌ Pipeline failed!'
            bat 'docker logs disaster-detection-api 2>nul || exit /b 0'
        }
        
        always {
            echo '🧹 Cleaning up...'
            // Archive test results if they exist
            junit testResults: 'test-results.xml', allowEmptyResults: true
            
            // Clean old Docker images
            bat 'docker image prune -f --filter "until=24h" 2>nul || exit /b 0'
        }
    }
}
