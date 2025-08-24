import discord
from discord.ext import commands
import torch
import io
import os
import asyncio
from stable_diffusion_bot import StableDiffusionBot
from dotenv import load_dotenv

load_dotenv()

# --- Modal Class for Advanced Generation ---
class UIModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="🎨 AniMei: Image Generator")
        
        # Large text area for main prompt
        self.prompt = discord.ui.TextInput(
            label="Describe your image",
            style=discord.TextStyle.paragraph,  # Multi-line text box
            placeholder="A mochi girl wearing a pajamas...",
            max_length=1000,
            required=True
        )
        
        # Negative prompt
        self.negative = discord.ui.TextInput(
            label="What to avoid (optional)",
            style=discord.TextStyle.paragraph,
            placeholder="blurry, low quality, distorted, bad anatomy...",
            max_length=1000,
            required=False
        )
        
        # Steps
        self.steps = discord.ui.TextInput(
            label="Steps (10-50)",
            style=discord.TextStyle.short,
            placeholder="20",
            default="20",
            required=False
        )
        
        # CFG Scale
        self.cfg_scale = discord.ui.TextInput(
            label="CFG Scale (1.0-20.0)",
            style=discord.TextStyle.short,
            placeholder="7.5",
            default="7.5",
            required=False
        )
        
        # Image dimensions
        self.dimensions = discord.ui.TextInput(
            label="Size (width x height)",
            style=discord.TextStyle.short,
            placeholder="512x512",
            default="512x512",
            required=False
        )
        
        # Add all inputs to the modal
        self.add_item(self.prompt)
        self.add_item(self.negative)
        self.add_item(self.steps)
        self.add_item(self.cfg_scale)
        self.add_item(self.dimensions)
    
    async def on_submit(self, interaction: discord.Interaction):
        # Check if model is still loading
        if sd_bot.pipe is None:
            await interaction.response.send_message("⏳ Model is still loading, please wait a moment and try again!")
            return
        
        # Defer the response since image generation takes time
        await interaction.response.defer()
        
        # Parse user inputs with validation
        try:
            steps = int(self.steps.value) if self.steps.value.isdigit() else 20
            steps = max(10, min(50, steps))  # Clamp between 10-50
            
            cfg_scale = float(self.cfg_scale.value) if self.cfg_scale.value.replace('.', '').isdigit() else 7.5
            cfg_scale = max(1.0, min(20.0, cfg_scale))  # Clamp between 1-20
            
            # Parse dimensions
            if 'x' in self.dimensions.value.lower():
                width, height = self.dimensions.value.lower().split('x')
                width = int(width.strip()) if width.strip().isdigit() else 512
                height = int(height.strip()) if height.strip().isdigit() else 512
            else:
                width = height = 512
            
            # Clamp dimensions to reasonable values
            width = max(256, min(1024, width))
            height = max(256, min(1024, height))
            
        except:
            # If parsing fails, use defaults
            steps = 20
            cfg_scale = 7.5
            width = height = 512
        
        # Generate image with all the parameters
        try:
            image = await sd_bot.generate_image(
                prompt=self.prompt.value,
                negative_prompt=self.negative.value,
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
            
            # Create info embed
            embed = discord.Embed(title="✨ Generated Image", color=0x00ff00)
            embed.add_field(name="Prompt", value=self.prompt.value[:100] + "..." if len(self.prompt.value) > 100 else self.prompt.value, inline=False)
            embed.add_field(name="Steps", value=str(steps), inline=True)
            embed.add_field(name="CFG Scale", value=str(cfg_scale), inline=True)
            embed.add_field(name="Size", value=f"{width}x{height}", inline=True)
            
            await interaction.followup.send(embed=embed, file=file)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error generating image: {str(e)}")

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

# --- NEW: Modal-based Generate Command ---
@bot.tree.command(name="generate", description="Generate an AI image using advanced modal interface")
async def generate_modal_command(interaction: discord.Interaction):
    """Opens a modal form for advanced image generation"""
    modal = UIModal()
    await interaction.response.send_modal(modal)

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))