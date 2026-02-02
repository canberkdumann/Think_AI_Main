#!/bin/bash

echo "🚀 Think AI Starting..."

docker-compose down
docker-compose up -d

echo "⏳ Waiting for containers..."
sleep 15

echo "🔥 Warming up models (optional, may take 30s)..."
docker exec think-ai-ollama ollama run qwen2.5:7b "test" > /dev/null 2>&1
docker exec think-ai-ollama ollama run gemma2:9b "test" > /dev/null 2>&1

echo "✅ Think AI is running!"
echo "📊 Gradio UI: http://localhost:7860"