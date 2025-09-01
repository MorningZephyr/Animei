import discord
from discord.ext import commands
import asyncio
from stable_diffusion_bot import StableDiffusionGenerator
from ui_modal import UIModal
from generation_service import GenerationService
from config import config

# --- Loading the Bot ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize the image generator
image_generator = StableDiffusionGenerator()

# Initialize the generation service (owns everything)
generation_service = GenerationService(image_generator)

# Get queue manager from service for other components that need it
queue_manager = generation_service.get_queue_manager()

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
    asyncio.create_task(image_generator.load_model())
    
    # Wait for model to load
    while image_generator.pipe is None:
        await asyncio.sleep(1)
    
    # Start the queue worker
    await queue_manager.start_worker()
    
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
    """This is called when the bot is starting up"""
    await bot.tree.sync()  # Sync slash commands with Discord
    print("Slash commands synced!")

@bot.tree.command(name="generate", description="Press Enter for modal interface!")
async def generate_modal_command(interaction: discord.Interaction):
    """Opens a modal form for advanced image generation"""
    modal = UIModal(generation_service)                 # Creates the modal instance in memory
    await interaction.response.send_modal(modal)        # Sends the modal to the user

@bot.tree.command(name="queue", description="Check the current queue status")
async def queue_status_command(interaction: discord.Interaction):
    """Shows current queue status"""
    status = queue_manager.get_queue_status()
    
    embed = discord.Embed(title="📊 Queue Status", color=0x00ff00)
    embed.add_field(name="Requests in Queue", value=str(status["queue_size"]), inline=True)
    embed.add_field(name="Max Queue Size", value=str(status["max_size"]), inline=True)
    embed.add_field(name="Processing", value="Yes" if status["is_processing"] else "No", inline=True)
    
    if status["current_request_id"]:
        embed.add_field(name="Current Request", value=status["current_request_id"], inline=False)
    
    if status["queue_size"] > 0:
        embed.add_field(name="Estimated Wait", value=f"~{status['queue_size'] * 10} seconds", inline=False)
    
    await interaction.response.send_message(embed=embed)

if __name__ == "__main__":
    try:
        bot.run(config.discord_token)
    except KeyboardInterrupt:
        print("\n⚠️ Shutdown requested by user (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Clean up resources
        asyncio.run(queue_manager.stop_worker())
        image_generator.cleanup()
        print("✅ Bot shutdown complete!")