# VideoNote Windows 故障排查脚本
# 使用方法: 在PowerShell中运行 .\troubleshoot.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "VideoNote Windows 故障排查工具" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查Windows版本
Write-Host "1. 检查系统信息..." -ForegroundColor Yellow
$osInfo = Get-CimInstance Win32_OperatingSystem
Write-Host "   操作系统: $($osInfo.Caption)" -ForegroundColor Green
Write-Host "   版本: $($osInfo.Version)" -ForegroundColor Green
Write-Host "   架构: $($osInfo.OSArchitecture)" -ForegroundColor Green
Write-Host ""

# 2. 检查端口占用
Write-Host "2. 检查端口8118占用情况..." -ForegroundColor Yellow
$portCheck = netstat -ano | Select-String ":8118"
if ($portCheck) {
    Write-Host "   ⚠️ 警告: 端口8118已被占用!" -ForegroundColor Red
    Write-Host "   详情:" -ForegroundColor Red
    $portCheck | ForEach-Object { Write-Host "   $_" -ForegroundColor Red }
    Write-Host ""
    Write-Host "   解决方案:" -ForegroundColor Yellow
    Write-Host "   - 关闭占用端口的程序" -ForegroundColor White
    Write-Host "   - 或在应用中修改为其他端口" -ForegroundColor White
} else {
    Write-Host "   ✓ 端口8118未被占用" -ForegroundColor Green
}
Write-Host ""

# 3. 检查防火墙规则
Write-Host "3. 检查防火墙规则..." -ForegroundColor Yellow
try {
    $firewallRules = Get-NetFirewallRule -DisplayName "*VideoNote*" -ErrorAction SilentlyContinue
    if ($firewallRules) {
        Write-Host "   ✓ 找到VideoNote防火墙规则:" -ForegroundColor Green
        $firewallRules | ForEach-Object {
            Write-Host "   - $($_.DisplayName) [已$($_.Enabled ? '启用' : '禁用')]" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️ 未找到VideoNote防火墙规则" -ForegroundColor Yellow
        Write-Host "   首次运行时,Windows会提示添加防火墙规则,请点击'允许访问'" -ForegroundColor White
    }
} catch {
    Write-Host "   ⚠️ 无法检查防火墙规则(需要管理员权限)" -ForegroundColor Yellow
}
Write-Host ""

# 4. 检查应用安装
Write-Host "4. 检查应用安装..." -ForegroundColor Yellow
$appPath = "$env:LOCALAPPDATA\VideoNote"
if (Test-Path $appPath) {
    Write-Host "   ✓ 应用已安装: $appPath" -ForegroundColor Green
    
    # 检查sidecar
    $sidecarPath = Join-Path $appPath "vn-sidecar.exe"
    if (Test-Path $sidecarPath) {
        Write-Host "   ✓ Python Sidecar存在" -ForegroundColor Green
        $sidecarSize = (Get-Item $sidecarPath).Length / 1MB
        Write-Host "   文件大小: $([math]::Round($sidecarSize, 2)) MB" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Python Sidecar不存在!" -ForegroundColor Red
        Write-Host "   请重新安装应用" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️ 应用未安装在默认位置" -ForegroundColor Yellow
}
Write-Host ""

# 5. 检查日志
Write-Host "5. 检查应用日志..." -ForegroundColor Yellow
$logPath = "$env:APPDATA\VideoNote\logs"
if (Test-Path $logPath) {
    Write-Host "   ✓ 日志目录存在: $logPath" -ForegroundColor Green
    $logFiles = Get-ChildItem $logPath -Filter "*.log" | Sort-Object LastWriteTime -Descending
    if ($logFiles) {
        Write-Host "   最新的3个日志文件:" -ForegroundColor Green
        $logFiles | Select-Object -First 3 | ForEach-Object {
            Write-Host "   - $($_.Name) ($($_.LastWriteTime))" -ForegroundColor Green
        }
        
        # 检查最新日志中的错误
        Write-Host ""
        Write-Host "   检查最新日志中的错误..." -ForegroundColor Yellow
        $latestLog = $logFiles | Select-Object -First 1
        $errorLines = Select-String -Path $latestLog.FullName -Pattern "ERROR|Exception|Failed" | Select-Object -Last 5
        if ($errorLines) {
            Write-Host "   ⚠️ 发现错误信息(最后5条):" -ForegroundColor Red
            $errorLines | ForEach-Object { Write-Host "   $_" -ForegroundColor Red }
        } else {
            Write-Host "   ✓ 未发现明显错误" -ForegroundColor Green
        }
    } else {
        Write-Host "   ⚠️ 未找到日志文件" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠️ 日志目录不存在(应用可能未运行过)" -ForegroundColor Yellow
}
Write-Host ""

# 6. 测试网络连接
Write-Host "6. 测试本地网络连接..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8118/health" -TimeoutSec 3 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✓ Python Sidecar正在运行并响应!" -ForegroundColor Green
        Write-Host "   响应: $($response.Content)" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️ 无法连接到Python Sidecar" -ForegroundColor Yellow
    Write-Host "   这是正常的(如果应用当前未运行)" -ForegroundColor White
}
Write-Host ""

# 7. 检查杀毒软件(常见的)
Write-Host "7. 检查安全软件..." -ForegroundColor Yellow
$antivirusProducts = Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct -ErrorAction SilentlyContinue
if ($antivirusProducts) {
    Write-Host "   检测到的安全软件:" -ForegroundColor Green
    $antivirusProducts | ForEach-Object {
        Write-Host "   - $($_.displayName)" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "   提示: 如果应用无法启动,可能被安全软件阻止" -ForegroundColor Yellow
    Write-Host "   请将VideoNote添加到安全软件的白名单" -ForegroundColor White
} else {
    Write-Host "   ✓ 未检测到第三方安全软件(仅Windows Defender)" -ForegroundColor Green
}
Write-Host ""

# 总结
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "排查完成!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果问题仍未解决,请:" -ForegroundColor Yellow
Write-Host "1. 查看详细日志: $logPath" -ForegroundColor White
Write-Host "2. 阅读部署指南: WINDOWS_DEPLOYMENT.md" -ForegroundColor White
Write-Host "3. 提交Issue并附上本脚本的输出结果" -ForegroundColor White
Write-Host ""

# 询问是否打开日志目录
if (Test-Path $logPath) {
    $openLogs = Read-Host "是否打开日志目录? (Y/N)"
    if ($openLogs -eq "Y" -or $openLogs -eq "y") {
        explorer $logPath
    }
}


