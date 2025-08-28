"""
Configurations for the overall project
"""

import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ModelConfig:
    """Configuration for the AI model."""
    path: str = r"C:\Stable Diffusion\stable-diffusion-webui\models\Stable-diffusion\anythingV5_fp16.safetensors"
    device: str = "auto" # auto, cuda, cpu
    dtype: str = "float16" # Model loads with less precision but memory friendly
    enable_attention_slicing: bool = True  # Divide and conquer, reduce peak memory usage
    enable_memory_efficient_attention: bool = True  # 
    use_safetensors: bool = True
    load_safety_checker: bool = False  # Model may falsely flag, thus we'll manage in the neg prompts

@dataclass
class QueueConfig:
    """Configuration for the request queue system"""
    max_size: int = 50
    max_workers: int = 1  # Number of concurrent image generations; 1 due to system limitation
    # timeout_seconds: int = 300  # 5 minutes
    estimated_time_per_request: int = 10  # Seconds for wait time estimation

@dataclass
class BotConfig:
    """Configuration for the Discord bot."""
    token: str = ""
    command_prefix: str = "!"
    max_prompt_length: int = 400
    max_negative_length: int = 300
    max_steps: int = 50
    min_steps: int = 10
    max_cfg_scale: float = 20.0
    min_cfg_scale: float = 1.0
    max_resolution: int = 1024
    min_resolution: int = 256

@dataclass
class BotConfig:
    """Configuration for the Discord bot."""
    token: str = ""
    command_prefix: str = "!"
    max_prompt_length: int = 400
    max_negative_length: int = 300
    max_steps: int = 50
    min_steps: int = 10
    max_cfg_scale: float = 20.0
    min_cfg_scale: float = 1.0
    max_resolution: int = 1024
    min_resolution: int = 256

@dataclass
class GenerationDefaults:
    """Default values for image generation parameters."""
    steps: int = 25
    cfg_scale: float = 7.0
    width: int = 512
    height: int = 512
    negative_prompt: str = "nsfw, nude, inappropriate, gore, bad anatomy, bad hands, blurry, low quality, text, watermark, missing fingers"
    quality_tags: str = "masterpiece, best quality, "

@dataclass
class LoggingConfig:
    """Configuration for logging."""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_file_logging: bool = True
    log_file: str = "bot.log"
    max_log_size_mb: int = 10
    backup_count: int = 5