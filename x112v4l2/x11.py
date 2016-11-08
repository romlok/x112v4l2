"""
	Gubbins for interfacing with X11/xlib
"""
import Xlib.X
import Xlib.error
import Xlib.display
import Xlib.xobject.drawable


# We ignore windows whose dimensions are both under this value
MIN_SIZE = 64


def get_display(name):
	"""
		Returns the named X Display instance
		
		The result is None if no such Display can be found.
		
		This is intended primarily to wrap the various
		different known error cases that can occur, and tidy
		up display-fetching code.
	"""
	try:
		return Xlib.display.Display(name)
	except Xlib.error.DisplayNameError:
		# The name didn't look like a Display
		# eg. didn't start with a ':'.
		return None
	except FileNotFoundError:
		# The name looked a bit like a display,
		# but was not numeric; eg. ':blah'
		return None
	except Xlib.error.DisplayConnectionError:
		# The name looked a-ok, but the socket couldn't be opened
		# (aka "file not found")
		return None
	
def get_displays():
	"""
		Provides a dict of available X Display instances
	"""
	displays = {}
	# Just try to connect to display IDs sequentially,
	# giving up when one doesn't connect
	idx = 0
	while True:
		name = ':{}'.format(idx)
		display = get_display(name)
		if not display:
			break
		displays[name] = display
		idx += 1
	
	return displays
	

def get_screens(displays=None):
	"""
		Provides a dict of available X screen objects
		
		If an iterable of `displays` is specified, as instances
		or IDs (eg. ":0"), only screens on those displays
		will be returned.
	"""
	screens = {}
	if not displays:
		displays = get_displays().values()
	
	for display in displays:
		# We always want a display object
		if not hasattr(display, 'get_display_name'):
			display = get_display(display)
			if not display:
				# Invalid display specified; move on to the next
				continue
			
		for screen_num in range(display.screen_count()):
			screen = display.screen(screen_num)
			# The full screen_id is useful to have around
			screen_id = '{disp}.{scr}'.format(
				disp=display.get_display_name(),
				scr=screen_num,
			)
			screen.full_id = screen_id
			screens[screen_id] = screen
			
	return screens
	


def get_windows(screen):
	"""
		Returns an iterable of X window objects for the given `screen`
	"""
	for win in get_subwindows(screen.root):
		attribs = win.get_attributes()
		geom = win.get_abs_geometry()
		# Disregard any that aren't visible
		if attribs.map_state != Xlib.X.IsViewable:
			continue
		# Disregard any with no title
		if not win.get_wm_name():
			continue
		# Disregard teeny windows
		if geom['width'] < MIN_SIZE and geom['height'] < MIN_SIZE:
			continue
		
		# Additional useful info that we don't already get
		win.screen = screen
		
		yield win
		
	
# Functions which are monkey-patched onto the Xlib Window class
def get_subwindows(root):
	"""
		Returns an iterable of all windows under the given root
		
		Recursively delves into the deepest recesses
		of the window hierarchy.
	"""
	for win in root.query_tree().children:
		yield win
		for subwin in get_subwindows(win):
			yield subwin
	
Xlib.xobject.drawable.Window.get_subwindows = get_subwindows

def get_window_abs_pos(window):
	"""
		Returns a 2-tuple of a window's absolute position
	"""
	x = 0
	y = 0
	win = window
	while win != Xlib.X.NONE:
		geom = win.get_geometry()
		x += geom.x
		y += geom.y
		win = win.query_tree().parent
	return (x, y)
	
Xlib.xobject.drawable.Window.get_abs_pos = get_window_abs_pos

def get_window_abs_geom(window):
	"""
		Returns a dict of x, y, width, height
		
		Additionally, ensures that the returned geometry does not
		exceed the bounds of the window's screen/root.
	"""
	geom = {}
	root = window.query_tree().root
	# First the position
	pos = window.get_abs_pos()
	root_pos = root.get_abs_pos()
	geom['x'] = max(root_pos[0], pos[0])
	geom['y'] = max(root_pos[1], pos[1])
	# Then the size
	win_geom = window.get_geometry()
	root_geom = root.get_geometry()
	geom['width'] = min(
		win_geom.width,
		root_geom.width - geom['x'],
	)
	geom['height'] = min(
		win_geom.height,
		root_geom.height - geom['y'],
	)
	
	return geom
	
Xlib.xobject.drawable.Window.get_abs_geometry = get_window_abs_geom

def get_window_wm_name(window):
	"""
		Fetch the window's wm_name via a custom method
		
		This is needed because Ubuntu/Debian ship with an
		ancient version of python-xlib, wherein get_wm_name
		is broken for non-ascii values.
		And even with the latest python-xlib (0.17), it doesn't
		check _NET_WM_NAME, which is the only place some apps put
		their title (eg. Chromium).
	"""
	ANY_TYPE = 0
	
	for prop_name in ['_NET_WM_NAME', 'WM_NAME']:
		prop_atom = window.display.get_atom(prop_name)
		prop = window.get_property(prop_atom, ANY_TYPE, 0, 100)
		if not prop:
			continue
		
		if isinstance(prop.value, bytes):
			return prop.value.decode('utf8', errors='replace')
		else:
			return prop.value
	
Xlib.xobject.drawable.Window.get_wm_name = get_window_wm_name

#
# Somewhat more high-level functions
#
def search_windows(title):
	"""
		Find and return a subset of all Window instances
		
		Use the `title` parameter to perform a partial (case-
		insensitive) match against the window's title/name.
	"""
	for screen in get_screens().values():
		for win in get_windows(screen):
			if title.lower() in win.get_wm_name().lower():
				yield win
	
