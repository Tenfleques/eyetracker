pyinstaller gis-eyetracker-mipt-dev.spec
cp *.kv dist/gis-eyetracker-mipt/
cp *.dll dist/gis-eyetracker-mipt/
cp *.json dist/gis-eyetracker-mipt/
cp -r settings dist/gis-eyetracker-mipt/settings
cp -r assets/ dist/gis-eyetracker-mipt/assets
cp -r poppler-0.68.0/ dist/gis-eyetracker-mipt/poppler-0.68.0
cp -r bin/ dist/gis-eyetracker-mipt/bin
mv dist/gis-eyetracker-mipt dist/gis-eyetracker-mipt.v1.0.7-dev
powershell "Compress-Archive dist/gis-eyetracker-mipt.v1.0.7-dev dist/gis-eyetracker-mipt.v1.0.7-dev.zip"