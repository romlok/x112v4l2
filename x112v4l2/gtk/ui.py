"""
	Functionality for handling the UI elements
"""
import os
from concurrent import futures

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from x112v4l2 import v4l2
from x112v4l2 import x11
from x112v4l2 import ffmpeg
from x112v4l2 import thumbs
from x112v4l2.gtk import utils


class MainUI(object):
	"""
		General wrapper around all the main window functionality
	"""
	main_glade = os.path.join(os.path.dirname(__file__), 'main.glade')
	device_glade = os.path.join(os.path.dirname(__file__), 'device.glade')
	
	STATE_RELOADING = 'reloading'
	STATE_RELOADING_LABEL = '???'
	MAX_WORKERS = 2
	
	
	# Icons
	ICON_RELOAD = 'gtk-refresh'
	ICON_YES = 'gtk-yes'
	ICON_NO = 'gtk-no'
	
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		thumbs.mkdir()
		
		self.executor = futures.ProcessPoolExecutor(max_workers=self.MAX_WORKERS)
		
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
		
	def get_device_names(self):
		"""
			Returns the list of device names from the UI
		"""
		device_names_widget = self.get_widget('v4l2_device_names')
		names = device_names_widget.get_buffer().get_property('text')
		names = [name.strip() for name in names.split('\n') if name.strip()]
		return names
		
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
		
	
	def show_v4l2_available(self, state):
		"""
			Update indicators of v4l2 availability
		"""
		mod_avail_widget = self.get_widget('v4l2_module_available_indicator')
		if state == self.STATE_RELOADING:
			icon = self.ICON_RELOAD
		else:
			icon = self.ICON_YES if state else self.ICON_NO
		mod_avail_widget.set_from_icon_name(icon, Gtk.IconSize.BUTTON)
		
	def show_v4l2_loaded(self, state):
		"""
			Update indicators of v4l2 loadedness
		"""
		mod_loaded_widget = self.get_widget('v4l2_module_loaded_indicator')
		if state == self.STATE_RELOADING:
			icon = self.ICON_RELOAD
		else:
			icon = self.ICON_YES if state else self.ICON_NO
		mod_loaded_widget.set_from_icon_name(icon, Gtk.IconSize.BUTTON)
		
	def show_v4l2_devices(self, devices):
		"""
			Update indicators of v4l2 devices
		"""
		# Update the summary's total device count
		num_devices_widget = self.get_widget('v4l2_num_devices')
		if devices == self.STATE_RELOADING:
			num_devices_widget.set_label(self.STATE_RELOADING_LABEL)
			devices = []
		else:
			num_devices_widget.set_label(str(len(list(devices))))
		
		# Populate the list of device names
		device_names_widget = self.get_widget('v4l2_device_names')
		buff = device_names_widget.get_buffer()
		buff.set_text('\n'.join(dev['label'] for dev in devices))
		
		# Re/populate the device tabs
		self.clear_devices()
		for device in devices:
			self.add_device(path=device['path'], label=device['label'])
		
	
	def show_x11_display_info(self, displays):
		"""
			Update X11 display info UI
		"""
		widget = self.get_widget('x11_display_count_indicator')
		if displays == self.STATE_RELOADING:
			widget.set_label(self.STATE_RELOADING_LABEL)
		else:
			widget.set_label(str(len(displays)))
		
	def show_x11_screen_info(self, screens):
		"""
			Update X11 screen info UI
		"""
		widget = self.get_widget('x11_screen_count_indicator')
		if screens == self.STATE_RELOADING:
			widget.set_label(self.STATE_RELOADING_LABEL)
		else:
			widget.set_label(str(len(screens)))
		
	def show_x11_window_info(self, windows):
		"""
			Update X11 window info UI
		"""
		widget = self.get_widget('x11_window_count_indicator')
		if windows == self.STATE_RELOADING:
			widget.set_label(self.STATE_RELOADING_LABEL)
		else:
			widget.set_label(str(len(windows)))
		
	def show_x11_thumb_path(self, path):
		widget = self.get_widget('x11_thumb_path_indicator')
		widget.set_label(path)
		
	def show_x11_thumbs(self, thumbs):
		count_widget = self.get_widget('x11_thumb_count_indicator')
		if thumbs == self.STATE_RELOADING:
			count_widget.set_label(self.STATE_RELOADING_LABEL)
		else:
			count_widget.set_label(str(len(thumbs)))
		
	
	def show_ffmpeg_installed(self, state):
		"""
			Update indicators of ffmpeg installed-ness
		"""
		widget = self.get_widget('ffmpeg_installed_indicator')
		if state == self.STATE_RELOADING:
			icon = self.ICON_RELOAD
		else:
			icon = self.ICON_YES if state else self.ICON_NO
		widget.set_from_icon_name(icon, Gtk.IconSize.BUTTON)
		
	def show_ffmpeg_version(self, version):
		"""
			Update indicators of ffmpeg devices
		"""
		# Update the version string
		widget = self.get_widget('ffmpeg_version_indicator')
		if version == self.STATE_RELOADING:
			widget.set_label(self.STATE_RELOADING_LABEL)
		else:
			widget.set_label(str(version))
		
	
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
		
	
	def exit_application(self, *args):
		return Gtk.main_quit(*args)
		
	
	def on_show_main(self, *args):
		"""
			Triggered when the main window is shown
		"""
		self.refresh_v4l2_info()
		self.refresh_ffmpeg_info()
		self.refresh_x11_info()
		self.regen_x11_thumbs()
	
	def refresh_v4l2_info(self, *args):
		"""
			Recheck the state of the v4l2loopback kernel module
		"""
		# Indicate that stuff is reloading
		self.ui.show_v4l2_available(self.ui.STATE_RELOADING)
		self.ui.show_v4l2_loaded(self.ui.STATE_RELOADING)
		self.ui.show_v4l2_devices(self.ui.STATE_RELOADING)
		
		# Async info-getting
		avail_future = self.ui.executor.submit(v4l2.get_module_available)
		avail_future.add_done_callback(
			lambda f: self.ui.show_v4l2_available(f.result())
		)
		
		loaded_future = self.ui.executor.submit(v4l2.get_module_loaded)
		loaded_future.add_done_callback(
			lambda f: self.ui.show_v4l2_loaded(f.result())
		)
		
		devices_future = self.ui.executor.submit(v4l2.get_devices)
		devices_future.add_done_callback(
			lambda f: self.ui.show_v4l2_devices(f.result())
		)
		
	def set_v4l2_device_info(self, *args):
		"""
			Applies any changes made to the v4l2 configuration
		"""
		## TODO: Indicate we're updating
		names = self.ui.get_device_names()
		devices_future = self.ui.executor.submit(v4l2.configure_devices, names)
		devices_future.add_done_callback(
			lambda f: self.refresh_v4l2_info(f.result())
		)
		
	
	def refresh_x11_info(self, *args):
		"""
			Recheck the X11 situation
		"""
		# Indicate stuff is reloading
		self.ui.show_x11_display_info(self.ui.STATE_RELOADING)
		self.ui.show_x11_screen_info(self.ui.STATE_RELOADING)
		self.ui.show_x11_window_info(self.ui.STATE_RELOADING)
		
		# Xlib classes aren't picklable, so we can't future this :/
		displays = x11.get_displays()
		self.ui.show_x11_display_info(displays)
		screens = x11.get_screens()
		self.ui.show_x11_screen_info(screens)
		windows = x11.get_windows()
		self.ui.show_x11_window_info(list(windows))
		
	def regen_x11_thumbs(self, *args):
		"""
			(Re-)Generate thumbnails of all X11 windows
		"""
		self.ui.show_x11_thumb_path(thumbs.CACHE_PATH)
		self.ui.show_x11_thumbs(self.ui.STATE_RELOADING)
		
		future = self.ui.executor.submit(thumbs.create_all)
		future.add_done_callback(
			lambda f: self.ui.show_x11_thumbs(f.result())
		)
		
	
	def refresh_ffmpeg_info(self, *args):
		"""
			Recheck the state of the ffmpeg binary
		"""
		# Indicate that stuff is reloading
		self.ui.show_ffmpeg_installed(self.ui.STATE_RELOADING)
		self.ui.show_ffmpeg_version(self.ui.STATE_RELOADING)
		
		version_future = self.ui.executor.submit(ffmpeg.get_version)
		version_future.add_done_callback(
			lambda f: self.ui.show_ffmpeg_installed(f.result())
		)
		version_future.add_done_callback(
			lambda f: self.ui.show_ffmpeg_version(f.result())
		)
		
	
