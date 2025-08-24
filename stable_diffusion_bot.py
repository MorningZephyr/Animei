import torch
from diffusers import StableDiffusionPipeline


class StableDiffusionBot:
    def __init__(self, model_id: str = "stablediffusionapi/anything-v5"):
        self.model_id = model_id
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipe = None

        # Device info
        if self.device == "cuda":
            print(f"🚀 GPU detected: {torch.cuda.get_device_name(0)}")
            print(f"   VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
        else:
            print("🐌 Using CPU (will be slower)")
        
    async def load_model(self):
        """Loads the given model into memory and establish the pipeline"""
        if self.pipe is not None:
            return
        
        print(f"📥 Model being loaded: {self.model_id}")

        self.pipe = StableDiffusionPipeline.from_pretrained(
            self.model_id,
            torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
        )
        self.pipe = self.pipe.to(self.device)
        self.pipe.safety_checker = None

        print("✅ Model loaded!")

    async def generate_image(self, prompt: str, negative_prompt: str = "", num_inference_steps: int = 20, cfg_scale: float = 7.5, width: int = 512, height: int = 512):
        if self.pipe is None:
            await self.load_model()

        # Prevent NFSW images
        safety_filters = "nsfw, nude, inappropriate, gore"
        negative_prompt = safety_filters if not negative_prompt else f"{negative_prompt}, {safety_filters}"

        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_inference_steps=num_inference_steps,
            guidance_scale=cfg_scale,
            width=width,
            height=height,
        )
        return result.images[0]