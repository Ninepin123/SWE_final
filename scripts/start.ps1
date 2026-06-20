# ============================================================
# NUKSAMS 一鍵啟動腳本（由 start.bat 呼叫；組長維護）
# 功能：檢查環境 -> venv/pip -> .env -> 可攜版 MySQL（自動下載/啟動）
#       -> 資料庫初始化 -> npm install -> 啟動前後端 -> 開瀏覽器
# 冪等設計：重複執行不會壞，套件只在有變動時重裝。
# ============================================================
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"  # 加速 Invoke-WebRequest / Expand-Archive
$root = Split-Path -Parent $PSScriptRoot

# 可攜版 MySQL 設定（改版本時這裡與 docs 一起改）
# 多個下載來源依序嘗試（Oracle 官方站不穩定，鏡像站為主）。
# 注意：固定使用 8.0.28——不要換成 8.0.29（該版有 InnoDB 重大 bug 被官方撤回）。
$mysqlZipUrls = @(
    "https://ftp.jaist.ac.jp/pub/mysql/Downloads/MySQL-8.0/mysql-8.0.28-winx64.zip",
    "https://mirrors.dotsrc.org/mysql/Downloads/MySQL-8.0/mysql-8.0.28-winx64.zip",
    "https://cdn.mysql.com//Downloads/MySQL-8.0/mysql-8.0.28-winx64.zip"
)
$mysqlHome = Join-Path $root "tools\mysql"        # 解壓位置（gitignored）
$mysqlData = Join-Path $root "tools\mysql-data"   # 資料目錄（gitignored）
$mysqlPort = 3307                                  # 避開本機既有 MySQL 的 3306

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Fail($msg) { Write-Host "[X] $msg" -ForegroundColor Red; exit 1 }
function Test-Port($h, $p) {
    try {
        $c = New-Object Net.Sockets.TcpClient
        $c.Connect($h, $p); $c.Close(); return $true
    } catch { return $false }
}

# ---------- 1. 檢查必要工具 ----------
Step "檢查環境"
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Fail "找不到 Node.js（需要 20+）。請安裝：https://nodejs.org/ 後重新執行。"
}
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Fail "找不到 Python（需要 3.10+）。請安裝：https://www.python.org/downloads/（記得勾 Add to PATH）後重新執行。"
}
Write-Host ("Node {0} / {1}" -f (node --version), (python --version))

# ---------- 2. 後端 venv 與套件 ----------
Step "後端環境 (backend/.venv)"
$venv = Join-Path $root "backend\.venv"
$py = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "建立虛擬環境中..."
    python -m venv $venv
    if ($LASTEXITCODE -ne 0) { Fail "建立 venv 失敗" }
}
# requirements.txt 有變動才重新 pip install（用雜湊值比對）
$req = Join-Path $root "backend\requirements.txt"
$stamp = Join-Path $venv "requirements.stamp"
$reqHash = (Get-FileHash $req -Algorithm SHA256).Hash
$oldHash = ""
if (Test-Path $stamp) { $oldHash = (Get-Content $stamp -Raw).Trim() }
if ($oldHash -ne $reqHash) {
    Write-Host "安裝/更新 Python 套件中（第一次會比較久）..."
    & $py -m pip install -r $req --quiet --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) { Fail "pip install 失敗，請看上方錯誤訊息" }
    Set-Content -Path $stamp -Value $reqHash
} else {
    Write-Host "Python 套件已是最新，略過安裝。"
}

# ---------- 3. backend/.env ----------
$envFile = Join-Path $root "backend\.env"
if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $root "backend\.env.example") $envFile
    Write-Host "已自動建立 backend/.env（使用可攜版 MySQL 預設設定）"
}

# ---------- 4. MySQL 伺服器（可攜版，自動下載，免安裝） ----------
Step "資料庫伺服器 (MySQL)"
# 從 .env 解析 host:port——若組員自己改用本機安裝的 MySQL(3306)，腳本會直接沿用
$envText = Get-Content $envFile -Raw
$dbHost = "127.0.0.1"; $dbPort = $mysqlPort
$m = [regex]::Match($envText, 'mysql\+pymysql://[^@]+@([^:/]+):(\d+)/')
if ($m.Success) { $dbHost = $m.Groups[1].Value; $dbPort = [int]$m.Groups[2].Value }

