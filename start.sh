#!/bin/bash
set -e

echo "Starting Promtail in the background..."
/usr/local/bin/promtail-linux-amd64 -config.file=/home/user/app/promtail-config.yaml -config.expand-env=true &

echo "Starting Gunicorn..."
exec gunicorn -b 0.0.0.0:7860 --timeout 300 --threads 4 app:app
