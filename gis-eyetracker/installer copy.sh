# python -m PyInstaller -y --noconfirm --icon assets/icon.ico --name gis-eye-tracker-mipt main.py
python -m PyInstaller -y --noconfirm --icon assets/icon.ico --name gis-eye-tracker-mipt gis-eye-tracker-mipt.spec
cp *.kv dist/gis-eye-tracker-mipt/
cp *.json dist/gis-eye-tracker-mipt/
cp *.dll dist/gis-eye-tracker-mipt/
