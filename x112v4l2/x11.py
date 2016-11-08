"""
	Gubbins for interfacing with X11/xlib
"""
import Xlib.X
import Xlib.error
import Xlib.display


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
			screen_id = '{disp}.{scr}'.format(
				disp=display.get_display_name(),
				scr=screen_num,
			)
			screens[screen_id] = display.screen(screen_num)
			
	return screens
	
