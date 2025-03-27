#!/usr/bin/env python3

import os
import json
import datetime
import time
import threading
import sys
import argparse
from pathlib import Path

# Parse command line arguments early to check for background mode
parser = argparse.ArgumentParser(description="Reminder Application")
parser.add_argument("--background", "-b", action="store_true", help="Run in background mode")
parser.add_argument("--show-ui", "-u", action="store_true", help="Show UI (ignores background mode)")
args, remaining_args = parser.parse_known_args()

# Only import GUI libraries if not in background mode or show-ui is requested
BACKGROUND_MODE = args.background and not args.show_ui
GUI_AVAILABLE = not BACKGROUND_MODE

# Import notification system - always needed
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify

# Only import GTK if GUI is needed
if GUI_AVAILABLE:
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib, Gio

# For background mode, we need GLib for the main loop
if BACKGROUND_MODE:
    from gi.repository import GLib, Gio

# ReminderWindow class (GUI mode only)
if GUI_AVAILABLE:
    class ReminderWindow(Gtk.ApplicationWindow):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            
            self.app = kwargs['application']
            
            self.set_title("Reminder App")
            self.set_default_size(500, 400)
            self.set_border_width(10)
            
            # Main container
            main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            self.add(main_box)
            
            # Reminder creation area
            creation_frame = Gtk.Frame(label="Create Reminder")
            main_box.pack_start(creation_frame, False, True, 0)
            
            creation_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            creation_box.set_border_width(10)
            creation_frame.add(creation_box)
            
            # Title entry
            title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            title_label = Gtk.Label(label="Title:")
            title_label.set_width_chars(10)
            self.title_entry = Gtk.Entry()
            title_box.pack_start(title_label, False, True, 0)
            title_box.pack_start(self.title_entry, True, True, 0)
            creation_box.pack_start(title_box, False, True, 0)
            
            # Message entry
            message_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            message_label = Gtk.Label(label="Message:")
            message_label.set_width_chars(10)
            self.message_entry = Gtk.Entry()
            message_box.pack_start(message_label, False, True, 0)
            message_box.pack_start(self.message_entry, True, True, 0)
            creation_box.pack_start(message_box, False, True, 0)
            
            # Reminder type selection
            type_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            type_label = Gtk.Label(label="Type:")
            type_label.set_width_chars(10)
            
            self.type_combo = Gtk.ComboBoxText()
            self.type_combo.append_text("Time from now")
            self.type_combo.append_text("Specific date/time")
            self.type_combo.set_active(0)
            self.type_combo.connect("changed", self.on_type_changed)
            
            type_box.pack_start(type_label, False, True, 0)
            type_box.pack_start(self.type_combo, True, True, 0)
            creation_box.pack_start(type_box, False, True, 0)
            
            # Stack for different reminder type inputs
            self.time_stack = Gtk.Stack()
            self.time_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
            self.time_stack.set_transition_duration(200)
            
            # Time from now options
            time_from_now_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            
            adjustment = Gtk.Adjustment(
                value=5,
                lower=1,
                upper=999,
                step_increment=1,
                page_increment=10,
                page_size=0
            )
            self.time_value_entry = Gtk.SpinButton()
            self.time_value_entry.set_adjustment(adjustment)
            
            self.time_unit_combo = Gtk.ComboBoxText()
            self.time_unit_combo.append_text("minutes")
            self.time_unit_combo.append_text("hours")
            self.time_unit_combo.append_text("days")
            self.time_unit_combo.set_active(0)
            
            time_from_now_box.pack_start(Gtk.Label(label="Remind in:"), False, True, 0)
            time_from_now_box.pack_start(self.time_value_entry, True, True, 0)
            time_from_now_box.pack_start(self.time_unit_combo, True, True, 0)
            
            # Specific date/time options
            date_time_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            
            date_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            date_box.pack_start(Gtk.Label(label="Date:"), False, True, 0)
            self.calendar = Gtk.Calendar()
            date_box.pack_start(self.calendar, True, True, 0)
            
            time_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            time_box.pack_start(Gtk.Label(label="Time:"), False, True, 0)
            
            hour_adjustment = Gtk.Adjustment(
                value=12,
                lower=0,
                upper=23,
                step_increment=1,
                page_increment=5,
                page_size=0
            )
            self.hour_spin = Gtk.SpinButton()
            self.hour_spin.set_adjustment(hour_adjustment)
            self.hour_spin.set_numeric(True)
            self.hour_spin.set_width_chars(2)
            
            minute_adjustment = Gtk.Adjustment(
                value=0,
                lower=0,
                upper=59,
                step_increment=1,
                page_increment=5,
                page_size=0
            )
            self.minute_spin = Gtk.SpinButton()
            self.minute_spin.set_adjustment(minute_adjustment)
            self.minute_spin.set_numeric(True)
            self.minute_spin.set_width_chars(2)
            
            time_box.pack_start(self.hour_spin, False, True, 0)
            time_box.pack_start(Gtk.Label(label=":"), False, True, 0)
            time_box.pack_start(self.minute_spin, False, True, 0)
            
            date_time_box.pack_start(date_box, False, True, 0)
            date_time_box.pack_start(time_box, False, True, 0)
            
            # Add pages to stack
            self.time_stack.add_titled(time_from_now_box, "time_from_now", "Time from now")
            self.time_stack.add_titled(date_time_box, "date_time", "Specific date/time")
            
            creation_box.pack_start(self.time_stack, False, True, 0)
            
            # Add reminder button
            add_button = Gtk.Button(label="Add Reminder")
            add_button.connect("clicked", self.on_add_clicked)
            creation_box.pack_start(add_button, False, True, 0)
            
            # Reminders list
            list_frame = Gtk.Frame(label="Scheduled Reminders")
            main_box.pack_start(list_frame, True, True, 0)
            
            list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
            list_box.set_border_width(10)
            list_frame.add(list_box)
            
            # Create the list store and view
            self.reminder_store = Gtk.ListStore(str, str, str, str, bool)  # id as string, title, message, time, triggered
            self.reminder_view = Gtk.TreeView(model=self.reminder_store)
            
            # Add columns
            renderer_text = Gtk.CellRendererText()
            
            column_title = Gtk.TreeViewColumn("Title", renderer_text, text=1)
            column_title.set_expand(True)
            self.reminder_view.append_column(column_title)
            
            column_message = Gtk.TreeViewColumn("Message", renderer_text, text=2)
            column_message.set_expand(True)
            self.reminder_view.append_column(column_message)
            
            column_time = Gtk.TreeViewColumn("Time", renderer_text, text=3)
            self.reminder_view.append_column(column_time)
            
            renderer_toggle = Gtk.CellRendererToggle()
            renderer_toggle.set_activatable(False)
            column_triggered = Gtk.TreeViewColumn("Completed", renderer_toggle, active=4)
            self.reminder_view.append_column(column_triggered)
            
            # Scrolled window for the list
            scrolled_window = Gtk.ScrolledWindow()
            scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scrolled_window.add(self.reminder_view)
            list_box.pack_start(scrolled_window, True, True, 0)
            
            # Button box for actions
            button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            list_box.pack_start(button_box, False, True, 0)
            
            # Delete button
            delete_button = Gtk.Button(label="Delete Selected")
            delete_button.connect("clicked", self.on_delete_clicked)
            button_box.pack_start(delete_button, True, True, 0)
            
            # Clean up completed button
            cleanup_button = Gtk.Button(label="Clean Up Completed")
            cleanup_button.connect("clicked", self.on_cleanup_clicked)
            button_box.pack_start(cleanup_button, True, True, 0)
            
            # Refresh reminders list
            self.refresh_reminders_list()
            
            # Set up a timer to refresh the list periodically
            GLib.timeout_add_seconds(5, self.refresh_reminders_list)
            
            # Show all widgets
            self.show_all()
        
        def on_type_changed(self, combo):
            active = combo.get_active()
            if active == 0:
                self.time_stack.set_visible_child_name("time_from_now")
            else:
                self.time_stack.set_visible_child_name("date_time")
        
        def on_add_clicked(self, button):
            title = self.title_entry.get_text()
            message = self.message_entry.get_text()
            
            if not title:
                self.show_error_dialog("Title cannot be empty")
                return
            
            # Calculate trigger time based on type
            now = datetime.datetime.now()
            
            if self.type_combo.get_active() == 0:  # Time from now
                value = self.time_value_entry.get_value_as_int()
                unit = self.time_unit_combo.get_active_text()
                
                if unit == "minutes":
                    delta = datetime.timedelta(minutes=value)
                elif unit == "hours":
                    delta = datetime.timedelta(hours=value)
                else:  # days
                    delta = datetime.timedelta(days=value)
                
                trigger_time = now + delta
                display_time = f"In {value} {unit}"
            
            else:  # Specific date/time
                year, month, day = self.calendar.get_date()
                # Month is 0-based in GTK Calendar
                month += 1
                hour = self.hour_spin.get_value_as_int()
                minute = self.minute_spin.get_value_as_int()
                
                trigger_time = datetime.datetime(year, month, day, hour, minute)
                
                # Check if the time is in the past
                if trigger_time < now:
                    self.show_error_dialog("Cannot set reminders in the past")
                    return
                
                display_time = trigger_time.strftime("%Y-%m-%d %H:%M")
            
            # Add the reminder
            self.app.add_reminder(title, message, trigger_time.timestamp())
            
            # Clear inputs
            self.title_entry.set_text("")
            self.message_entry.set_text("")
            
            # Refresh the list
            self.refresh_reminders_list()
        
        def on_delete_clicked(self, button):
            selection = self.reminder_view.get_selection()
            model, iter_ = selection.get_selected()
            
            if iter_ is not None:
                reminder_id = int(model[iter_][0])
                self.app.remove_reminder(reminder_id)
                self.refresh_reminders_list()
        
        def on_cleanup_clicked(self, button):
            """Remove all completed reminders"""
            if self.app.cleanup_completed_reminders():
                # Show a confirmation dialog
                dialog = Gtk.MessageDialog(
                    transient_for=self,
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Cleanup Complete"
                )
                dialog.format_secondary_text("All completed reminders have been removed.")
                dialog.run()
                dialog.destroy()
            
            # Refresh the list
            self.refresh_reminders_list()
        
        def refresh_reminders_list(self):
            """Refresh the reminders list"""
            # Clear the list
            self.reminder_store.clear()
            
            # Sort reminders by trigger time (closest first)
            sorted_reminders = sorted(
                self.app.reminders,
                key=lambda r: float('inf') if r['triggered'] else float(r['trigger_time'])
            )
            
            # Add reminders to the list
            for reminder in sorted_reminders:
                # Format the time for display
                if reminder['triggered']:
                    time_str = "Completed"
                else:
                    trigger_time = datetime.datetime.fromtimestamp(float(reminder['trigger_time']))
                    time_str = trigger_time.strftime("%Y-%m-%d %H:%M")
                
                # Convert the ID to string to avoid integer overflow
                self.reminder_store.append([
                    str(reminder['id']),  # Store ID as string
                    reminder['title'],
                    reminder['message'],
                    time_str,
                    reminder['triggered']
                ])
            
            return True  # Return True to keep the timer running
        
        def show_error_dialog(self, message):
            """Show an error dialog with the given message"""
            dialog = Gtk.MessageDialog(
                transient_for=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Error"
            )
            dialog.format_secondary_text(message)
            dialog.run()
            dialog.destroy()

