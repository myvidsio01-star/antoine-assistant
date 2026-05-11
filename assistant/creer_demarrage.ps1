$WshShell = New-Object -ComObject WScript.Shell
$startupPath = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Antoine.lnk"
$Shortcut = $WshShell.CreateShortcut($startupPath)
$Shortcut.TargetPath = "C:\Users\Utilisateur\jarvis-site\assistant\lancer_antoine.pyw"
$Shortcut.WorkingDirectory = "C:\Users\Utilisateur\jarvis-site\assistant"
$Shortcut.Description = "A.N.T.O.I.N.E - Assistant Vocal"
$Shortcut.Save()
Write-Host "Raccourci cree : $startupPath"
