# ======================================================================
# 🚀 Deploy automático para Render.com com verificação de API Key e logs
# ======================================================================

Write-Host "🔍 Verificando configuração..." -ForegroundColor Cyan

# Caminho do arquivo .env
$envFile = ".env"

# Verifica se .env existe
if (-Not (Test-Path $envFile)) {
    Write-Host "❌ Arquivo .env não encontrado. Crie um e adicione sua RENDER_API_KEY." -ForegroundColor Red
    exit 1
}

# Carrega o .env e extrai o token
$envContent = Get-Content $envFile | Where-Object { $_ -match "RENDER_API_KEY" }
if ($envContent -match "RENDER_API_KEY=(.+)") {
    $apiKey = $matches[1].Trim()
} else {
    Write-Host "❌ Variável RENDER_API_KEY não encontrada no .env" -ForegroundColor Red
    exit 1
}

# Testa se o token é válido
Write-Host "🧩 Validando token do Render..." -ForegroundColor Cyan
try {
    $headers = @{ "Authorization" = "Bearer $apiKey" }
    $check = Invoke-RestMethod -Uri "https://api.render.com/v1/services" -Headers $headers -Method Get -ErrorAction Stop
    Write-Host "✅ Token válido! Render API conectada." -ForegroundColor Green
} catch {
    Write-Host "❌ Token inválido ou expirado. Gere um novo em https://render.com/docs/api" -ForegroundColor Red
    exit 1
}

# Envia push para GitHub
Write-Host "📦 Enviando código atualizado para o GitHub..." -ForegroundColor Yellow
git add .
git commit -m "Atualização automática via deploy_push.ps1" 2>$null
git push origin main
Write-Host "✅ Código enviado com sucesso." -ForegroundColor Green

# Solicita o deploy no Render
Write-Host "🌱 Solicitando deploy no Render..." -ForegroundColor Yellow
try {
    $serviceId = Read-Host "👉 Digite o ID do serviço Render (ou deixe em branco para apenas abrir o site)"
    if ($serviceId) {
        $response = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$serviceId/deploys" -Headers $headers -Method Post
        Write-Host "✅ Deploy iniciado com ID: $($response.id)" -ForegroundColor Green
    } else {
        Write-Host "ℹ️ Nenhum ID informado — apenas abrindo painel Render..." -ForegroundColor Cyan
    }
} catch {
    Write-Host "⚠️ Falha ao solicitar deploy via API. Verifique se o ID do serviço está correto." -ForegroundColor Red
}

# Abre o Render no navegador
Start-Process "https://render.com/dashboard"
Write-Host "🌍 Render aberto no navegador. Aguarde alguns minutos para o deploy completar." -ForegroundColor Green
