#!/bin/bash

# Exit on error
set -e

echo "Installing Reminder App..."

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-notify-0.7

# Create the app directory
INSTALL_DIR="/usr/local/bin"

# Copy the main script and window module
echo "Installing application..."
sudo cp reminder_app.py "$INSTALL_DIR/reminder-app"
sudo chmod +x "$INSTALL_DIR/reminder-app"

# Create app icon
echo "Creating app icon..."
mkdir -p ~/.local/share/icons/hicolor/scalable/apps/
# Either copy a custom icon or create a symbolic link to an existing one
if [ -f "reminder-app.svg" ]; then
    cp reminder-app.svg ~/.local/share/icons/hicolor/scalable/apps/
else
    ln -sf /usr/share/icons/hicolor/scalable/apps/gnome-clocks.svg ~/.local/share/icons/hicolor/scalable/apps/reminder-app.svg
fi

# Update icon cache
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor

# Install desktop entry
echo "Installing desktop entry..."
sudo cp reminder-app.desktop /usr/share/applications/

# Install systemd service
echo "Installing systemd service..."
mkdir -p ~/.config/systemd/user/
cp reminder-app.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable reminder-app.service
systemctl --user start reminder-app.service

echo "Installation complete! You can now find Reminder App in your applications menu."
echo "The reminder service has been installed and started."