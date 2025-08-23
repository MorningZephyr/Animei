# 🎨 Discord AI Image Generator Bot

A Discord bot that generates images from text prompts using Stable Diffusion.

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
# Install PyTorch with CUDA support
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Install other requirements
pip install discord.py python-dotenv diffusers transformers accelerate safetensors pillow numpy
```

### 2. Configure Bot Token
```bash
# Copy the template and add your token
copy env_template.txt .env
# Edit .env and add your Discord bot token
```

### 3. Run the Bot
```bash
python bot.py
```

## 🎮 Commands

### Basic Usage
- `!generate <prompt>` - Generate an image from text
- `!gen <prompt>` - Short form
- `!img <prompt>` - Alternative

### Advanced Usage
- `!advanced <steps> <guidance> <seed> <prompt>` - Custom parameters
- `!info` - Show bot and model information
- `!help_ai` - Show all commands

### Examples
```
!gen a beautiful sunset over mountains
!advanced 30 8.0 42 detailed portrait of a warrior
!img futuristic cityscape at night
```

## ⚙️ Features

- ✅ GPU/CPU auto-detection
- ✅ Memory optimization for CUDA
- ✅ Progress feedback while generating
- ✅ Parameter validation and limits
- ✅ Beautiful Discord embeds
- ✅ Error handling and recovery

## 🛠 Technical Details

- **Model**: Stable Diffusion v1.5 (default)
- **Scheduler**: DPM++ Multistep
- **Framework**: Hugging Face Diffusers
- **Requirements**: Python 3.8+, PyTorch 2.0+

## 📊 Performance

- **GPU (CUDA)**: 10-30 seconds per image
- **CPU**: 2-5 minutes per image
- **Memory**: 4-8GB VRAM recommended

## 🔧 Troubleshooting

### CUDA Out of Memory
- Reduce image size or steps
- Enable memory efficient attention
- Close other GPU applications

### Model Loading Issues
- Check internet connection
- Verify disk space (models are ~5GB)
- Try restarting the bot

### Bot Not Responding
- Check Discord bot permissions
- Verify token in .env file
- Ensure bot is in a server
