echo #!/usr/bin/env bash > build.sh
echo # exit on error >> build.sh
echo set -o errexit >> build.sh
echo. >> build.sh
echo pip install -r requirements.txt >> build.sh
echo. >> build.sh
echo python manage.py collectstatic --no-input >> build.sh
echo python manage.py migrate >> build.sh