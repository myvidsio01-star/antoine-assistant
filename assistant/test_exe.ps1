Start-Process "C:\Users\Utilisateur\jarvis-site\assistant\dist\ANTOINE-V1.1\ANTOINE.exe"
Start-Sleep -Seconds 6
$p = Get-Process -Name "ANTOINE" -ErrorAction SilentlyContinue
if ($p) {
    $mem = [math]::Round($p.WorkingSet64 / 1MB)
    Write-Host "OK - ANTOINE tourne (PID $($p.Id)), memoire : $mem Mo"
} else {
    Write-Host "ECHEC - ANTOINE ne tourne plus, il a plante au demarrage"
}
