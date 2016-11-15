"""
	Gubbins for interfacing with the v4l2 side of things
"""
import subprocess


def get_devices():
	"""
		Provides an iterable of v4l2 loopback devices
	"""
	proc = subprocess.Popen(
		['v4l2-ctl', '--list-devices'],
		stdout=subprocess.PIPE,
		stderr=subprocess.DEVNULL,
	)
	for line in proc.stdout:
		if not b'platform:v4l2loopback' in line:
			continue
		next_line = proc.stdout.readline()
		yield next_line.decode('utf8').strip()
		