# Base application class that handles reminders in both GUI and background modes
class ReminderAppBase:
    def __init__(self):
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
                    if GUI_AVAILABLE:
                        GLib.idle_add(self.trigger_notification, reminder)
                    else:
                        # Direct notification without idle_add
                        self.trigger_notification(reminder)
                    reminder['triggered'] = True
                    if GUI_AVAILABLE:
                        GLib.idle_add(self.save_reminders)
                    else:
                        self.save_reminders()
            
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
        
        if GUI_AVAILABLE:
            return False  # Required for GLib.idle_add
    
    def shutdown(self):
        """Clean up when the application is shutting down"""
        self.stop_thread = True
        if self.reminder_thread.is_alive():
            self.reminder_thread.join(1)  # Wait up to 1 second for the thread to finish
        
        Notify.uninit()

# GUI application (when not in background mode)
if GUI_AVAILABLE:
    class ReminderApp(Gtk.Application, ReminderAppBase):
        def __init__(self):
            Gtk.Application.__init__(
                self,
                application_id="com.example.reminder",
                flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE
            )
            ReminderAppBase.__init__(self)
            
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
            
            self.activate()
            return 0
        
        def do_activate(self):
            # Show the window
            self.show_window()
        
        def show_window(self):
            """Show the application window"""
            # Get the current window or create one if necessary
            window = self.get_active_window()
            if not window:
                window = ReminderWindow(application=self)
            window.present()
        
        def do_shutdown(self):
            """Clean up when the application is shutting down"""
            self.shutdown()
            Gtk.Application.do_shutdown(self)

# Background mode application (no GUI)
else:
    class BackgroundReminderApp(ReminderAppBase):
        def __init__(self):
            super().__init__()
            self.main_loop = GLib.MainLoop()
            print("Running in background mode (no GUI)")
        
        def run(self):
            """Run the application in background mode"""
            try:
                self.main_loop.run()
            except KeyboardInterrupt:
                print("Shutting down background service")
            finally:
                self.shutdown()

def main():
    if GUI_AVAILABLE:
        app = ReminderApp()
        return app.run(sys.argv)
    else:
        app = BackgroundReminderApp()
        app.run()
        return 0

if __name__ == "__main__":
    main()