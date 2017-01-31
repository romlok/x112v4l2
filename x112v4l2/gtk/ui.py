"""
	Functionality for handling the UI elements
"""
import os
import subprocess
import fcntl
from concurrent import futures

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GLib
from gi.repository import GObject

from x112v4l2 import thumbs
from x112v4l2 import ffmpeg
from x112v4l2.gtk import signals
from x112v4l2.gtk import utils


class BaseUI(object):
	"""
		Core functionality for all UI classes.
	"""
	# Random constants
	STATE_RELOADING = 'reloading'
	STATE_RELOADING_LABEL = '???'
	MAX_WORKERS = 2
	
	# Icons
	ICON_RELOAD = 'gtk-refresh'
	ICON_YES = 'gtk-yes'
	ICON_NO = 'gtk-no'
	
	
	def __init__(self, executor=None, **kwargs):
		"""
			Fire up a new UI
			
			The `executor` should be a futures Executor class.
			If none is supplied, a new ProcessPoolExecutor is created.
		"""
		if executor is None:
			executor = futures.ProcessPoolExecutor(max_workers=self.MAX_WORKERS)
		self.executor = executor
		
		super().__init__(**kwargs)
		
	
	def future_callback(self, func, *args, **kwargs):
		"""
			Return a function which can be used as a future callback
			
			At the time of the callback, the `future.result()` is sent
			to the function as the first argument, followed by any
			additional arguments specified here.
		"""
		def callback(future):
			return GObject.idle_add(func, future.result(), *args, **kwargs)
			
		return callback
		
	
