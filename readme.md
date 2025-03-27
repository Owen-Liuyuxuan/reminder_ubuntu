# <img src="./reminder-app.svg" height="48" style="vertical-align: middle;"> Reminder App

A GTK-based desktop reminder application for Linux that allows you to create and manage reminders with system notifications. The app can run in both interactive and background modes, making it perfect for desktop integration.


## Features

- Create reminders with custom titles and messages
- Two reminder scheduling options:
  - Time from now (minutes, hours, or days)
  - Specific date and time
- System notifications when reminders are due
- Background service mode for continuous operation
- Clean and intuitive GTK3 user interface
- Persistent storage of reminders
- Ability to manage (view/delete) existing reminders
- Clean up completed reminders
- Desktop integration with autostart capability

## Requirements

- Python 3.x
- GTK 3.0
- Python GObject bindings
- libnotify

On Ubuntu/Debian systems, install dependencies with:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-notify-0.7
```

## Installation

1. Clone this repository or download the files to your preferred location.

2. Make the Python scripts executable:
```bash
chmod +x reminder_app.py apk_window.py
```

3. Install the application system-wide:
```bash
sudo cp reminder_app.py /usr/local/bin/reminder-app
sudo cp apk_window.py /usr/local/lib/python3/dist-packages/
sudo cp reminder-app.desktop /usr/share/applications/
sudo cp reminder-app.service /etc/systemd/user/
```

4. Enable and start the background service:
```bash
systemctl --user enable reminder-app.service
systemctl --user start reminder-app.service
```

## Usage

### GUI Mode

Launch the app with the graphical interface in one of these ways:
- Click on the Reminder App icon in your applications menu
- Run from terminal: `reminder-app --show-ui`

### Background Mode

Run the app in background mode (no window):
```bash
reminder-app --background
```

### Creating Reminders

1. Enter a title and message for your reminder
2. Choose the reminder type:
   - "Time from now" - Set a reminder for X minutes/hours/days from now
   - "Specific date/time" - Choose a specific date and time for the reminder
3. Click "Add Reminder"

### Managing Reminders

- View all scheduled reminders in the main window
- Delete individual reminders using the "Delete Selected" button
- Remove all completed reminders with "Clean Up Completed"

## Configuration

The app stores its configuration and reminders in:
```
~/.config/reminder-app/reminders.json
```

## Autostart

The application is configured to start automatically with your desktop session through the desktop entry file.

## Command Line Options

- `--background` or `-b`: Run in background mode without showing the window
- `--show-ui` or `-u`: Show the UI window (can be used with background mode)

## Files Description

- `reminder_app.py`: Main application logic and background service
- `apk_window.py`: GTK window and UI implementation
- `reminder-app.service`: Systemd user service file for background operation
- `reminder-app.desktop`: Desktop entry file for application menu integration

## License

This project is open source and available under the MIT License.
