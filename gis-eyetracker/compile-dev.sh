v=8
pyinstaller gis-eye-tracker-mipt-dev.spec
cp *.kv dist/gis-eyetracker-mipt-dev/
cp *.dll dist/gis-eyetracker-mipt-dev/
cp *.json dist/gis-eyetracker-mipt-dev/
cp -r settings dist/gis-eyetracker-mipt-dev/settings
cp -r assets/ dist/gis-eyetracker-mipt-dev/assets
cp -r poppler-0.68.0/ dist/gis-eyetracker-mipt-dev/poppler-0.68.0

mv dist/gis-eyetracker-mipt-dev dist/gis-eyetracker-mipt.v1.0.${v}-dev
powershell "Compress-Archive dist/gis-eyetracker-mipt.v1.0.${v}-dev dist/gis-eyetracker-mipt.v1.0.${v}-dev.zip"