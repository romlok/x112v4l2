"""
	Functionality for handling the UI elements
"""
import os

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from x112v4l2 import v4l2
from x112v4l2.gtk import utils


class MainUI(object):
	"""
		General wrapper around all the main window functionality
	"""
	main_glade = os.path.join(os.path.dirname(__file__), 'main.glade')
	device_glade = os.path.join(os.path.dirname(__file__), 'device.glade')
	
	# Icons
	ICON_RELOAD = 'gtk-refresh'
	ICON_YES = 'gtk-yes'
	ICON_NO = 'gtk-no'
	
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		self.load_main_window()
		self.add_device('/dev/video666', 'Gateway to Hell')
		
	def run(self):
		self.main_window.show_all()
		Gtk.main()
		
	def load_main_window(self):
		"""
			Loads the main window UI from file
		"""
		builder = Gtk.Builder()
		builder.add_from_file(self.main_glade)
		builder.connect_signals(SignalHandler(ui=self))
		# We want the main window
		self.main_window = builder.get_object('main')
		# We also want the device-tab widget
		self.device_list = builder.get_object('device_list')
		
		# Finally, clean up the template/demo widgets we don't need
		self.clear_devices()
		
	
	def get_widget(self, name):
		"""
			Return the `name`d widget, or none
		"""
		return utils.find_child_by_id(self.main_window, name)
		
	
	def clear_devices(self):
		"""
			Removes all device configuration tabs from the main UI
		"""
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
		# There's no way to completely copy widget style,
		# and label justification can't be set through CSS,
		# so we manually make sure the justification is consistent.
		tab_label.set_justify(first_label.get_justify())
		
		self.device_list.append_page(page, tab_label)
		
		return page
		
	
class SignalHandler(object):
	"""
		Handle all the signals
	"""
	def __init__(self, ui, **kwargs):
		"""
			Create a new SignalHandler
			
			The `ui` parameter should be an instance of a MainUI class.
		"""
		super().__init__(**kwargs)
		self.ui = ui
		
	
	def onExitApplication(self, widget, data):
		return Gtk.main_quit(widget, data)
		
	def onRefreshDeviceInfo(self, widget, data=None):
		"""
			Rechecks the state of the v4l2loopback kernel module
		"""
		mod_avail_widget = self.ui.get_widget('v4l2_module_available_indicator')
		mod_loaded_widget = self.ui.get_widget('v4l2_module_loaded_indicator')
		num_devices_widget = self.ui.get_widget('v4l2_num_devices')
		
		# Indicate that stuff is reloading
		mod_avail_widget.set_from_icon_name(self.ui.ICON_RELOAD, Gtk.IconSize.BUTTON)
		mod_loaded_widget.set_from_icon_name(self.ui.ICON_RELOAD, Gtk.IconSize.BUTTON)
		num_devices_widget.set_label('???')
		
		# Get t'info
		module_available = v4l2.get_module_available()
		if not module_available:
			module_loaded = False
		else:
			module_loaded = v4l2.get_module_loaded()
		
		if not module_loaded:
			devices = []
		else:
			devices = v4l2.get_devices()
		
		# Update the UI
		icons = {True: self.ui.ICON_YES, False: self.ui.ICON_NO}
		mod_avail_widget.set_from_icon_name(icons[module_available], Gtk.IconSize.BUTTON)
		mod_loaded_widget.set_from_icon_name(icons[module_loaded], Gtk.IconSize.BUTTON)
		num_devices_widget.set_label(str(len(list(devices))))
		
	
