import discord
from discord.ext import commands
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image
import io
import os
import time
import asyncio
from dotenv import load_dotenv

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

load_dotenv()

# --- Loading the Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

sd_bot = StableDiffusionBot()

# --- Setting the event listener ---
@bot.event
async def on_ready():
    asyncio.create_task(sd_bot.load_model())
    print(f"✅ {bot.user} is online! Loading model in background...")

@bot.event
async def setup_hook():
    await bot.tree.sync()  # Sync slash commands with Discord
    print("Slash commands synced!")

@bot.tree.command(name="generate", description="Generate an AI image from text")
async def generate_image_command(
    interaction: discord.Interaction,
    prompt: str,
    negative_prompt: str = "",
    steps: int = 20,
    cfg_scale: float = 7.5,
    width: int = 512,
    height: int = 512
):
    # Check if model is still loading
    if sd_bot.pipe is None:
        await interaction.response.send_message("⏳ Model is still loading, please wait a moment and try again!")
        return
    
    # Defer the response since image generation takes time
    await interaction.response.defer()
    
    # Generate image with all the parameters
    image = await sd_bot.generate_image(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=steps,
        cfg_scale=cfg_scale,
        width=width,
        height=height
    )
    
    # Convert to Discord file
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    buffer.seek(0)
    
    file = discord.File(buffer, filename="generated_image.png")
    await interaction.followup.send(f"✨ Here's your image for: `{prompt}`", file=file)

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))
