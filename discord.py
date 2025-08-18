import discord
from discord.ext import commands
import requests
import base64
from PIL import Image
from io import BytesIO
import os
import asyncio

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration
WEBUI_URL = "http://127.0.0.1:7860"
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual token

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    
    # Test if Stable Diffusion API is accessible
    try:
        response = requests.get(f"{WEBUI_URL}/sdapi/v1/samplers", timeout=5)
        if response.status_code == 200:
            print("✅ Stable Diffusion API is accessible!")
        else:
            print("❌ Stable Diffusion API returned error:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("❌ Cannot connect to Stable Diffusion API:", str(e))
        print("Make sure WebUI is running with --api flag")

@bot.command(name='generate', aliases=['gen', 'img'])
async def generate_image(ctx, *, prompt):
    """Generate an image from a text prompt
    Usage: !generate a beautiful sunset over mountains
    """
    
    if len(prompt.strip()) == 0:
        await ctx.send("❌ Please provide a prompt! Example: `!generate a cat wearing a hat`")
        return
    
    # Send initial response
    message = await ctx.send(f"🎨 Generating image for: `{prompt[:100]}...`")
    
    try:
        # Prepare API request
        url = f"{WEBUI_URL}/sdapi/v1/txt2img"
        payload = {
            "prompt": prompt,
            "negative_prompt": "blurry, low quality, distorted, bad anatomy, worst quality",
            "steps": 25,
            "width": 512,
            "height": 512,
            "cfg_scale": 7.0,
            "sampler_index": "Euler a",
            "seed": -1,
            "send_images": True,
            "save_images": False
        }
        
        # Make the request
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code == 200:
            r = response.json()
            
            # Convert base64 to image
            image_data = base64.b64decode(r['images'][0])
            
            # Send to Discord
            file = discord.File(BytesIO(image_data), filename="generated_image.png")
            await message.edit(content=f"✅ Generated image for: `{prompt[:50]}...`")
            await ctx.send(file=file)
            
        else:
            await message.edit(content=f"❌ Generation failed with status {response.status_code}")
            
    except requests.exceptions.Timeout:
        await message.edit(content="❌ Generation timed out. Try a simpler prompt or check if WebUI is running.")
    except requests.exceptions.ConnectionError:
        await message.edit(content="❌ Cannot connect to Stable Diffusion. Make sure WebUI is running!")
    except Exception as e:
        await message.edit(content=f"❌ Error: {str(e)}")

@bot.command(name='fanny')
async def generate_fanny(ctx, *, custom_prompt=""):
    """Generate Fanny character art
    Usage: !fanny
           !fanny sitting in classroom
           !fanny holding sword
    """
    
    # Base Fanny prompt with trigger words
    base_prompt = "<lora:Fanny:1.0> masterpiece, best quality, fanny, 1girl, blonde hair, green eyes, short hair"
    
    if custom_prompt:
        full_prompt = f"{base_prompt}, {custom_prompt}"
    else:
        full_prompt = f"{base_prompt}, detailed face, cowboy shot"
    
    await ctx.send(f"🎨 Generating Fanny: `{custom_prompt if custom_prompt else 'default pose'}`...")
    
    try:
        url = f"{WEBUI_URL}/sdapi/v1/txt2img"
        payload = {
            "prompt": full_prompt,
            "negative_prompt": "blurry, low quality, bad anatomy, worst quality, extra fingers, bad hands",
            "steps": 25,
            "width": 512,
            "height": 512,
            "cfg_scale": 7.0,
            "sampler_index": "Euler a",
            "seed": -1,
            "send_images": True,
            "save_images": False
        }
        
        response = requests.post(url, json=payload, timeout=120)
        
        if response.status_code == 200:
            r = response.json()
            image_data = base64.b64decode(r['images'][0])
            file = discord.File(BytesIO(image_data), filename="fanny.png")
            await ctx.send(file=file)
        else:
            await ctx.send(f"❌ Generation failed: {response.status_code}")
            
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='help_bot')
async def help_command(ctx):
    """Show help for image generation commands"""
    embed = discord.Embed(
        title="🎨 Image Generation Bot",
        description="Generate images using Stable Diffusion!",
        color=0x00ff00
    )
    embed.add_field(
        name="Commands",
        value=(
            "`!generate <prompt>` - Generate any image\n"
            "`!fanny <prompt>` - Generate Fanny character\n"
            "`!help_bot` - Show this help"
        ),
        inline=False
    )
    embed.add_field(
        name="Examples",
        value=(
            "`!generate a cute cat in a garden`\n"
            "`!fanny holding a sword in combat pose`\n"
            "`!fanny sitting in classroom`"
        ),
        inline=False
    )
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status_command(ctx):
    """Check if the Stable Diffusion API is working"""
    try:
        response = requests.get(f"{WEBUI_URL}/sdapi/v1/samplers", timeout=5)
        if response.status_code == 200:
            await ctx.send("✅ Stable Diffusion API is working!")
        else:
            await ctx.send(f"❌ API returned status: {response.status_code}")
    except Exception as e:
        await ctx.send(f"❌ Cannot connect to API: {str(e)}")

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Command not found. Use `!help_bot` to see available commands.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required argument. Check the command usage.")
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")

# Run the bot
if __name__ == "__main__":
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ Please set your bot token in the BOT_TOKEN variable")
    else:
        bot.run(BOT_TOKEN)