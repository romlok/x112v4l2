#!/usr/bin/env python3
"""
	Test script to fetch a list of castable desktops/windows
"""
import subprocess
import Xlib.X
import Xlib.display


def get_screens(display):
	"""
		Returns an iterable of X screen IDs
	"""
	return range(display.screen_count())
	
def get_windows(screen):
	"""
		Returns an iterable of X window objects
	"""
	windows = []
	for win in get_subwindows(screen.root):
		attribs = win.get_attributes()
		if attribs.map_state != Xlib.X.IsViewable:
			continue
		windows.append(win)
		
	return windows
	
def get_subwindows(root):
	"""
		Returns an iterable of all windows under the given root
		
		Recursively delves into the deepest recesses of the window hierarchy.
	"""
	windows = []
	for win in root.query_tree().children:
		windows.append(win)
		windows.extend(get_subwindows(win))
		
	return windows
	
def get_window_pos(window):
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
	
def get_window_geom(window):
	"""
		Returns a dict with x, y, width, height
		
		Ensures that the given geometry does not exceed the bounds of
		the window's screen.
	"""
	geom = {}
	root = window.query_tree().root
	# First the position
	pos = get_window_pos(window)
	root_pos = get_window_pos(root)
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
	


if __name__ == '__main__':
	display = Xlib.display.Display()
	
	for screen_id in get_screens(display):
		print('Screen:', screen_id)
		print(' Windows:')
		for window in get_windows(display.screen(screen_id)):
			attribs = window.get_attributes()
			geom = get_window_geom(window)
			print(' ', window.id, window.get_wm_name())
			print('  ', geom)
			# Save a screenshot of that window
			cmd = [
				'ffmpeg',
				# Input options
				'-f', 'x11grab',
				'-s', '{}x{}'.format(geom['width'], geom['height']),
				'-i', '{display}.{screen}+{x},{y}'.format(
					display=display.get_display_name(),
					screen=screen_id,
					x=geom['x'],
					y=geom['y'],
				),
				# Output options
				'-vframes', '1',
				'-y', # Overwrite without asking
				'/tmp/snaps/{window}.png'.format(window=window.id),
			]
			print('  ', ' '.join(cmd))
			proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			
	
