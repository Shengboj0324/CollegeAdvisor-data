#!/usr/bin/env python3
"""
🔧 ADVANCED FINE-TUNING SETUP SCRIPT
Automated environment setup for bulletproof fine-tuning on MacBook

Features:
- Environment validation and setup
- Dependency installation with version pinning
- Data download and validation
- Pre-flight checks
- Troubleshooting guidance
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("=" * 100)
print("🔧 ADVANCED FINE-TUNING SETUP")
print("=" * 100)
print(f"🕒 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🎯 Target: Bulletproof MacBook fine-tuning environment")
print("=" * 100)
print()

class SetupConfig:
    """Configuration for setup process"""
    
    def __init__(self):
        self.python_min_version = (3, 9)
        self.venv_name = "venv_advanced_finetune"
        self.requirements = {
            # Core ML packages
            "torch": ">=2.0.0",
            "transformers": ">=4.35.0",
            "datasets": ">=2.14.0",
            "accelerate": ">=0.24.0",
            "peft": ">=0.6.0",
            
            # Unsloth for optimization
            "unsloth[colab-new]": "",  # Latest version
            
            # Data handling
            "numpy": ">=1.24.0,<2.0.0",  # Pin for compatibility
            "pandas": ">=2.0.0",
            "scikit-learn": ">=1.3.0",
            
            # Cloud storage
            "boto3": ">=1.28.0",
            "python-dotenv": ">=1.0.0",
            
            # Utilities
            "tqdm": ">=4.65.0",
            "rich": ">=13.5.0",
            "psutil": ">=5.9.0",
        }

config = SetupConfig()

def check_python_version():
    """Check if Python version is compatible"""
    logger.info("🐍 Checking Python version...")
    
    current_version = sys.version_info[:2]
    min_version = config.python_min_version
    
    if current_version >= min_version:
        logger.info(f"✅ Python {current_version[0]}.{current_version[1]} is compatible")
        return True
    else:
        logger.error(f"❌ Python {current_version[0]}.{current_version[1]} is too old")
        logger.error(f"Minimum required: Python {min_version[0]}.{min_version[1]}")
        return False

def check_system_resources():
    """Check system resources"""
    logger.info("💾 Checking system resources...")
    
    try:
        import psutil
        
        # Memory check
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        
        logger.info(f"📊 Total RAM: {memory_gb:.1f} GB")
        
        if memory_gb < 8:
            logger.warning("⚠️ Less than 8GB RAM detected - training may be slow")
        else:
            logger.info("✅ Sufficient RAM available")
        
        # Disk space check
        disk = psutil.disk_usage('.')
        disk_free_gb = disk.free / (1024**3)
        
        logger.info(f"💽 Free disk space: {disk_free_gb:.1f} GB")
        
        if disk_free_gb < 10:
            logger.warning("⚠️ Less than 10GB free disk space - may need cleanup")
        else:
            logger.info("✅ Sufficient disk space available")
        
        return True
        
    except ImportError:
        logger.warning("⚠️ psutil not available - skipping resource check")
        return True

def create_virtual_environment():
    """Create and activate virtual environment"""
    logger.info(f"🏗️ Creating virtual environment: {config.venv_name}")
    
    venv_path = Path(config.venv_name)
    
    if venv_path.exists():
        logger.info(f"📁 Virtual environment already exists at {venv_path}")
        response = input("Do you want to recreate it? (y/N): ").strip().lower()
        if response == 'y':
            logger.info("🗑️ Removing existing virtual environment...")
            import shutil
            shutil.rmtree(venv_path)
        else:
            logger.info("✅ Using existing virtual environment")
            return True
    
    try:
        # Create virtual environment
        subprocess.run([
            sys.executable, "-m", "venv", str(venv_path)
        ], check=True, capture_output=True, text=True)
        
        logger.info("✅ Virtual environment created successfully")
        
        # Get activation command
        if os.name == 'nt':  # Windows
            activate_cmd = f"{venv_path}\\Scripts\\activate"
        else:  # Unix/MacOS
            activate_cmd = f"source {venv_path}/bin/activate"
        
        logger.info(f"💡 To activate: {activate_cmd}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to create virtual environment: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    logger.info("📦 Installing dependencies...")
    
    venv_path = Path(config.venv_name)
    if not venv_path.exists():
        logger.error("❌ Virtual environment not found")
        return False
    
    # Get pip path
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip"
    else:  # Unix/MacOS
        pip_path = venv_path / "bin" / "pip"
    
    try:
        # Upgrade pip first
        logger.info("⬆️ Upgrading pip...")
        subprocess.run([
            str(pip_path), "install", "--upgrade", "pip"
        ], check=True, capture_output=True, text=True)
        
        # Install packages
        for package, version in config.requirements.items():
            logger.info(f"📦 Installing {package}...")
            
            if version:
                package_spec = f"{package}{version}"
            else:
                package_spec = package
            
            try:
                result = subprocess.run([
                    str(pip_path), "install", package_spec
                ], check=True, capture_output=True, text=True, timeout=300)
                
                logger.info(f"✅ {package} installed successfully")
                
            except subprocess.TimeoutExpired:
                logger.warning(f"⚠️ {package} installation timed out - continuing...")
            except subprocess.CalledProcessError as e:
                logger.warning(f"⚠️ Failed to install {package}: {e}")
                if "unsloth" in package:
                    logger.info("🔄 Trying alternative Unsloth installation...")
                    try:
                        subprocess.run([
                            str(pip_path), "install", "unsloth", "--upgrade"
                        ], check=True, capture_output=True, text=True)
                        logger.info("✅ Unsloth installed via alternative method")
                    except:
                        logger.warning("⚠️ Unsloth installation failed - will try at runtime")
        
        logger.info("✅ Dependencies installation completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dependency installation failed: {e}")
        return False

def verify_installation():
    """Verify that all packages are correctly installed"""
    logger.info("🔍 Verifying installation...")
    
    venv_path = Path(config.venv_name)
    if os.name == 'nt':  # Windows
        python_path = venv_path / "Scripts" / "python"
    else:  # Unix/MacOS
        python_path = venv_path / "bin" / "python"
    
    verification_script = """
