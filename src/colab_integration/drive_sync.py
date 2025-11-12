"""
Synchronize models between Google Drive and local API server
Downloads trained models from Google Drive to local storage
"""
import os
import io
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import pickle

logger = logging.getLogger(__name__)


class DriveModelSync:
    """
    Sync trained models from Google Drive to local server
    """
    
    def __init__(self):
        self.local_model_dir = Path('./models/saved_models')
        self.local_model_dir.mkdir(parents=True, exist_ok=True)
        
        self.service = None
        self.setup_drive_service()
    
    def setup_drive_service(self):
        """Initialize Google Drive API client"""
        try:
            from googleapiclient.discovery import build
            
            token_path = Path('token.pickle')
            
            if not token_path.exists():
                logger.warning("⚠️  token.pickle not found. Run setup_colab_auth.py first")
                return
            
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
            
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("✅ Drive service initialized")
            
        except ImportError:
            logger.error("❌ google-api-python-client not installed")
            logger.info("   Install with: pip install google-api-python-client")
        except Exception as e:
            logger.error(f"❌ Could not initialize Drive service: {e}")
    
    def list_models(self, model_type: str = 'flood') -> List[dict]:
        """
        List all models of a specific type in Drive
        
        Args:
            model_type: 'flood' or 'fire'
        
        Returns:
            List of model file metadata
        """
        if not self.service:
            logger.warning("Drive service not initialized")
            return []
        
        try:
            folder_name = f"{os.getenv('DRIVE_MODEL_FOLDER', 'disaster_detection/models')}/{model_type}"
            
            # Search for folder first
            query = f"name='{model_type}' and mimeType='application/vnd.google-apps.folder'"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            if not folders:
                logger.warning(f"No folder found for {model_type} in Drive")
                return []
            
            folder_id = folders[0]['id']
            
            # List model files in folder
            query = f"'{folder_id}' in parents and (name contains '.h5' or name contains '.pt')"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, modifiedTime, size)',
                orderBy='modifiedTime desc'
            ).execute()
            
            models = results.get('files', [])
            logger.info(f"Found {len(models)} {model_type} models in Drive")
            
            return models
            
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    def download_latest_model(self, model_type: str = 'flood') -> Optional[Path]:
        """
        Download the latest trained model from Drive
        
        Args:
            model_type: 'flood' or 'fire'
        
        Returns:
            Local path to downloaded model
        """
        if not self.service:
            logger.warning("Drive service not initialized - skipping download")
            return None
        
        try:
            models = self.list_models(model_type)
            
            if not models:
                logger.warning(f"No models found for {model_type}")
                return None
            
            latest_model = models[0]  # Already sorted by modifiedTime desc
            file_id = latest_model['id']
            file_name = latest_model['name']
            
            logger.info(f"Downloading: {file_name}")
            logger.info(f"  Modified: {latest_model['modifiedTime']}")
            logger.info(f"  Size: {int(latest_model['size']) / (1024*1024):.2f} MB")
            
            # Download file
            from googleapiclient.http import MediaIoBaseDownload
            
            request = self.service.files().get_media(fileId=file_id)
            
            local_path = self.local_model_dir / model_type / file_name
            local_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(local_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        logger.info(f"  Download progress: {progress}%")
            
            logger.info(f"✅ Model downloaded to: {local_path}")
            
            # Also download metrics file
            self._download_metrics(file_name, model_type)
            
            return local_path
            
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
            return None
    
    def _download_metrics(self, model_filename: str, model_type: str):
        """Download associated metrics file"""
        if not self.service:
            return
        
        try:
            metrics_name = model_filename.replace('.h5', '_metrics.json').replace('.pt', '_metrics.json')
            
            # Search for metrics file
            query = f"name='{metrics_name}'"
            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            if not files:
                logger.warning(f"No metrics file found: {metrics_name}")
                return
            
            file_id = files[0]['id']
            
            from googleapiclient.http import MediaIoBaseDownload
            
            request = self.service.files().get_media(fileId=file_id)
            
            local_path = self.local_model_dir / model_type / metrics_name
            
            with open(local_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
            
            logger.info(f"✅ Metrics downloaded: {metrics_name}")
            
        except Exception as e:
            logger.warning(f"Could not download metrics: {e}")
    
    def check_for_updates(self, model_type: str = 'flood') -> bool:
        """
        Check if there's a newer model in Drive than what's local
        
        Returns:
            True if update available
        """
        if not self.service:
            logger.warning("Drive service not initialized")
            return False
        
        try:
            drive_models = self.list_models(model_type)
            if not drive_models:
                return False
            
            latest_drive_model = drive_models[0]
            drive_modified = datetime.fromisoformat(
                latest_drive_model['modifiedTime'].replace('Z', '+00:00')
            )
            
            # Check local model
            local_models_dir = self.local_model_dir / model_type
            if not local_models_dir.exists():
                logger.info(f"No local models for {model_type} - update needed")
                return True
            
            local_models = list(local_models_dir.glob("*.h5")) + list(local_models_dir.glob("*.pt"))
            if not local_models:
                logger.info(f"No local model files for {model_type} - update needed")
                return True
            
            # Get latest local model modification time
            local_models.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_local = local_models[0]
            local_modified = datetime.fromtimestamp(latest_local.stat().st_mtime)
            
            if drive_modified > local_modified:
                logger.info(f"Update available for {model_type}!")
                logger.info(f"  Drive: {latest_drive_model['name']} ({drive_modified})")
                logger.info(f"  Local: {latest_local.name} ({local_modified})")
                return True
            
            logger.info(f"✅ Local {model_type} model is up to date")
            return False
            
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False
    
    def sync_models(self, model_types: List[str] = ['flood', 'fire']):
        """
        Sync all model types from Drive to local
        
        Args:
            model_types: List of model types to sync
        """
        logger.info("=" * 60)
        logger.info("📥 Syncing models from Google Drive")
        logger.info("=" * 60)
        
        for model_type in model_types:
            logger.info(f"\nChecking {model_type} models...")
            
            try:
                if self.check_for_updates(model_type):
                    self.download_latest_model(model_type)
                else:
                    logger.info(f"✅ {model_type} models up to date")
            except Exception as e:
                logger.error(f"❌ Error syncing {model_type}: {e}")
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Model sync complete")
        logger.info("=" * 60)


if __name__ == '__main__':
    # Test the sync
    logging.basicConfig(level=logging.INFO)
    syncer = DriveModelSync()
    syncer.sync_models()
