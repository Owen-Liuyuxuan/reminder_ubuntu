#!/usr/bin/env python3

import gi
import os
import json
import datetime
import time
import threading
import argparse
import sys
from pathlib import Path

gi.require_version('Gtk', '3.0')
gi.require_version('Notify', '0.7')

from gi.repository import Gtk, GLib, Gio, Notify
from apk_window import ReminderWindow

class ReminderApp(Gtk.Application):
    def __init__(self, background_mode=False):
        super().__init__(application_id="com.example.reminder",
                        flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        
        # Set background mode flag
        self.background_mode = background_mode
        
        # Initialize notification system
        Notify.init("Reminder App")
        
        # Path for storing reminders
        self.config_dir = os.path.join(str(Path.home()), ".config", "reminder-app")
        self.reminders_file = os.path.join(self.config_dir, "reminders.json")
        
        # Create config directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Load existing reminders
        self.reminders = self.load_reminders()
        
        # Start the reminder checker thread
        self.stop_thread = False
        self.reminder_thread = threading.Thread(target=self.check_reminders)
        self.reminder_thread.daemon = True
        self.reminder_thread.start()
        
        # Add command line option handler
        self.add_main_option(
            "background",
            ord("b"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Run in background mode",
            None
        )
        
        # Add command line option handler for showing UI
        self.add_main_option(
            "show-ui",
            ord("u"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            "Show the UI even when running in background mode",
            None
        )
    
    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        
        # Convert GVariantDict -> GVariant -> Python dictionary
        options = options.end().unpack()
        
        # Check for background mode
        if "background" in options:
            self.background_mode = True
        
        # Check for show-ui flag
        show_ui = "show-ui" in options
        
        self.activate()
        
        # If show-ui flag is set, show the window even in background mode
        if show_ui and self.background_mode:
            self.show_window()
        
        return 0
    
    def do_activate(self):
        # In background mode, don't show the window by default
        if self.background_mode:
            print("Running in background mode")
            # Keep the application running
            self.hold()
            return
            
        # Show the window
        self.show_window()
    
    def show_window(self):
        """Show the application window"""
        # Get the current window or create one if necessary
        window = self.get_active_window()
        if not window:
            window = ReminderWindow(application=self)
        window.present()
    
    def load_reminders(self):
        """Load reminders from the JSON file"""
        if os.path.exists(self.reminders_file):
            try:
                with open(self.reminders_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []
    
    def save_reminders(self):
        """Save reminders to the JSON file"""
        with open(self.reminders_file, 'w') as f:
            json.dump(self.reminders, f)
    
    def add_reminder(self, title, message, trigger_time):
        """Add a new reminder"""
        # Use a smaller integer for ID that fits within 32-bit range
        reminder = {
            'id': int(time.time()) % 2000000000,  # Ensure ID is within 32-bit integer range
            'title': title,
            'message': message,
            'trigger_time': trigger_time,
            'triggered': False
        }
        self.reminders.append(reminder)
        self.save_reminders()
    
    def remove_reminder(self, reminder_id):
        """Remove a reminder by ID"""
        self.reminders = [r for r in self.reminders if r['id'] != reminder_id]
        self.save_reminders()
    
    def cleanup_completed_reminders(self):
        """Remove all completed reminders"""
        initial_count = len(self.reminders)
        self.reminders = [r for r in self.reminders if not r['triggered']]
        self.save_reminders()
        
        # Return True if any reminders were removed
        return len(self.reminders) < initial_count
    
    def check_reminders(self):
        """Background thread to check for due reminders"""
        while not self.stop_thread:
            current_time = datetime.datetime.now().timestamp()
            
            for reminder in self.reminders:
                if not reminder['triggered'] and float(reminder['trigger_time']) <= current_time:
                    GLib.idle_add(self.trigger_notification, reminder)
                    reminder['triggered'] = True
                    GLib.idle_add(self.save_reminders)
            
            # Check every second
            time.sleep(1)
    
    def trigger_notification(self, reminder):
        """Display a system notification for the reminder"""
        notification = Notify.Notification.new(
            reminder['title'],
            reminder['message'],
            "dialog-information"
        )
        notification.set_urgency(Notify.Urgency.NORMAL)
        notification.show()
        
        return False  # Required for GLib.idle_add
    
    def do_shutdown(self):
        """Clean up when the application is shutting down"""
        self.stop_thread = True
        if self.reminder_thread.is_alive():
            self.reminder_thread.join(1)  # Wait up to 1 second for the thread to finish
        
        Notify.uninit()
        Gtk.Application.do_shutdown(self)


def main():
    # Parse command line arguments
    app = ReminderApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    main()