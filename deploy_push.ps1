# deploy_push.ps1 — Envia código para o GitHub e inicia deploy no Render

Write-Host "🚀 Iniciando script de deploy automático..." -ForegroundColor Cyan

# Lê variáveis do arquivo .env
$envFile = ".env"
if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    if ($envContent -match "RENDER_API_KEY=(.*)") {
        $renderApiKey = $matches[1].Trim()
    }
    if ($envContent -match "RENDER_SERVICE_ID=(.*)") {
        $renderServiceId = $matches[1].Trim()
    }
} else {
    Write-Host "⚠️  Arquivo .env não encontrado! Crie um com RENDER_API_KEY e RENDER_SERVICE_ID." -ForegroundColor Yellow
    exit
}

# Faz commit e push no GitHub
Write-Host "💾 Enviando alterações ao GitHub..." -ForegroundColor Cyan
git add .
git commit -m "🚀 Deploy automático via PowerShell" 2>$null
git push origin main

Write-Host "✅ Código enviado com sucesso." -ForegroundColor Green

# Dispara o deploy no Render
if ($renderApiKey -and $renderServiceId) {
    Write-Host "🌎 Solicitando deploy no Render..." -ForegroundColor Cyan
    try {
        $headers = @{
            "Authorization" = "Bearer $renderApiKey"
            "Accept" = "application/json"
            "Content-Type" = "application/json"
        }
        $body = @{}
        $response = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$renderServiceId/deploys" -Method POST -Headers $headers -Body ($body | ConvertTo-Json)
        Write-Host "✅ Deploy iniciado com ID: $($response.id)" -ForegroundColor Green
    } catch {
        Write-Host "❌ Erro ao solicitar deploy no Render: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "⚠️  Variáveis RENDER_API_KEY ou RENDER_SERVICE_ID ausentes no .env" -ForegroundColor Yellow
}

Start-Process "https://render.com"
Write-Host "🌐 Render aberto no navegador. Aguarde alguns minutos para o deploy completar." -ForegroundColor Cyan
