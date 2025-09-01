import os
import torch
from dotenv import load_dotenv

# Load environment variables first, before any config access
load_dotenv()

class Config:
    """Simple configuration management for AniMei Discord Bot"""
    
    def __init__(self):
        # ========================================
        # 🔑 ESSENTIAL SETTINGS
        # ========================================
        self.discord_token = self._get_required_env('DISCORD_BOT_TOKEN')
        self.model_path = os.getenv('MODEL_PATH', r'C:\Stable Diffusion\stable-diffusion-webui\models\Stable-diffusion\anythingV5_fp16.safetensors')
        self.model_device = os.getenv('MODEL_DEVICE', 'cuda' if torch.cuda.is_available() else 'cpu')
        
        # Validate configuration
        self._validate_config()
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set!")
        return value
    
    def _validate_config(self):
        """Validate configuration values"""
        if not os.path.exists(self.model_path):
            print(f"⚠️  Warning: Model path does not exist: {self.model_path}")
            print("   Please check your MODEL_PATH in .env file")
        
        if self.model_device not in ['cuda', 'cpu']:
            raise ValueError("MODEL_DEVICE must be either 'cuda' or 'cpu'")
        
        if self.model_device == 'cuda' and not torch.cuda.is_available():
            print("⚠️  Warning: CUDA requested but not available, falling back to CPU")
            self.model_device = 'cpu'

# Global configuration instance
config = Config()
