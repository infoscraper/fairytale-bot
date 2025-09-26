#!/bin/bash
set -e

echo "🚀 Starting Fairytale Bot..."

# Check if init_db.py exists
if [ -f "init_db.py" ]; then
    echo "📦 Running database initialization..."
    python init_db.py
    echo "✅ Database initialization completed!"
else
    echo "⚠️  init_db.py not found, skipping database initialization"
fi

echo "🤖 Starting bot..."
python -m src.main
