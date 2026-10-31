#!/usr/bin/env bash
set -e

# Automatically get the absolute path where the user cloned the repo
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$HOME/.local/share/applications/pdforge.desktop"

# Ensure the launcher is executable
chmod +x "$APP_DIR/run_pdforge.sh"

# Create the user's desktop entry with dynamic paths
mkdir -p "$HOME/.local/share/applications"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=PDForge
Comment=Local PDF Studio
Exec="$APP_DIR/run_pdforge.sh" %F
Icon=$APP_DIR/assets/brand/pdforge-logo.svg
Terminal=false
Categories=Office;Utility;
StartupNotify=true
EOF

# Update the Linux desktop database so it shows up immediately
chmod +x "$DESKTOP_FILE"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true

echo "✓ PDForge installed successfully! You can now launch it from your Applications menu."