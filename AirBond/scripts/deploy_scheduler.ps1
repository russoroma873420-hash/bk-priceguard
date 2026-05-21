# BK-PriceGuard: register hourly Windows Scheduled Task
# Run from an elevated PowerShell:
#   powershell -ExecutionPolicy Bypass -File scripts\deploy_scheduler.ps1

$ErrorActionPreference = "Stop"

# Make sure русский/✅ rendering doesn't break the host console
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch { }

$TaskName   = "BK-PriceGuard"
$WorkingDir = "D:\bk-priceguard"
$Arguments  = "-m src.main --once"
$Description = "BK-PriceGuard: hourly competitor price monitor"

# ---------- 1. Admin rights check ----------
$identity  = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
$isAdmin   = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: запустите PowerShell от имени Администратора." -ForegroundColor Red
    Write-Host "       Правый клик на PowerShell -> Run as Administrator." -ForegroundColor Yellow
    exit 1
}

# ---------- 2. Consent prompt ----------
$consent = Read-Host "Установить автоматический запуск каждые 1 час? (Y/N)"
if ($consent -notmatch '^[Yy]') {
    Write-Host "Отменено пользователем." -ForegroundColor Yellow
    exit 0
}

# ---------- 3. Locate python.exe ----------
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $PythonPath = $pythonCmd.Source
    Write-Host "Найден Python: $PythonPath" -ForegroundColor Cyan
} else {
    Write-Host "python.exe не найден в PATH." -ForegroundColor Yellow
    $PythonPath = Read-Host "Введите полный путь к python.exe"
    if (-not (Test-Path $PythonPath)) {
        Write-Host "ERROR: файл '$PythonPath' не существует." -ForegroundColor Red
        exit 1
    }
}

# ---------- 4. Verify working directory ----------
if (-not (Test-Path $WorkingDir)) {
    Write-Host "ERROR: рабочая папка '$WorkingDir' не найдена." -ForegroundColor Red
    Write-Host "       Поправьте путь в начале скрипта и попробуйте снова." -ForegroundColor Yellow
    exit 1
}

# ---------- 5. Remove existing task if present ----------
$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Задача '$TaskName' уже существует — удаляю старую..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# ---------- 6. Build trigger: every 60 minutes, effectively indefinitely ----------
# StartInterval = 01:00:00 (one hour). RepetitionDuration set to 10 years
# (~"indefinite" — Task Scheduler doesn't accept TimeSpan.MaxValue directly).
$trigger = New-ScheduledTaskTrigger `
    -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Hours 1) `
    -RepetitionDuration (New-TimeSpan -Days 3650)

# ---------- 7. Build action ----------
$action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument $Arguments `
    -WorkingDirectory $WorkingDir

# ---------- 8. Build settings ----------
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew

# ---------- 9. Build principal (run as current user, highest privileges) ----------
$taskPrincipal = New-ScheduledTaskPrincipal `
    -UserId ("$env:USERDOMAIN\$env:USERNAME") `
    -LogonType Interactive `
    -RunLevel Highest

# ---------- 10. Register the task ----------
Register-ScheduledTask `
    -TaskName    $TaskName `
    -Trigger     $trigger `
    -Action      $action `
    -Settings    $settings `
    -Principal   $taskPrincipal `
    -Description $Description | Out-Null

# ---------- 11. Success message ----------
$check = [char]::ConvertFromUtf32(0x2705)  # ✅ — codepoint-safe against ANSI hosts
Write-Host ""
Write-Host "$check BK-PriceGuard добавлен в Планировщик заданий. Бот будет запускаться автоматически. Проверь логи через 1 час!" -ForegroundColor Green
Write-Host ""

Write-Host "Полезные команды для проверки:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Start-ScheduledTask -TaskName '$TaskName'       # запустить вручную сейчас"
Write-Host "  Get-ScheduledTaskInfo -TaskName '$TaskName'    # код выхода последнего запуска"
Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false  # удалить задачу"
Write-Host ""
Write-Host "Логи: $WorkingDir\data\price_monitor.log" -ForegroundColor DarkGray
