#!/usr/bin/env python
import os
import json
import gi
import threading
import sys
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk,GLib

##############################
# Class to read data from js #
##############################
class StdioReader(threading.Thread):
    def __init__(self, callback):
        threading.Thread.__init__(self)
        self.callback = callback
        self._stop_event = threading.Event()

    def run(self):
        while not self._stop_event.is_set():
            line = os.read(0,1024)
            if line:
                try:
                    data =json.loads(line.decode('utf-8'))
                    GLib.idle_add(self.callback, data)
                except Exception:
                    pass
    def stop(self):
        self._stop_event.set()

class PopupDialog(Gtk.Dialog):
    def __init__(self, parent, message):
        Gtk.Dialog.__init__(self, "Popup Dialog", parent, 0,
            (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        self.set_default_size(150, 100)

        label = Gtk.Label(message)
        box = self.get_content_area()
        box.add(label)
        self.show_all()

class ChatRoomWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Chat Room")

        self.set_border_width(10)

        self.chat_room_label = Gtk.Label(label="Enter Chat Room:")
        self.chat_room_entry = Gtk.Entry()
        self.chat_room_entry.set_placeholder_text("Enter room name")

        self.enter_button = Gtk.Button(label="Enter")
        self.create_channel = Gtk.Button(label="Create Channel")

        self.enter_button.connect("clicked", self.on_enter_button_clicked)
        self.create_channel.connect("clicked",self.on_create_channel_button_clicked)
        self.chat_room_grid = Gtk.Grid()
        self.chat_room_grid.attach(self.chat_room_label, 0, 0, 1, 1)
        self.chat_room_grid.attach(self.chat_room_entry, 1, 0, 1, 1)
        self.chat_room_grid.attach(self.enter_button, 0, 1, 2, 1)
        self.chat_room_grid.attach(self.create_channel,0,2,2,1)
        self.add(self.chat_room_grid)

    def on_create_channel_button_clicked(self,button):
        data = {
            'action':'create_channel'
        }
        json_data = json.dumps(data).encode('utf-8')
        os.write(1,json_data)
        self.hide()
        chat_window = ChatWindow('Room')
        chat_window.connect("destroy", Gtk.main_quit)
        chat_window.show_all()
        Gtk.main()

    def on_enter_button_clicked(self, button):
        room_name = self.chat_room_entry.get_text()
        data = {
            'action':'join_channel',
            'data':room_name
        }
        json_data = json.dumps(data).encode('utf-8')
        os.write(1,json_data)

        if room_name:
            self.hide()
            chat_window = ChatWindow(room_name)
            chat_window.connect("destroy", Gtk.main_quit)
            chat_window.show_all()
            Gtk.main()
        else:
            dialog = Gtk.MessageDialog(
                parent=self,
                flags=0,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text="Please enter a room name."
            )
            dialog.run()
            dialog.destroy()



class ChatWindow(Gtk.Window):

    def __init__(self, room_name):
        Gtk.Window.__init__(self, title=f"Chat Room - {room_name}")

        self.set_default_size(400, 300)

        self.chat_history = Gtk.TextView()
        self.chat_history.set_editable(False)
        self.chat_history_buffer = self.chat_history.get_buffer()

        self.chat_entry = Gtk.Entry()
        self.send_button = Gtk.Button(label="Send")
        self.send_button.connect("clicked", self.on_send_button_clicked)

        self.chat_grid = Gtk.Grid()
        self.chat_grid.attach(self.chat_history, 0, 0, 2, 1)
        self.chat_grid.attach(self.chat_entry, 0, 1, 1, 1)
        self.chat_grid.attach(self.send_button, 1, 1, 1, 1)

        self.add(self.chat_grid)
        self.reader = StdioReader(self.update_chat)
        self.reader.start()

    def on_send_button_clicked(self, button):
        message = self.chat_entry.get_text()
        if message:
            data = {
                'action':'send',
                'data':message
            }
            json_data = json.dumps(data).encode('utf-8')
            os.write(1,json_data)
            self.chat_history_buffer.insert_at_cursor(f"You: {message}\n")
            self.chat_entry.set_text("")
    def on_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            print("OK button clicked")

            dialog.destroy()
    def update_chat(self,data):
        if data['task'] == 'join_channel':
            self.chat_history_buffer.insert_at_cursor(f"Connected\n")
        if data['task'] == 'create_channel':
            self.chat_history_buffer.insert_at_cursor(f"Channel: {data['channel']}\n")
        if data['task'] == 'message':
            self.chat_history_buffer.insert_at_cursor(f"{data['from']}: {data['message']}\n")


if __name__ == "__main__":
    chat_room_window = ChatRoomWindow()
    chat_room_window.connect("destroy", Gtk.main_quit)
    chat_room_window.show_all()

    Gtk.main()
