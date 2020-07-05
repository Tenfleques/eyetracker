source ../version.txt
dev="-dev"
name="gis-eyetracker-mipt${dev}"
echo "compiling version ${name}.v${major}.${major}.${patch}"

pyinstaller ${name}.spec

echo "copying support files..."
cp *.kv dist/${name}/
cp *.dll dist/${name}/
cp *.json dist/${name}/
cp -r settings dist/${name}/settings
cp -r assets/ dist/${name}/assets
cp -r poppler-0.68.0/ dist/${name}/poppler-0.68.0

echo "{\"main\": { \"name\": \"${name}\", \"version\" :  [${major}, ${major}, ${patch}]}}" > dist/${name}/assets/version.json

mkdir dist/v${major}.${minor}.${patch}

mv dist/${name}/* dist/v${major}.${minor}.${patch}/
mv dist/v${major}.${minor}.${patch} dist/${name}/${name}.v${major}.${minor}.${patch}


# cmd='$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut("dist\\'${name}'\\GIS Eyetracker MIPT.lnk"); $Shortcut.TargetPath = ".\\dist\\'${name}'\\'${name}'.v'${major}'.'${minor}'.'${patch}'\\'${name}'.exe"; $Shortcut.Save(); exit'

# powershell "${cmd}"

# powershell "Compress-Archive dist/${name} dist/${name}.v${major}.${minor}.${patch}.zip"


if ! command -v gdrive-windows-x64.exe &> /dev/null
then
    echo "gdrive-windows-x64.exe not found, you will upload manually"
    exit
fi

upload_result=$(gdrive-windows-x64.exe upload --parent ${gdrive_parent} dist/${name}.v${major}.${minor}.${patch}${dev}.zip)

echo "${upload_result}${dev}.v${major}.${major}.${patch}" >> ../releases-heroku/releases${dev}.changelog

cd ../releases-heroku/
git add -A
git commit -m "uploaded new dev"
git push