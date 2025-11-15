#!/bin/bash
# Script to fix file permissions for the project
# This can be run manually or called from other scripts

PROJECT_DIR="/etc/dokploy/applications/fairytalebot-bot-zpwqwc/code"
USER="danil"

echo "🔧 Fixing permissions for $PROJECT_DIR..."

# Fix ownership
sudo chown -R $USER:$USER "$PROJECT_DIR"

# Fix permissions: user can read/write/execute, group and others can read/execute
sudo chmod -R u+rwX,go+rX "$PROJECT_DIR"

# Ensure .git directory is writable
if [ -d "$PROJECT_DIR/.git" ]; then
    sudo chown -R $USER:$USER "$PROJECT_DIR/.git"
    sudo chmod -R u+rwX "$PROJECT_DIR/.git"
    echo "✅ Git directory permissions fixed"
fi

echo "✅ Permissions fixed successfully!"
echo ""
echo "Verification:"
ls -ld "$PROJECT_DIR"
echo ""
echo "You can now edit files in VS Code without permission errors."

