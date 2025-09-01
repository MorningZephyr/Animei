import discord
import io
import uuid
from schema import GenerationRequest
from queue_manager import QueueManager

class GenerationService:
    """Service class that handles all generation request business logic"""
    
    def __init__(self, sd_bot):
        self.sd_bot = sd_bot
        self.queue_manager = QueueManager(sd_bot)
        self.user_request_tracker = {}  # Track user request frequency
        self.max_requests_per_minute = 3  # Rate limit per user
    
    def get_queue_manager(self):
        """Get the queue manager for other components that need it"""
        return self.queue_manager
    
    async def handle_generation_request(self, interaction: discord.Interaction, prompt_data: dict):
        """Main entry point for handling generation requests"""
        try:
            # Validate the request
            validation_result = await self._validate_request(prompt_data)
            if not validation_result["valid"]:
                await interaction.response.send_message(validation_result["message"])
                return
            
            # Defer the response since we're adding to queue
            await interaction.response.defer()
            
            # Create and queue the generation request
            request = await self._create_and_queue_request(interaction, prompt_data)
            if not request:
                await interaction.followup.send("❌ Failed to add request to queue. Please try again later.")
                return
            
            # Send confirmation to user
            await self._send_queue_confirmation(interaction, request)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error processing request: {str(e)}")
            print(f"❌ Error in generation service: {e}")
    
    async def _validate_request(self, prompt_data: dict) -> dict:
        """Validate the generation request"""
        # Check if model is still loading
        if self.sd_bot.pipe is None:
            return {
                "valid": False,
                "message": "⏳ Model is still loading, please wait a moment and try again!"
            }
        
        # Check if queue is full
        queue_status = self.queue_manager.get_queue_status()
        if queue_status["queue_size"] >= queue_status["max_size"]:
            return {
                "valid": False,
                "message": "❌ Queue is full! Please try again later."
            }
        
        # Validate prompt length
        if len(prompt_data["prompt"]) < 3:
            return {
                "valid": False,
                "message": "❌ Prompt must be at least 3 characters long."
            }
        
        # Check user rate limit
        user_id = prompt_data["user_id"]
        if not self._check_user_rate_limit(user_id):
            return {
                "valid": False,
                "message": "⏳ You're making requests too quickly. Please wait a moment."
            }
        
        return {"valid": True}
    
    async def _create_and_queue_request(self, interaction: discord.Interaction, prompt_data: dict) -> GenerationRequest:
        """Create the generation request and add it to the queue"""
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
        request = GenerationRequest(
            request_id=str(uuid.uuid4()),
            prompt=prompt_data["prompt"],
            negative_prompt=prompt_data.get("negative_prompt", ""),
            num_inference_steps=None,  # Will use config default
            cfg_scale=None,  # Will use config default
            width=512,
            height=512,
            user_id=str(interaction.user.id),
            channel_id=str(interaction.channel.id),
            callback=send_completed_image,
            callback_data={"interaction": interaction}
        )
        
        # Add to queue
        success = await self.queue_manager.add_to_queue(request)
        if not success:
            return None
        
        return request
    
    async def _send_queue_confirmation(self, interaction: discord.Interaction, request: GenerationRequest):
        """Send confirmation message to user about their queued request"""
        queue_status = self.queue_manager.get_queue_status()
        
        # Create confirmation embed
        embed = discord.Embed(title="📥 Request Added to Queue", color=0xffa500)
        embed.add_field(name="Request ID", value=request.request_id[:8], inline=True)
        embed.add_field(name="Position in Queue", value=str(queue_status["queue_size"]), inline=True)
        embed.add_field(name="Estimated Wait", value=f"~{queue_status['queue_size'] * 10} seconds", inline=True)
        embed.add_field(name="Prompt", value=request.prompt[:100] + "..." if len(request.prompt) > 100 else request.prompt, inline=False)
        
        # Add note about current processing
        if queue_status["is_processing"]:
            embed.add_field(name="Currently Processing", value=f"Request {queue_status['current_request_id']}", inline=False)
        
        # Add delivery info
        embed.add_field(name="📬 Delivery", value="Your image will be sent here automatically when ready!", inline=False)
        embed.set_footer(text="You can use /queue to check status anytime")
        
        await interaction.followup.send(embed=embed)
    
    def _check_user_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit"""
        import time
        
        now = time.time()
        if user_id not in self.user_request_tracker:
            self.user_request_tracker[user_id] = []
        
        # Remove old requests (older than 1 minute)
        self.user_request_tracker[user_id] = [
            req_time for req_time in self.user_request_tracker[user_id] 
            if now - req_time < 60
        ]
        
        # Check if user has exceeded limit
        if len(self.user_request_tracker[user_id]) >= self.max_requests_per_minute:
            return False
        
        # Add current request
        self.user_request_tracker[user_id].append(now)
        return True
