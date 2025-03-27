#!/bin/bash

# Exit on error
set -e

echo "Uninstalling Reminder App..."

# Stop and disable the systemd service
echo "Stopping and disabling systemd service..."
systemctl --user stop reminder-app.service 2>/dev/null || true
systemctl --user disable reminder-app.service 2>/dev/null || true
systemctl --user daemon-reload

# Remove systemd service file
echo "Removing systemd service file..."
rm -f ~/.config/systemd/user/reminder-app.service

# Remove the main executable
echo "Removing application executable..."
sudo rm -f /usr/local/bin/reminder-app

# Remove desktop entry
echo "Removing desktop entry..."
sudo rm -f /usr/share/applications/reminder-app.desktop

# Remove app icon
echo "Removing app icon..."
rm -f ~/.local/share/icons/hicolor/scalable/apps/reminder-app.svg

# Update icon cache
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor 2>/dev/null || true

# Ask if user wants to remove configuration and reminders
read -p "Do you want to remove all reminders and configuration data? (y/n): " remove_config
if [ "$remove_config" = "y" ] || [ "$remove_config" = "Y" ]; then
    echo "Removing configuration directory and reminders..."
    rm -rf ~/.config/reminder-app
    echo "All reminders and configuration data have been removed."
else
    echo "Configuration directory and reminders have been kept."
    echo "You can find them at: ~/.config/reminder-app"
fi

echo "Uninstallation complete! Reminder App has been removed from your system."