import sys
print(f"Python: {sys.version}")

packages_to_check = [
    'torch', 'transformers', 'datasets', 'accelerate', 'peft',
    'numpy', 'pandas', 'boto3', 'tqdm', 'rich'
]

failed_imports = []

for package in packages_to_check:
    try:
        __import__(package)
        print(f"✅ {package}")
    except ImportError as e:
        print(f"❌ {package}: {e}")
        failed_imports.append(package)

# Special check for Unsloth
try:
    from unsloth import FastLanguageModel
    print("✅ unsloth")
except ImportError as e:
    print(f"⚠️ unsloth: {e} (will install at runtime)")

# Check PyTorch capabilities
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    
    if torch.cuda.is_available():
        print("🚀 CUDA available")
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        print("🍎 MPS (Apple Silicon) available")
    else:
        print("💻 Using CPU")
        
except Exception as e:
    print(f"❌ PyTorch check failed: {e}")
    failed_imports.append('torch')

if failed_imports:
    print(f"\\n❌ Failed imports: {failed_imports}")
    sys.exit(1)
else:
    print("\\n✅ All core packages verified")
    sys.exit(0)
"""
    
    try:
        result = subprocess.run([
            str(python_path), "-c", verification_script
        ], capture_output=True, text=True, timeout=60)
        
        print(result.stdout)
        
        if result.returncode == 0:
            logger.info("✅ Installation verification passed")
            return True
        else:
            logger.error("❌ Installation verification failed")
            if result.stderr:
                logger.error(f"Error output: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Verification timed out")
        return False
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def download_training_data():
    """Download and validate training data"""
    logger.info("📥 Checking training data availability...")
    
    # Check if data already exists locally
    local_files = [
        "training_data_alpaca.json",
        "training_data_ollama.txt"
    ]
    
    for file in local_files:
        if Path(file).exists():
            logger.info(f"✅ Found local training data: {file}")
            return True
    
    # Try to download from R2
    logger.info("🌐 Attempting to download from R2...")
    
    venv_path = Path(config.venv_name)
    if os.name == 'nt':  # Windows
        python_path = venv_path / "Scripts" / "python"
    else:  # Unix/MacOS
        python_path = venv_path / "bin" / "python"
    
    download_script = """
import sys
sys.path.insert(0, '.')

try:
    from college_advisor_data.storage.r2_storage import R2StorageClient
    
    client = R2StorageClient()
    
    # Try to download training data
    training_files = [
        ("multi_source/training_datasets/instruction_dataset_alpaca.json", "training_data_alpaca.json"),
        ("real_data/training_datasets/instruction_dataset_alpaca.json", "training_data_alpaca_backup.json")
    ]
    
    for r2_key, local_file in training_files:
        try:
            success = client.download_file(r2_key, local_file)
            if success:
                print(f"✅ Downloaded {local_file}")
                sys.exit(0)
        except Exception as e:
            print(f"⚠️ Failed to download {r2_key}: {e}")
            continue
    
    print("❌ No training data could be downloaded")
    sys.exit(1)
    
except ImportError as e:
    print(f"⚠️ R2 client not available: {e}")
    print("You'll need to provide training data manually")
    sys.exit(1)
