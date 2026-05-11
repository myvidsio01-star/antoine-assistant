$dest = "C:\Users\Utilisateur\jarvis-site\assistant\dist\ANTOINE-V1.1"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Recurse -Force "C:\Users\Utilisateur\jarvis-site\assistant\dist\ANTOINE\*" $dest
Copy-Item "C:\Users\Utilisateur\jarvis-site\assistant\.env.example" "$dest\.env.example"
Write-Host "Dossier prêt : $dest"
Get-ChildItem $dest | Select-Object Name, @{N='Taille';E={if($_.PSIsContainer){'[dossier]'} else {"$([math]::Round($_.Length/1KB)) Ko"}}}
