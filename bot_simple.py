import discord
from discord.ext import commands
import io
import os
import asyncio
from stable_diffusion_bot import StableDiffusionBot, GenerationRequest
from dotenv import load_dotenv
import uuid

load_dotenv()

# --- Modal Class for Advanced Generation ---
class UIModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="🎨 AniMei: Image Generator")
        
        # Large text area for main prompt
        self.prompt = discord.ui.TextInput(
            label="Image prompt (use commas between keywords)",
            style=discord.TextStyle.paragraph,  # Multi-line text box
            placeholder=" ex: 1girl, mochi, pajamas, sleeping",
            max_length=400,  # ~75 tokens for CLIP (most words are 1-2 tokens)
            required=True
        )
        
        # Negative prompt
        self.negative = discord.ui.TextInput(
            label="What to avoid (optional)",
            style=discord.TextStyle.paragraph,
            placeholder="bad anatomy, bad hands, blurry, low quality, text, watermark, missing fingers",
            max_length=300,  # ~50 tokens for negative prompt + safety filters
            required=False
        )
        
        # Steps
        self.steps = discord.ui.TextInput(
            label="Steps (10-50)",
            style=discord.TextStyle.short,
            placeholder="25",
            default="25",
            required=False
        )
        
        # CFG Scale
        self.cfg_scale = discord.ui.TextInput(
            label="CFG Scale (1.0-20.0)",
            style=discord.TextStyle.short,
            placeholder="7.0",
            default="7.0",
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
        
        # Check if queue is full
        queue_status = sd_bot.get_queue_status()
        if queue_status["queue_size"] >= queue_status["max_size"]:
            await interaction.response.send_message("❌ Queue is full! Please try again later.")
            return
        
        # Defer the response since we're adding to queue
        await interaction.response.defer()
        
        # Parse user inputs with validation
        try:
            steps = int(self.steps.value) if self.steps.value.isdigit() else 25
            steps = max(10, min(50, steps))  # Clamp between 10-50
            
            cfg_scale = float(self.cfg_scale.value) if self.cfg_scale.value.replace('.', '').isdigit() else 7.0
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
            steps = 25
            cfg_scale = 7.0
            width = height = 512
        
        # Create callback function to send image when ready
        async def send_completed_image(image, request):
            """Callback function to send the generated image to Discord"""
            try:
                # Convert PIL image to Discord file
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                buffer.seek(0)
                
                file = discord.File(buffer, filename=f"generated_{request.request_id[:8]}.png")
                
                # Create result embed
                embed = discord.Embed(title="✨ Generated Image", color=0x00ff00)
                embed.add_field(name="Request ID", value=request.request_id[:8], inline=True)
                embed.add_field(name="Steps", value=str(request.num_inference_steps), inline=True)
                embed.add_field(name="CFG Scale", value=str(request.cfg_scale), inline=True)
                embed.add_field(name="Size", value=f"{request.width}x{request.height}", inline=True)
                embed.add_field(name="Prompt", value=request.prompt[:100] + "..." if len(request.prompt) > 100 else request.prompt, inline=False)
                
                # Send the final image
                await interaction.followup.send(embed=embed, file=file)
                print(f"📤 Sent completed image for request {request.request_id[:8]} to user {request.user_id}")
                
            except Exception as e:
                error_embed = discord.Embed(title="❌ Image Delivery Failed", color=0xff0000)
                error_embed.add_field(name="Request ID", value=request.request_id[:8], inline=True)
                error_embed.add_field(name="Error", value=str(e), inline=False)
                await interaction.followup.send(embed=error_embed)
                print(f"❌ Failed to send image for request {request.request_id[:8]}: {e}")

        # Create generation request
        try:
            request = GenerationRequest(
                request_id=str(uuid.uuid4()),
                prompt=self.prompt.value,
                negative_prompt=self.negative.value,
                num_inference_steps=steps,
                cfg_scale=cfg_scale,
                width=width,
                height=height,
                user_id=str(interaction.user.id),
                channel_id=str(interaction.channel.id),
                callback=send_completed_image,
                callback_data={"interaction": interaction}
            )
            
            # Add to queue
            success = await sd_bot.add_to_queue(request)
            if not success:
                await interaction.followup.send("❌ Failed to add request to queue. Please try again later.")
                return
            
            # Get current queue status
            queue_status = sd_bot.get_queue_status()
            
            # Send queue confirmation
            embed = discord.Embed(title="📥 Request Added to Queue", color=0xffa500)
            embed.add_field(name="Request ID", value=request.request_id[:8], inline=True)
            embed.add_field(name="Position in Queue", value=str(queue_status["queue_size"]), inline=True)
            embed.add_field(name="Estimated Wait", value=f"~{queue_status['queue_size'] * 30} seconds", inline=True)
            embed.add_field(name="Prompt", value=self.prompt.value[:100] + "..." if len(self.prompt.value) > 100 else self.prompt.value, inline=False)
            
            # Add note about current processing
            if queue_status["is_processing"]:
                embed.add_field(name="Currently Processing", value=f"Request {queue_status['current_request_id']}", inline=False)
            
            # Add delivery info
            embed.add_field(name="📬 Delivery", value="Your image will be sent here automatically when ready!", inline=False)
            embed.set_footer(text="You can use /queue to check status anytime")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error adding request to queue: {str(e)}")

# --- Loading the Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

sd_bot = StableDiffusionBot()

# --- Setting the event listener ---
@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online!")
    
    # Set loading status
    await bot.change_presence(
        status=discord.Status.idle,  # Yellow dot
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="Loading AI Model..."
        )
    )
    
    # Start loading model in background
    asyncio.create_task(sd_bot.load_model())
    
    # Wait for model to load
    while sd_bot.pipe is None:
        await asyncio.sleep(1)
    
    # Start the queue worker
    await sd_bot.start_queue_worker()
    
    # Update status when ready
    await bot.change_presence(
        status=discord.Status.online,  # Green dot
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="/generate"
        )
    )
    print("✅ AI model loaded and queue worker started!")

@bot.event
async def setup_hook():
    await bot.tree.sync()  # Sync slash commands with Discord
    print("Slash commands synced!")

@bot.tree.command(name="generate", description="Press Enter for modal interface!")
async def generate_modal_command(interaction: discord.Interaction):
    """Opens a modal form for advanced image generation"""
    modal = UIModal()
    await interaction.response.send_modal(modal)

@bot.tree.command(name="queue", description="Check the current queue status")
async def queue_status_command(interaction: discord.Interaction):
    """Shows current queue status"""
    status = sd_bot.get_queue_status()
    
    embed = discord.Embed(title="📊 Queue Status", color=0x00ff00)
    embed.add_field(name="Requests in Queue", value=str(status["queue_size"]), inline=True)
    embed.add_field(name="Max Queue Size", value=str(status["max_size"]), inline=True)
    embed.add_field(name="Processing", value="Yes" if status["is_processing"] else "No", inline=True)
    
    if status["current_request_id"]:
        embed.add_field(name="Current Request", value=status["current_request_id"], inline=False)
    
    if status["queue_size"] > 0:
        embed.add_field(name="Estimated Wait", value=f"~{status['queue_size'] * 30} seconds", inline=False)
    
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    try:
        bot.run(os.getenv('DISCORD_BOT_TOKEN'))
    except KeyboardInterrupt:
        print("\n⚠️ Shutdown requested by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Clean up resources
        asyncio.run(sd_bot.stop_queue_worker())
        sd_bot.cleanup()
        print("✅ Bot shutdown complete!")