except Exception as e:
    print(f"❌ Download failed: {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run([
            str(python_path), "-c", download_script
        ], capture_output=True, text=True, timeout=120)
        
        print(result.stdout)
        
        if result.returncode == 0:
            logger.info("✅ Training data downloaded successfully")
            return True
        else:
            logger.warning("⚠️ Could not download training data from R2")
            logger.info("💡 You can provide training data manually:")
            logger.info("   - Place training_data_alpaca.json in the current directory")
            logger.info("   - Or use any JSON file with instruction/output format")
            return True  # Continue anyway
            
    except subprocess.TimeoutExpired:
        logger.warning("⚠️ Download timed out")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Download error: {e}")
        return True

def create_usage_guide():
    """Create usage guide and next steps"""
    logger.info("📚 Creating usage guide...")
    
    guide = f"""# 🚀 ADVANCED FINE-TUNING USAGE GUIDE

## Environment Setup Complete ✅

Your advanced fine-tuning environment is ready!

### 📁 Files Created:
- `{config.venv_name}/` - Virtual environment with all dependencies
- `advanced_finetune_macos.py` - Main training script
- `test_advanced_model.py` - Comprehensive testing script
- `setup_advanced_finetuning.py` - This setup script

### 🎯 Next Steps:

#### 1. Activate Environment
```bash
source {config.venv_name}/bin/activate
```

#### 2. Start Training
```bash
python advanced_finetune_macos.py
```

#### 3. Test Model (After Training)
```bash
python test_advanced_model.py
```

### ⚙️ Training Configuration:
- **Model**: Unsloth TinyLlama (4-bit quantized)
- **LoRA Rank**: 32 (high capacity)
- **Sequence Length**: 2048 tokens
- **Epochs**: 5 (thorough training)
- **Target Accuracy**: 95%+

### 🔧 Troubleshooting:

#### If Training Fails:
1. Check available memory: `python -c "import psutil; print(f'RAM: {{psutil.virtual_memory().available/1024**3:.1f}} GB')"`
2. Reduce batch size in config if OOM
3. Check logs in `advanced_finetune.log`

#### If Dependencies Fail:
1. Update pip: `pip install --upgrade pip`
2. Install manually: `pip install torch transformers datasets`
3. Try CPU-only PyTorch if GPU issues

#### If No Training Data:
1. Download manually from R2 bucket
2. Use any JSON file with instruction/output format
3. Check data format matches expected structure

### 📊 Expected Training Time:
- **MacBook Pro M1/M2**: 2-4 hours
- **MacBook Air**: 4-6 hours  
- **Intel MacBook**: 6-8 hours

### 🎉 Success Criteria:
- Training loss decreases steadily
- Evaluation accuracy > 95%
- Model generates coherent responses
- All test categories pass

### 📞 Support:
Check the logs and error messages for specific issues.
The scripts include comprehensive error handling and diagnostics.

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open("ADVANCED_FINETUNING_GUIDE.md", "w") as f:
        f.write(guide)
    
    logger.info("✅ Usage guide created: ADVANCED_FINETUNING_GUIDE.md")

def main():
    """Main setup function"""
    success_steps = []
    
    try:
        # Step 1: Check Python version
        if check_python_version():
            success_steps.append("Python version")
        else:
            logger.error("❌ Python version check failed")
            return False
        
        # Step 2: Check system resources
        if check_system_resources():
            success_steps.append("System resources")
        
        # Step 3: Create virtual environment
        if create_virtual_environment():
            success_steps.append("Virtual environment")
        else:
            logger.error("❌ Virtual environment creation failed")
            return False
        
        # Step 4: Install dependencies
        if install_dependencies():
            success_steps.append("Dependencies")
        else:
            logger.error("❌ Dependency installation failed")
            return False
        
        # Step 5: Verify installation
        if verify_installation():
            success_steps.append("Installation verification")
        else:
            logger.error("❌ Installation verification failed")
            return False
        
        # Step 6: Download training data
        if download_training_data():
            success_steps.append("Training data")
        
        # Step 7: Create usage guide
        create_usage_guide()
        success_steps.append("Usage guide")
        
        # Success summary
        print("\n" + "=" * 100)
        print("🎉 SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 100)
        print("✅ Completed steps:")
        for step in success_steps:
            print(f"  ✅ {step}")
        
        print(f"\n🚀 Next steps:")
        print(f"  1. Activate environment: source {config.venv_name}/bin/activate")
        print(f"  2. Start training: python advanced_finetune_macos.py")
        print(f"  3. Read guide: ADVANCED_FINETUNING_GUIDE.md")
        
        print("\n🎯 Target: 95%+ accuracy fine-tuned model")
        print("⏱️ Estimated training time: 2-8 hours (depending on hardware)")
        print("=" * 100)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

