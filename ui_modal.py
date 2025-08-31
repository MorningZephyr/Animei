import discord

class UIModal(discord.ui.Modal):
    """Pure UI modal class for collecting generation request data"""
    
    def __init__(self, generation_service):
        super().__init__(title="🎨 AniMei: Image Generator")
        self.generation_service = generation_service
        
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
        
        # Add all inputs to the modal
        self.add_item(self.prompt)
        self.add_item(self.negative)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Collect form data and delegate to generation service"""
        # Prepare prompt data
        prompt_data = {
            'prompt': self.prompt.value,
            'negative_prompt': self.negative.value,
            'user_id': str(interaction.user.id),
            'channel_id': str(interaction.channel.id)
        }
        
        # Delegate all business logic to the service
        await self.generation_service.handle_generation_request(interaction, prompt_data)