if (Test-Port $dbHost $dbPort) {
    Write-Host "MySQL 已在 ${dbHost}:${dbPort} 運行，直接使用。"
} elseif (($dbHost -ne "127.0.0.1" -and $dbHost -ne "localhost") -or $dbPort -ne $mysqlPort) {
    Fail "backend/.env 指定的 MySQL（${dbHost}:${dbPort}）沒有回應。請先啟動你自己的 MySQL，或把 .env 改回預設（127.0.0.1:${mysqlPort}）讓腳本使用可攜版。"
} else {
    # 4-1. 沒有可攜版就自動下載解壓（只需一次）
    $mysqld = Get-ChildItem -Path $mysqlHome -Filter mysqld.exe -Recurse -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $mysqld) {
        Write-Host "第一次使用：下載可攜版 MySQL（約 200MB，只需一次，請稍候）..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $zipPath = Join-Path $env:TEMP "nuksams-mysql.zip"
        $downloaded = $false
        foreach ($url in $mysqlZipUrls) {
            try {
                Write-Host "  嘗試來源：$url"
                Invoke-WebRequest -Uri $url -OutFile $zipPath -UserAgent "Mozilla/5.0" -UseBasicParsing
                if ((Get-Item $zipPath).Length -gt 100MB) { $downloaded = $true; break }
            } catch {
                Write-Host "  此來源失敗，換下一個..." -ForegroundColor Yellow
            }
        }
        if (-not $downloaded) { Fail "所有下載來源都失敗。請檢查網路連線後重試；持續失敗請回報群組（可請已下載成功的組員直接把 tools\mysql 資料夾整包傳給你）。" }
        Write-Host "解壓縮中..."
        New-Item -ItemType Directory -Force -Path $mysqlHome | Out-Null
        Expand-Archive -Path $zipPath -DestinationPath $mysqlHome -Force
        Remove-Item $zipPath -Force -Confirm:$false
        $mysqld = Get-ChildItem -Path $mysqlHome -Filter mysqld.exe -Recurse -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if (-not $mysqld) { Fail "下載/解壓 MySQL 失敗，請重新執行一次；多次失敗請回報群組。" }
    }
    $baseDir = Split-Path -Parent (Split-Path -Parent $mysqld.FullName)  # bin 的上一層

    # 4-2. 第一次初始化資料目錄（root 無密碼，僅限本機開發）
    if (-not (Test-Path (Join-Path $mysqlData "mysql"))) {
        Write-Host "初始化 MySQL 資料目錄..."
        & $mysqld.FullName --initialize-insecure --basedir="$baseDir" --datadir="$mysqlData"
        if ($LASTEXITCODE -ne 0) { Fail "MySQL 初始化失敗。若訊息提到缺少 VCRUNTIME140.dll，請先安裝 VC++ 執行環境：https://aka.ms/vs/17/release/vc_redist.x64.exe" }
    }

    # 4-3. 開一個視窗跑 MySQL（之後重跑 start.bat 會偵測到已啟動而跳過）
    Write-Host "啟動 MySQL（port ${mysqlPort}）..."
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command",
        "`$host.UI.RawUI.WindowTitle='NUKSAMS MySQL (請保持開啟；關閉視窗即停止資料庫)'; & '$($mysqld.FullName)' --console --basedir='$baseDir' --datadir='$mysqlData' --port=$mysqlPort"
    )
    $deadline = (Get-Date).AddSeconds(60)
    while (-not (Test-Port $dbHost $dbPort)) {
        if ((Get-Date) -gt $deadline) {
            Fail "MySQL 啟動逾時。請看 MySQL 視窗的錯誤訊息；若提到缺少 VCRUNTIME140.dll，請安裝：https://aka.ms/vs/17/release/vc_redist.x64.exe"
        }
        Start-Sleep -Milliseconds 500
    }
    Write-Host "MySQL 已啟動。"
}

# ---------- 5. 資料庫初始化 / 更新 ----------
Step "資料庫 schema"
& $py (Join-Path $root "scripts\init_db.py")
if ($LASTEXITCODE -ne 0) { Fail "資料庫初始化失敗（見上方訊息）" }

Step "預設管理員帳號"
Push-Location (Join-Path $root "backend")
& $py -m app.modules.aas.bootstrap_admin
$adminCode = $LASTEXITCODE
Pop-Location
if ($adminCode -ne 0) { Fail "建立預設管理員帳號失敗（見上方訊息）" }

# ---------- 6. 前端套件 ----------
Step "前端環境 (frontend/node_modules)"
$needNpm = -not (Test-Path (Join-Path $root "frontend\node_modules"))
if (-not $needNpm) {
    # package.json 比 node_modules 新代表有人加了套件
    $pkgTime = (Get-Item (Join-Path $root "frontend\package.json")).LastWriteTime
    $nmTime = (Get-Item (Join-Path $root "frontend\node_modules")).LastWriteTime
    if ($pkgTime -gt $nmTime) { $needNpm = $true }
}
if ($needNpm) {
    Write-Host "npm install 中（第一次會比較久）..."
    Push-Location (Join-Path $root "frontend")
    npm install
    $npmCode = $LASTEXITCODE
    Pop-Location
    if ($npmCode -ne 0) { Fail "npm install 失敗，請看上方錯誤訊息" }
} else {
    Write-Host "npm 套件已是最新，略過安裝。"
}

# ---------- 7. 啟動前後端 ----------
Step "啟動服務"
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "`$host.UI.RawUI.WindowTitle='NUKSAMS 後端 (關閉視窗即停止)'; Set-Location '$root\backend'; & '$py' -m uvicorn app.main:app --reload"
)
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "`$host.UI.RawUI.WindowTitle='NUKSAMS 前端 (關閉視窗即停止)'; Set-Location '$root\frontend'; npm run dev"
)
Start-Sleep -Seconds 3
Start-Process "http://localhost:5173"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host " 啟動完成！" -ForegroundColor Green
Write-Host "   前端頁面      http://localhost:5173"
Write-Host "   後端 API 文件  http://localhost:8000/docs"
Write-Host " 存檔即熱重載，直接改 code 直接測。"
Write-Host " 停止系統：關閉「前端」與「後端」兩個視窗；"
Write-Host " 「MySQL」視窗可以留著，下次啟動會直接沿用。"
Write-Host "=========================================" -ForegroundColor Green
