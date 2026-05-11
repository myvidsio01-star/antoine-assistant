$src = "C:\Users\Utilisateur\jarvis-site\assistant\dist\ANTOINE-V1.1"
$zip = "C:\Users\Utilisateur\jarvis-site\assistant\dist\ANTOINE-V1.1.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path "$src\*" -DestinationPath $zip
$taille = [math]::Round((Get-Item $zip).Length / 1MB)
Write-Host "ZIP cree : $taille Mo -> $zip"
