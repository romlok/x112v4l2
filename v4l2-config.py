#!/usr/bin/env python3
"""
	Simple script to reconfigure v4l2loopback devices
"""
import sys

from x112v4l2 import v4l2


if __name__ == '__main__':
	labels = sys.argv[1:]
	
	try:
		device_info = v4l2.configure_devices(labels)
	except FileNotFoundError:
		sys.stderr.write('Unable to modprobe; is this script being run as root?\n')
		sys.exit(1)
	
	for device in device_info:
		sys.stdout.write('{path}: {label}\n'.format(**device))
	
