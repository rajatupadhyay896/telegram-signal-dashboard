#!/bin/bash

cd /Users/user/Desktop/telegram_scraper

export DB_URL="postgresql://neondb_owner:npg_1DWscdB9Pjwu@ep-floral-smoke-ann9y638-pooler.c-6.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

python3 scraper.py >> log.txt 2>&1