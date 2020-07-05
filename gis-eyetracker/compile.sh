source ../version.txt
dev=""
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


echo "uploading to google drive"
python upload_to_drive --parent ${gdrive_parent} -p dist/${name}.v${major}.${minor}.${patch}${dev}.zip >> ../releases-heroku/releases${dev}.changelog

echo "${major}.${major}.${patch}" >> ../releases-heroku/releases${dev}.changelog

cd ../releases-heroku/
git add -A
git commit -m "uploaded new dev"
git push

