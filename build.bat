pyinstaller --onefile sparkplug_vault.py
pyinstaller --onefile sparkplug_citrix.py

xcopy /Y res dist\res\
xcopy /Y .env.local dist\
xcopy /Y config.json dist\
