v=8
pyinstaller gis-eyetracker-mipt.spec
cp *.kv dist/gis-eyetracker-mipt/
cp *.dll dist/gis-eyetracker-mipt/
cp *.json dist/gis-eyetracker-mipt/
cp -r settings dist/gis-eyetracker-mipt/settings
cp -r assets/ dist/gis-eyetracker-mipt/assets
cp -r poppler-0.68.0/ dist/gis-eyetracker-mipt/poppler-0.68.0

mv dist/gis-eyetracker-mipt dist/gis-eyetracker-mipt.v1.0.${v}
powershell "Compress-Archive dist/gis-eyetracker-mipt.v1.0.${v} dist/gis-eyetracker-mipt.v1.0.${v}.zip"