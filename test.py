#!/usr/bin/env python3
"""
	Test script to fetch a list of castable desktops/windows
"""
import subprocess

from x112v4l2 import x11


if __name__ == '__main__':
	for screen_id, screen in x11.get_screens().items():
		print('Screen:', screen_id)
		print(' Windows:')
		for window in x11.get_windows(screen):
			attribs = window.get_attributes()
			geom = window.get_abs_geometry()
			print(' ', window.id, window.get_wm_name())
			print('  ', geom)
			# Save a screenshot of that window
			cmd = [
				'ffmpeg',
				# Input options
				'-f', 'x11grab',
				'-s', '{}x{}'.format(geom['width'], geom['height']),
				'-i', '{screen}+{x},{y}'.format(
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
			
	
