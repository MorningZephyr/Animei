import torch
from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler
import os
import concurrent.futures
import functools


class StableDiffusionGenerator:
    """Handles Stable Diffusion model loading and image generation."""
    
    def __init__(self, model_path: str = None):
        from config import config
        self.model_path = model_path or config.model_path
        self.device = config.model_device
        self.pipe = None
        
        # Thread pool for CPU/GPU intensive tasks (prevents blocking event loop)
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

        # Device info
        if self.device == "cuda":
            print(f"🚀 GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
        else:
            print("🐌 Using CPU (will be slower)")
        
    async def load_model(self):
        """Loads the local Anything V5 model into memory"""
        if self.pipe is not None:
            return
        
        # Check if model file exists
        if not os.path.exists(self.model_path):
            print(f"❌ Model file not found: {self.model_path}")
            print("Please download the Anything V5 model and place it in the models/Stable-diffusion/ folder")
            return
        
        print(f"📥 Loading local model: {self.model_path}")

        try:
            # Load the local model
            self.pipe = StableDiffusionPipeline.from_single_file(
                self.model_path,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                use_safetensors=True,
                load_safety_checker=False
            )
            
            # Use Euler A scheduler (great for anime models)
            self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(
                self.pipe.scheduler.config
            )
            
            self.pipe = self.pipe.to(self.device)
            
            # Memory optimizations for SD 1.5
            if self.device == "cuda":
                self.pipe.enable_attention_slicing()
                # Optional: enable memory efficient attention if available
                # Since xformers isn't installed, this should be removed
                try:
                    self.pipe.enable_memory_efficient_attention()
                    print("✅ Memory efficient attention enabled")
                except:
                    print("⚠️  Memory efficient attention not available")
            
            print("✅ Anything V5 model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise

    def _generate_image_sync(self, prompt: str, negative_prompt: str = "", num_inference_steps: int = None, cfg_scale: float = None, width: int = 512, height: int = 512):
        # Use config defaults if not specified
        from config import config
        if num_inference_steps is None:
            num_inference_steps = config.default_steps
        if cfg_scale is None:
            cfg_scale = config.default_cfg_scale
        """Synchronous image generation - runs in thread pool to avoid blocking event loop"""
        # Prevent NFSW images
        safety_filters = "nsfw, nude, inappropriate, gore"
        negative_prompt = safety_filters if not negative_prompt else f"{negative_prompt}, {safety_filters}"

        # Add quality tags that WebUI uses
        quality_tags = "masterpiece, best quality, "
        prompt = quality_tags + prompt if not prompt.startswith(quality_tags) else prompt

        # Use recommended settings for Anything V5
        print(f"🎨 Generating with prompt: {prompt[:50]}...")
        print(f"   Steps: {num_inference_steps}, CFG: {cfg_scale}, Size: {width}x{height}")
        
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=cfg_scale,
            width=width,
            height=height,
        )
        
        print("✅ Image generation completed")
        return result.images[0]

    async def generate_image(self, prompt: str, negative_prompt: str = "", num_inference_steps: int = None, cfg_scale: float = None, width: int = 512, height: int = 512):
        """Async wrapper that runs image generation in thread pool to prevent blocking"""
        if self.pipe is None:
            await self.load_model()

        # Run the sync generation in thread pool to avoid blocking the event loop
        import asyncio
        loop = asyncio.get_event_loop()
        image = await loop.run_in_executor(
            self.executor,
            functools.partial(
                self._generate_image_sync,
                prompt=prompt,
                negative_prompt=negative_prompt,
                num_inference_steps=num_inference_steps,
                cfg_scale=cfg_scale,
                width=width,
                height=height
            )
        )
        
        return image
    
    def cleanup(self):
        """Clean up resources"""
        if self.executor:
            self.executor.shutdown(wait=True)
            print("🧹 Thread pool executor shut down")
