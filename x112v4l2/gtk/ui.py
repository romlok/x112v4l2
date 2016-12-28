"""
	Functionality for handling the UI elements
"""
import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class MainUI(object):
	"""
		General wrapper around all the main window functionality
	"""
	main_glade = os.path.join(os.path.dirname(__file__), 'main.glade')
	device_glade = os.path.join(os.path.dirname(__file__), 'device.glade')
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		self.load_main_window()
		
	def run(self):
		self.main_window.show_all()
		Gtk.main()
		
	def load_main_window(self):
		"""
			Loads the main window UI from file
		"""
		builder = Gtk.Builder()
		builder.add_from_file(self.main_glade)
		# We want the main window
		self.main_window = builder.get_object('main')
		self.main_window.connect("delete-event", Gtk.main_quit)
		# We also want the device-tab widget
		self.device_list = builder.get_object('device_list')
		
		# Finally, clean up the template/demo widgets we don't need
		self.clear_devices()
		
	def clear_devices(self):
		"""
			Removes all device configuration tabs from the main UI
		"""
		# AFAICT there's no built-in way to "find" a particular child
		# so we assume we know the widget layout. Ell oh ell.
		self.device_list.set_current_page(0)
		for idx in range(0, self.device_list.get_n_pages() - 1):
			self.device_list.remove_page(-1)
		
	def load_device_config(self):
		"""
			Loads the device configuration UI from file
		"""
		builder = Gtk.Builder()
		builder.add_from_file(self.device_glade)
		config = builder.get_object('device_config')
		return config
		
	def add_device(self, path, label):
		"""
			Adds a device to the main UI
		"""
		# Use the first tab's label as a template for the new one
		first_page = self.device_list.get_nth_page(0)
		first_label = self.device_list.get_tab_label(first_page)
		
		page = self.load_device_config()
		tab_label = Gtk.Label('{}\n{}'.format(label, path))
		## TODO: I really want to set the tab_label style to match
		## that of the first_label, but set_style is:
		## "Deprecated since version 3.0: Use Gtk.StyleContext instead"
		## But I can't see any way to actually do it using StyleContext
		#tab_label.SOMETHING(first_label.get_style_context())
		self.device_list.append_page(page, tab_label)
		
		return page
		
	
