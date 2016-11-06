#!/usr/bin/env python3
"""
	Test script to fetch a list of castable desktops/windows
"""
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
	

if __name__ == '__main__':
	display = Xlib.display.Display()
	
	for screen in get_screens(display):
		print('Screen:', screen)
		print(' Windows:')
		for window in get_windows(display.screen(screen)):
			attribs = window.get_attributes()
			geom = window.get_geometry()
			print(' ', window.id, window.get_wm_name())
			print('  ', geom.x, geom.y, geom.width, geom.height)
	
