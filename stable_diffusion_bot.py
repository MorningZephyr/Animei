import torch
from diffusers import StableDiffusionPipeline, EulerAncestralDiscreteScheduler
import os


class StableDiffusionBot:
    def __init__(self, model_path: str = r"C:\Stable Diffusion\stable-diffusion-webui\models\Stable-diffusion\anythingV5_fp16.safetensors"):
        self.model_path = model_path
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None

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
                # xformer got compatibility issues so might not work
                try:
                    self.pipe.enable_memory_efficient_attention()
                    print("✅ Memory efficient attention enabled")
                except:
                    print("⚠️  Memory efficient attention not available")
            
            print("✅ Anything V5 model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            raise

    async def generate_image(self, prompt: str, negative_prompt: str = "", num_inference_steps: int = 28, cfg_scale: float = 7.0, width: int = 512, height: int = 512):
        if self.pipe is None:
            await self.load_model()

        # Prevent NFSW images
        safety_filters = "nsfw, nude, inappropriate, gore"
        negative_prompt = safety_filters if not negative_prompt else f"{negative_prompt}, {safety_filters}"

        # Use recommended settings for Anything V5
        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=cfg_scale,
            width=width,
            height=height,
        )
        return result.images[0]