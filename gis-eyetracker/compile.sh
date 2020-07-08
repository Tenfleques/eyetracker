source ../version.txt
dev=""
name="gis-eyetracker-mipt${dev}"
root_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo "compiling version ${name}.v${major}.${major}.${patch}" 

pyinstaller ${name}.spec

echo "copying support files..."
cp *.kv dist/${name}/
cp *.dll dist/${name}/
cp *.json dist/${name}/
rm -rf dist/${name}/client_secrets.json 
cp -r settings dist/${name}/settings
cp -r assets/ dist/${name}/assets
cp -r poppler-0.68.0/ dist/${name}/poppler-0.68.0

echo "{\"main\": { \"name\": \"${name}\", \"version\" :  [${major}, ${major}, ${patch}]}}" > dist/${name}/assets/version.json

mkdir dist/${dev}v${major}.${minor}.${patch}

mv dist/${name}/* dist/${dev}v${major}.${minor}.${patch}/
mv dist/${dev}v${major}.${minor}.${patch} dist/${name}/${name}.v${major}.${minor}.${patch}


# cmd='$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut("dist\\'${name}'\\GIS Eyetracker MIPT.lnk"); $Shortcut.TargetPath = ".\\dist\\'${name}'\\'${name}'.v'${major}'.'${minor}'.'${patch}'\\'${name}'.exe"; $Shortcut.Save(); exit'

# powershell "${cmd}"

powershell "Compress-Archive dist/${name} dist/${name}.v${major}.${minor}.${patch}.zip;"


#echo "uploading to google drive"

#python ${root_path}/upload_to_gdrive.py --parent ${gdrive_parent} -p dist/${name}.v${major}.${minor}.${patch}${dev}.zip --result ${root_path}/../gis-eyetracker-releases/releases${dev}.changelog

#echo "${major}.${major}.${patch}" >> ../gis-eyetracker-releases/releases${dev}.changelog

# cd ../gis-eyetracker-releases/ && git add -A && git commit -m "uploaded new dev" && git push origin

