#!/usr/bin/env python3
"""
	Test script to fetch a list of castable desktops/windows
"""
from x112v4l2 import x11
from x112v4l2 import ffmpeg


if __name__ == '__main__':
	for screen_id, screen in x11.get_screens().items():
		print('Screen:', screen_id)
		print(' Windows:')
		for window in x11.get_windows([screen]):
			print(' ', window.id, window.get_wm_name())
			print('  ', window.get_abs_geometry())
			print('  ', window.get_attributes())
			# Save a screenshot of that window
			proc = ffmpeg.screenshot(
				screen_id=screen_id,
				geometry=window.get_abs_geometry(),
				filename='/tmp/snaps/{win}.png'.format(win=window.id),
			)
			print('  ', ' '.join(proc.args))
	
