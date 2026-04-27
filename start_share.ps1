# Inicia (ou reinicia) o servidor estatico + tunnel publico Cloudflare.
# Uso: powershell -File C:\Projects\cac-by-product\start_share.ps1

$ErrorActionPreference = "SilentlyContinue"
$dir   = "C:\Projects\cac-by-product"
$port  = 8766
$cf    = "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe"
$cflog = "$dir\cloudflared.log"
$pylog = "$dir\httpserver.log"

# Mata processos antigos rodando na porta ou cloudflared antigo do dashboard
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1

# Inicia http.server Python em background
$py = Start-Process -FilePath "python" `
    -ArgumentList "-m","http.server",$port,"--directory",$dir `
    -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $pylog -RedirectStandardError "$dir\httpserver.err"

Write-Host "HTTP server PID: $($py.Id) on port $port"

# Inicia tunnel
$tn = Start-Process -FilePath $cf `
    -ArgumentList "tunnel","--url","http://localhost:$port","--logfile",$cflog `
    -WindowStyle Hidden -PassThru

Write-Host "cloudflared PID: $($tn.Id)"
Write-Host "Aguardando URL publica..."

# Espera URL aparecer no log (ate 30s)
$url = $null
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    $logContent = Get-Content $cflog -ErrorAction SilentlyContinue -Raw
    if ($logContent -match "https://[a-z0-9-]+\.trycloudflare\.com") {
        $url = $matches[0]
        break
    }
}

if ($url) {
    Set-Content -Path "$dir\PUBLIC_URL.txt" -Value "$url/dashboard_cac_br.html" -Encoding UTF8
    Write-Host ""
    Write-Host "=== LINK PUBLICO ==="
    Write-Host "$url/dashboard_cac_br.html"
    Write-Host "===================="
    Write-Host "Salvo em $dir\PUBLIC_URL.txt"
} else {
    Write-Host "ERRO: URL publica nao apareceu em 30s. Veja $cflog"
    exit 1
}
