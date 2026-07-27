#!/bin/bash

# Run Aider with Ollama.com configuration
# Place this in your repo root or ~/bin and run: chmod +x run-aider-ollama.sh

# Remove Anthropic config to stop Aider defaulting to Claude
unset ANTHROPIC_API_KEY
unset ANTHROPIC_API_BASE

# Configure Ollama.com API credentials
# Replace with your actual API key from ollama.com settings
export OLLAMA_API_KEY="${OLLAMA_API_KEY:-your-ollama-api-key-here}"

# Set Ollama.com endpoint (cloud hosted, not localhost:11434)
export OLLAMA_HOST="${OLLAMA_HOST:-https://api.ollama.com}"

# Set which model to use (kimi, llama3, mistral, etc.)
MODEL_NAME="${MODEL_NAME:-kimi}"

echo "Starting Aider with Ollama.com..."
echo "Host: $OLLAMA_HOST"
echo "Model: ollama/$MODEL_NAME"
echo ""

# Run aider with explicit Ollama model flag
# This prevents Aider from searching for Claude or other defaults
exec aider --model "ollama/$MODEL_NAME" "$@"
