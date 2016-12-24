"""
	Functionality for handling the UI elements
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class MainUI(object):
	"""
		General wrapper around all the main window functionality
	"""
	main_glade = 'main.glade'
	device_glade = 'device.glade'
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		self.main_window = self.load_main_window()
		
	def load_main_window(self):
		builder = Gtk.Builder()
		builder.add_from_file(self.main_glade)
		main = builder.get_object('main')
		main.connect("delete-event", Gtk.main_quit)
		return main
		
	def load_device_config(self):
		builder = Gtk.Builder()
		builder.add_from_file(self.device_glade)
		config = builder.get_object('device_config')
		return config
		
	def run(self):
		self.main_window.show_all()
		Gtk.main()
	
