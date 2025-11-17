@echo off
echo Building Email Client...

pyinstaller --onefile ^
--add-data "features/email_reader/email_reader.py;features/email_reader" ^
--add-data "features/email_replier/email_replier.py;features/email_replier" ^
--add-data "features/auth/auth.py;features/auth" ^
--add-data "utils/config.py;utils" ^
--add-data "utils/helpers.py;utils" ^
--hidden-import=questionary ^
--hidden-import=prompt_toolkit ^
--hidden-import=rich ^
cli_app.py

echo Build completed! Check dist/cli_app.exe
pause