
# Script de automação para deploy no Render.com
param ([string]$Repo = "allan/bolsas-automation-app")
Write-Host "🚀 Iniciando push e deploy automático para $Repo..." -ForegroundColor Cyan
if (-not (Test-Path Env:RENDER_API_KEY)) {
    Write-Host "❌ ERRO: variável de ambiente RENDER_API_KEY não encontrada!" -ForegroundColor Red
    exit
}
git add .
git commit -m "Deploy automático via PowerShell"
git push origin main
$service_id = $Env:RENDER_SERVICE_ID
if (-not $service_id) {
    Write-Host "❌ ERRO: variável de ambiente RENDER_SERVICE_ID não encontrada!" -ForegroundColor Red
    exit
}
Write-Host "⏳ Solicitando deploy no Render..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$service_id/deploys" `
    -Headers @{ "Authorization" = "Bearer $Env:RENDER_API_KEY" } `
    -Method Post
Write-Host "✅ Deploy iniciado com ID: $($response.id)" -ForegroundColor Green
Start-Process "https://render.com/deploys/$($response.id)"
Write-Host "🌐 Render aberto no navegador. Aguarde alguns minutos para o deploy completar."
