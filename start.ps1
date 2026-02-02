Write-Host "Think AI Starting..." -ForegroundColor Green

docker-compose down
docker-compose up -d

Write-Host "Waiting for containers..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host "Warming up models (optional, may take 30s)..." -ForegroundColor Cyan
docker exec think-ai-ollama ollama run qwen2.5:7b "test" 2>$null | Out-Null
docker exec think-ai-ollama ollama run gemma2:9b "test" 2>$null | Out-Null

Write-Host "Think AI is running!" -ForegroundColor Green
Write-Host "Gradio UI: http://localhost:7860" -ForegroundColor Cyan