class MainUI(BaseUI):
	"""
		General wrapper around all the main window functionality
	"""
	# UI definition files
	MAIN_GLADE = os.path.join(os.path.dirname(__file__), 'main.glade')
	
	
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		
		# The current DeviceUI instances
		self.deviceuis = []
		# The most recent X11 window information
		self.x11_windows = []
		
		self.load_main_window()
		
		
	def run(self):
		self.main_window.show_all()
		Gtk.main()
		
	def stop(self):
		for device in self.deviceuis:
			device.stop_process()
		self.executor.shutdown(wait=True)
		return Gtk.main_quit()
		
		
	def load_main_window(self):
		"""
			Loads the main window UI from file
		"""
		builder = Gtk.Builder()
		builder.add_from_file(self.MAIN_GLADE)
		builder.connect_signals(signals.MainHandler(ui=self))
		# We want the main window
		self.main_window = builder.get_object('main')
		# We also want the device-tab widget
		self.device_list = builder.get_object('device_list')
		
		# Finally, clean up the template/demo widgets we don't need
		self.clear_devices()
		
	
	def get_widget(self, name):
		"""
			Return the `name`d widget, or None
		"""
		return utils.find_child_by_id(self.main_window, name)
		
	
	def get_device_names(self):
		"""
			Returns the list of device names from the UI
		"""
		device_names_widget = self.get_widget('v4l2_device_names')
		names = device_names_widget.get_buffer().get_property('text')
		names = [name.strip() for name in names.split('\n') if name.strip()]
		return names
		
	def clear_devices(self):
		"""
			Removes all device configuration tabs from the main UI
		"""
		self.deviceuis = []
		self.device_list.set_current_page(0)
		for idx in range(0, self.device_list.get_n_pages() - 1):
			self.device_list.remove_page(-1)
		
	def add_device(self, path, label):
		"""
			Adds a device to the main UI
		"""
		device = DeviceUI(
			executor=self.executor,
			path=path,
			label=label,
			windows=self.x11_windows,
		)
		
		# Use the first tab's label as a template for the new one
		first_page = self.device_list.get_nth_page(0)
		first_label = self.device_list.get_tab_label(first_page)
		
		tab_label = Gtk.Label('{}\n{}'.format(label, path))
		# There's no way to completely copy widget style,
		# and label justification can't be set through CSS,
		# so we manually make sure the justification is consistent.
		tab_label.set_justify(first_label.get_justify())
		
		self.device_list.append_page(device.widget, tab_label)
		
		self.deviceuis.append(device)
		return device
		
	
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
		
		self.x11_windows = windows
		
	def show_x11_thumb_path(self, path):
		widget = self.get_widget('x11_thumb_path_indicator')
		widget.set_label(path)
		
	def show_x11_thumbs(self, thumbs):
		count_widget = self.get_widget('x11_thumb_count_indicator')
		if thumbs == self.STATE_RELOADING:
			# Clear all the things
			count_widget.set_label(self.STATE_RELOADING_LABEL)
			for device in self.deviceuis:
				device.clear_thumbs()
			return
			
		# We're doing it live!
		count_widget.set_label(str(len(thumbs)))
		
		for device in self.deviceuis:
			device.show_thumbs(self.x11_windows)
		
	
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
		
	
class DeviceUI(BaseUI):
	"""
		Wrapper around device-specific functionality
	"""
	DEVICE_GLADE = os.path.join(os.path.dirname(__file__), 'device.glade')
	THUMB_GLADE = os.path.join(os.path.dirname(__file__), 'device-thumb.glade')
	
	
	def __init__(self, path, label, windows=None, **kwargs):
		"""
			Create a new device UI inside the given `container`
			
			If `windows` is supplied, the thumb list will be populated.
		"""
		super().__init__(**kwargs)
		self.path = path
		self.label = label
		self.widget = self.load_config_widget()
		self.clear_thumbs()
		if windows:
			self.show_thumbs(windows=windows)
		
		self.process = None
		
	
	def load_config_widget(self):
		"""
			Loads the device config UI from file
		"""
		builder = Gtk.Builder()
		builder.add_from_file(self.DEVICE_GLADE)
		builder.connect_signals(signals.DeviceHandler(ui=self))
		config = builder.get_object('device_config')
		return config
		
	def load_thumb_widget(self):
		"""
			Loads the thumb_list item widget
		"""
		builder = Gtk.Builder()
		builder.add_from_file(self.THUMB_GLADE)
		widget = builder.get_object('thumb')
		return widget
		
	
	def get_widget(self, name):
		"""
			Return the `name`d widget, or None
		"""
		return utils.find_child_by_id(self.widget, name)
		
	
	def clear_thumbs(self):
		"""
			Remove all thumbnails from the list
		"""
		thumb_list = self.get_widget('thumb_list')
		for row in thumb_list.get_children():
			thumb_list.remove(row)
		
	def show_thumbs(self, windows):
		"""
			Show/update the list of window thumbnails
		"""
		self.clear_thumbs()
		for win in windows:
			thumb = self.add_thumb(
				label=win.get_wm_name(),
				image=os.path.join(thumbs.CACHE_PATH, thumbs.get_win_filename(win)),
			)
			# Associate the thumb with the window, for later reference
			thumb.source_window = win
			
		
	def add_thumb(self, label, image):
		"""
			Add a single thumbnail to the list of window thumbnails
		"""
		thumb_list = self.get_widget('thumb_list')
		thumb = self.load_thumb_widget()
		# The label part
		label_widget = utils.find_child_by_id(thumb, 'label')
		label_widget.set_text(label)
		# The image part
		image_widget = utils.find_child_by_id(thumb, 'image')
		image_widget.set_from_file(image)
		# Finally, add it to the list
		thumb_list.add(thumb)
		return thumb
		
	
	def set_source_window(self, window):
		"""
			Set the source details from the given `window`
		"""
		geom = window.get_abs_geometry()
		self.get_widget('source_screen').set_text(str(window.screen.full_id))
		self.get_widget('source_x').set_text(str(geom['x']))
		self.get_widget('source_y').set_text(str(geom['y']))
		self.get_widget('source_width').set_text(str(geom['width']))
		self.get_widget('source_height').set_text(str(geom['height']))
		
	
	def update_output_size(self, geom=None, width=None, height=None):
		"""
			Update output resolution
			
			Explicit `width` and `height` parameters can be given,
			after which will be checked any given `geom` dictionary.
			If none of these arguments are supplied, the values will
			be determined from the UI widgets as appropriate.
		"""
		width_widget = self.get_widget('output_width')
		height_widget = self.get_widget('output_height')
		
		# Work out what values of width and height to use
		if width is not None and height is not None:
			pass
		elif geom is not None:
			width = geom['width']
			height = geom['height']
		else:
			# Check what's going on in the UI
			from_source_widget = self.get_widget('output_use_source_size')
			if from_source_widget.get_active():
				width = self.get_widget('source_width').get_text()
				height = self.get_widget('source_height').get_text()
			else:
				# Just keep whatever's in the current widgets
				width = width_widget.get_text()
				height = height_widget.get_text()
			width = int(width) if width.isdigit() else 0
			height = int(height) if height.isdigit() else 0
		
		# Now we can update the widgets
		width_widget.set_text(str(width))
		height_widget.set_text(str(height))
		
	
	def get_process_command(self):
		"""
			Provide ffmpeg command based on what the UI displays
			
			The command is returned as a list of string tokens,
			suitable for passing to subprocess.Popen, or ' '.join().
			
			If a command cannot be compiled due to missing or invalid
			inputs, the return value will be an empty list.
		"""
		# We take as much as possible from the UI, so that the
		# actual values we use are visible to the user.
		try:
			cmd = ffmpeg.compile_command(
				source_screen=self.get_widget('source_screen').get_text(),
				source_x=self.get_widget('source_x').get_text(),
				source_y=self.get_widget('source_y').get_text(),
				source_width=self.get_widget('source_width').get_text(),
				source_height=self.get_widget('source_height').get_text(),
				output_filename=self.path,
				output_width=self.get_widget('output_width').get_text(),
				output_height=self.get_widget('output_height').get_text(),
				fps=self.get_widget('output_fps').get_text(),
				loglevel='info',
			)
		except ValueError:
			cmd = []
		return cmd
		
	def update_process_command(self):
		"""
			Update the display of the ffmpeg command to use
		"""
		cmd = self.get_process_command()
		self.get_widget('process_command').set_text(' '.join(cmd))
		
	def show_process_state(self):
		if self.process is None:
			state = 'Stopped'
		elif self.process.poll() is not None:
			state = 'Stopped ({})'.format(self.process.returncode)
		else:
			state = 'Running (pid {})'.format(self.process.pid)
		
		self.get_widget('process_state').set_label(state)
		
	def clear_process_stdout(self):
		"""
			Clear the display of the process STDOUT
		"""
		stdout_widget = self.get_widget('process_stdout')
		stdout_widget.get_buffer().set_text('')
		
	def clear_process_stderr(self):
		"""
			Clear the display of the process STDERR
		"""
		stderr_widget = self.get_widget('process_stderr')
		stderr_widget.get_buffer().set_text('')
		
	def append_process_stdout(self, output):
		"""
			Append some text to the process STDOUT display
		"""
		stdout_buffer = self.get_widget('process_stdout').get_buffer()
		stdout_buffer.insert(stdout_buffer.get_end_iter(), output)
		
	def append_process_stderr(self, output):
		"""
			Append some text to the process STDERR display
		"""
		stderr_buffer = self.get_widget('process_stderr').get_buffer()
		stderr_buffer.insert(stderr_buffer.get_end_iter(), output)
		
	def start_process(self):
		"""
			Start the ffmpeg subprocess
		"""
		if self.process and self.process.poll() is None:
			raise RuntimeError('Refusing to start process when already running')
		
		cmd = self.get_process_command()
		self.process = subprocess.Popen(
			cmd,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			stdin=subprocess.DEVNULL,
		)
		# Make the pipes non-blocking
		flags = fcntl.fcntl(self.process.stdout, fcntl.F_GETFL)
		fcntl.fcntl(self.process.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)
		flags = fcntl.fcntl(self.process.stderr, fcntl.F_GETFL)
		fcntl.fcntl(self.process.stderr, fcntl.F_SETFL, flags | os.O_NONBLOCK)
		# Clear any output from previous incarnations
		self.clear_process_stdout()
		self.clear_process_stderr()
		
		# Update the UI when there's output from the process
		def output_callback(fd, condition, pipe, func):
			""" Read from pipe, and pass to the given func """
			output = pipe.read()
			if not output:
				return False
			func(output.decode('utf-8'))
			return condition != GLib.IO_HUP
			
		stdout_read_cb = GLib.io_add_watch(
			self.process.stdout,
			GLib.PRIORITY_DEFAULT,
			GLib.IO_IN | GLib.IO_HUP,
			output_callback,
			self.process.stdout,
			self.append_process_stdout,
		)
		GLib.io_add_watch(
			self.process.stderr,
			GLib.PRIORITY_DEFAULT,
			GLib.IO_IN | GLib.IO_HUP,
			output_callback,
			self.process.stderr,
			self.append_process_stderr,
		)
		
	def stop_process(self):
		"""
			Stop any ffmpeg subprocess
			
			NB: This function blocks until the subprocess is finished!
		"""
		if not self.process or self.process.poll() is not None:
			# Already stopped
			self.show_process_state()
			return
		
		self.process.terminate()
		## TODO: Handle this in an async manner
		self.process.wait()
		self.show_process_state()
		
	
