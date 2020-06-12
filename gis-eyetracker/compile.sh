pyinstaller gis-track-generator-mipt.spec
cp *.kv dist/gis-generator-mipt/
cp *.dll dist/gis-generator-mipt/
cp *.json dist/gis-generator-mipt/
cp -r assets/ dist/gis-generator-mipt/assets
cp -r poppler-0.68.0/ dist/gis-generator-mipt/poppler-0.68.0