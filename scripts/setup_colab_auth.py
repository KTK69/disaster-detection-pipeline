"""
Setup script to authenticate Google services
Run this once to generate auth tokens for Drive and Earth Engine
"""
import os
import sys
from pathlib import Path
import pickle

def setup_drive_auth():
    """Authenticate and save credentials for Google Drive access"""
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
    except ImportError:
        print("❌ Missing dependencies. Install with:")
        print("   pip install google-auth-oauthlib google-api-python-client")
        sys.exit(1)
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.metadata.readonly'
    ]
    
    creds = None
    token_path = Path('token.pickle')
    credentials_path = Path('google-drive-credentials.json')
    
    # Check if credentials file exists
    if not credentials_path.exists():
        print("❌ google-drive-credentials.json not found!")
        print("\n📋 Steps to create credentials:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Enable Google Drive API")
        print("3. Create OAuth 2.0 Client ID (Desktop App)")
        print("4. Download credentials JSON")
        print("5. Save as 'google-drive-credentials.json' in this directory")
        sys.exit(1)
    
    # Check if token already exists
    if token_path.exists():
        print("🔍 Found existing token.pickle")
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, let user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("🌐 Opening browser for authentication...")
            print("   Please sign in with your Google account")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
        print("💾 Credentials saved to token.pickle")
    else:
        print("✅ Existing credentials are valid")
    
    print("\n✅ Google Drive authentication successful!")
    print(f"   Token saved to: {token_path.absolute()}")
    return creds


def verify_earth_engine_credentials():
    """Verify Earth Engine service account credentials"""
    service_account_path = Path('service-account-key.json')
    
    if not service_account_path.exists():
        print("\n⚠️  Earth Engine credentials not found!")
        print("\n📋 Steps to create Earth Engine credentials:")
        print("1. Go to https://earthengine.google.com/")
        print("2. Register and create a GCP project")
        print("3. Enable Earth Engine API")
        print("4. Create Service Account")
        print("5. Download JSON key")
        print("6. Save as 'service-account-key.json' in this directory")
        return False
    
    print("\n✅ Earth Engine credentials found!")
    print(f"   Located at: {service_account_path.absolute()}")
    
    # Try to initialize Earth Engine
    try:
        import ee
        from dotenv import load_dotenv
        load_dotenv()
        
        service_account = os.getenv('GEE_SERVICE_ACCOUNT')
        if service_account:
            credentials = ee.ServiceAccountCredentials(
                service_account, 
                str(service_account_path)
            )
            ee.Initialize(credentials)
            print("✅ Earth Engine initialized successfully!")
            return True
        else:
            print("⚠️  GEE_SERVICE_ACCOUNT not set in .env")
            return False
            
    except ImportError:
        print("⚠️  earthengine-api not installed. Install with:")
        print("   pip install earthengine-api")
        return False
    except Exception as e:
        print(f"⚠️  Could not initialize Earth Engine: {e}")
        return False


def create_directory_structure():
    """Create necessary project directories"""
    directories = [
        'data/raw',
        'data/processed',
        'data/baseline',
        'data/baseline_archive',
        'data/retraining',
        'models/saved_models/flood',
        'models/saved_models/fire',
        'models/architectures',
        'models/configs',
        'logs',
        'colab_notebooks/utils',
        'tests'
    ]
    
    print("\n📁 Creating project directories...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep files to preserve empty directories
    for directory in ['data/baseline', 'data/baseline_archive', 'logs']:
        gitkeep = Path(directory) / '.gitkeep'
        gitkeep.touch()
    
    print("✅ Directory structure created!")


def check_env_file():
    """Check if .env file exists"""
    env_path = Path('.env')
    env_example_path = Path('.env.example')
    
    if not env_path.exists():
        if env_example_path.exists():
            print("\n⚠️  .env file not found!")
            print("   Creating from .env.example...")
            env_path.write_text(env_example_path.read_text())
            print("✅ Created .env file")
            print("   ⚠️  Please edit .env with your actual credentials")
        else:
            print("\n❌ .env.example not found!")
            return False
    else:
        print("\n✅ .env file found")
    
    return True


def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 Disaster Detection System - Setup Script")
    print("=" * 60)
    
    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required!")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Create directories
    create_directory_structure()
    
    # Check .env file
    check_env_file()
    
    # Setup Drive authentication
    print("\n" + "=" * 60)
    print("📥 Setting up Google Drive Authentication")
    print("=" * 60)
    setup_drive_auth()
    
    # Verify Earth Engine credentials
    print("\n" + "=" * 60)
    print("🌍 Verifying Earth Engine Credentials")
    print("=" * 60)
    verify_earth_engine_credentials()
    
    # Final instructions
    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Edit .env with your actual credentials")
    print("2. Upload Colab notebooks to Google Drive")
    print("3. Update COLAB_NOTEBOOK_* IDs in .env")
    print("4. Run: docker-compose up -d")
    print("5. Access API at: http://localhost:8000")
    print("\n💡 Run this script again if you need to re-authenticate")


if __name__ == '__main__':
    main()
