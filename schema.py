"""
Data models for the AniMei Discord bot.
"""

from dataclasses import dataclass
from typing import Optional, Callable, Dict, Any
import uuid


@dataclass
class GenerationRequest:
    """Represents a single image generation request"""
    request_id: str
    prompt: str
    negative_prompt: str = ""
    num_inference_steps: int = None
    cfg_scale: float = None
    width: int = 512
    height: int = 512
    user_id: Optional[str] = None
    channel_id: Optional[str] = None
    callback: Optional[Callable] = None  # Function to call when image is ready
    callback_data: Optional[Dict[str, Any]] = None  # Extra data for callback
    
    def __post_init__(self):
        if not self.request_id:
            self.request_id = str(uuid.uuid4())
        
        # Use config defaults if not specified
        from config import config
        if self.num_inference_steps is None:
            self.num_inference_steps = config.default_steps
        if self.cfg_scale is None:
            self.cfg_scale = config.default_cfg_scale
