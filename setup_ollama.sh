#!/bin/bash

# Quick setup script for Ollama with DeepSeek Coder
# This script helps you set up Ollama for document generation

set -e

echo "🚀 Ollama Setup for TechDocGen"
echo "================================"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo ""
    echo "Please install Ollama first:"
    echo "  macOS:   brew install ollama"
    echo "  Linux:   curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Windows: Download from https://ollama.ai/download"
    echo ""
    exit 1
fi

echo "✅ Ollama is installed"
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama service is not running. Starting it..."
    echo "   (This may take a moment)"
    ollama serve &
    sleep 3
fi

echo "✅ Ollama service is running"
echo ""

# Show available models
echo "📋 Currently installed models:"
ollama list
echo ""

# Ask which model to install
echo "Which model would you like to use?"
echo "  1) deepseek-coder:6.7b (Recommended - ~8GB RAM, best balance)"
echo "  2) deepseek-coder:33b (Best quality - ~24GB RAM)"
echo "  3) codellama:13b (~10GB RAM, good quality)"
echo "  4) qwen2.5-coder:7b (~6GB RAM, fast)"
echo "  5) llama3.2:3b (~4GB RAM, lightweight)"
echo "  6) Skip (use existing model)"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        MODEL="deepseek-coder:6.7b"
        ;;
    2)
        MODEL="deepseek-coder:33b"
        ;;
    3)
        MODEL="codellama:13b"
        ;;
    4)
        MODEL="qwen2.5-coder:7b"
        ;;
    5)
        MODEL="llama3.2:3b"
        ;;
    6)
        echo "✅ Skipping model installation"
        echo ""
        echo "To use Ollama:"
        echo "  1. Update config.yaml with your model name"
        echo "  2. Run: python main.py --source ./src --type folder --provider ollama"
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "📥 Pulling model: $MODEL"
echo "   (This may take several minutes depending on your internet speed)"
echo ""

ollama pull "$MODEL"

echo ""
echo "✅ Model installed successfully!"
echo ""

# Update config.yaml
echo "📝 Updating config.yaml..."
if [ -f "config.yaml" ]; then
    # Create backup
    cp config.yaml config.yaml.backup
    
    # Update model in config (using sed for macOS/Linux compatibility)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/model:.*llama3.2.*/model: $MODEL/" config.yaml
    else
        # Linux
        sed -i "s/model:.*llama3.2.*/model: $MODEL/" config.yaml
    fi
    
    echo "✅ config.yaml updated with model: $MODEL"
    echo "   (Backup saved as config.yaml.backup)"
else
    echo "⚠️  config.yaml not found. Please update it manually with:"
    echo "   model: $MODEL"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Verify Ollama is running: ollama list"
echo "  2. Test the model: ollama run $MODEL 'Hello'"
echo "  3. Generate documentation:"
echo "     python main.py --source ./src --type folder --provider ollama"
echo "  4. Or use the Web UI:"
echo "     streamlit run app.py"
echo ""
echo "For detailed instructions, see OLLAMA_SETUP_GUIDE.md"
echo ""







