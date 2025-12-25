#!/bin/bash

# --- תיקון קריטי: כניסה לתיקייה שבה הסקריפט נמצא ---
cd "$(dirname "$0")"

echo "Current directory: $(pwd)"

echo "--- Pulling latest code from GitHub ---"
git pull origin main

echo "--- Building and restarting containers ---"

# וידוא שהקובץ קיים לפני שמנסים להריץ
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ CRITICAL ERROR: docker-compose.yml not found in $(pwd)"
    exit 1
fi

# הרצת דוקר (עם תמיכה בגרסאות ישנות וחדשות)
if command -v docker-compose &> /dev/null
then
    docker-compose -f docker-compose.yml up -d --build
else
    docker compose -f docker-compose.yml up -d --build
fi

echo "--- Cleanup unused images ---"
docker image prune -f

echo "✅ Production updated successfully!"