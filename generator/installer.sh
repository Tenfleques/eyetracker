# python -m PyInstaller -y --noconfirm --icon assets/icon.ico --name gis-track-generator-mipt gen_main.py
python -m PyInstaller -y --noconfirm --icon assets/icon.ico --name gis-track-generator-mipt gis-track-generator-mipt.spec
cp -r fonts dist/gis-track-generator-mipt/
cp *.kv dist/gis-track-generator-mipt/
