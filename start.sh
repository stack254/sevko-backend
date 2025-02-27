#!/usr/bin/env bash
set -e

# Start Gunicorn
gunicorn markdcommerce.wsgi:application --bind 0.0.0.0:$PORT