#!/usr/bin/env python3
"""
	Main script for the x112v4l2 application GUI
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

GLADE_FILE = 'x112v4l2.glade'


if __name__ == '__main__':
	builder = Gtk.Builder()
	builder.add_from_file(GLADE_FILE)
	main = builder.get_object('main')
	main.connect("delete-event", Gtk.main_quit)
	main.show_all()
	Gtk.main()
	
