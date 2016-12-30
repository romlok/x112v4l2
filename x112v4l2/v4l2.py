"""
	Gubbins for interfacing with the v4l2 side of things
"""
import os
import subprocess


DEFAULT_LABEL = 'Virtual camera'


def get_module_available():
	"""
		Whether or not v4l2loopback is installed
	"""
	proc = subprocess.Popen(
		['/sbin/modinfo', 'v4l2loopback', '-n'],
		stdout=subprocess.DEVNULL,
		stderr=subprocess.DEVNULL,
	)
	return not proc.wait()
	
def get_module_loaded():
	"""
		Whether or not the v4l2loopback module is in the kernel
	"""
	proc = subprocess.Popen(
		['grep', 'v4l2loopback', '/proc/modules'],
		stdout=subprocess.DEVNULL,
		stderr=subprocess.DEVNULL,
	)
	return not proc.wait()
	

def get_devices():
	"""
		Provides an iterable of v4l2 loopback device info
		
		Each item is a dictionary of: {
			'path': '/path/to/dev/video#',
			'label': 'The user-defined label for the device',
		}
	"""
	proc = subprocess.Popen(
		['v4l2-ctl', '--list-devices'],
		stdout=subprocess.PIPE,
		stderr=subprocess.DEVNULL,
	)
	devices = []
	for line in proc.stdout:
		if not b'platform:v4l2loopback' in line:
			continue
		info = {}
		info['label'] = line.decode('utf8').rsplit(' ', 1)[0]
		next_line = proc.stdout.readline()
		info['path'] = next_line.decode('utf8').strip()
		devices.append(info)
		
	return devices
	

def configure_devices(labels=None):
	"""
		Configures one or more v4l2 loopback devices
		
		Any existing configuration will be overridden.
		
		The `labels` parameter, if given, should be an iterable of
		labels, one for each desired loopback device. Eg:
			labels=['Desktop', 'Cat videos', 'Spoopycam']
		If no labels are given, a single device will be created, with
		some boring default label.
		
		Returns an iterable of the new devices
	"""
	# Sanity-check the labels
	if not labels:
		labels = [DEFAULT_LABEL]
	if any(not isinstance(label, str) for label in labels):
		raise TypeError('Device labels must be strings')
	
	# Re-modprobe the kernel module with the new params
	proc = subprocess.Popen(
		[
			'pkexec',
			os.path.join(os.path.dirname(__file__), '..', 'v4l2-reload.sh'),
			'exclusive_caps=1',
			'devices={}'.format(len(labels)),
			'card_label={}'.format(','.join(labels)),
		],
		stdout=subprocess.DEVNULL,
		stderr=subprocess.PIPE,
	)
	retcode = proc.wait()
	if retcode:
		raise OSError('Failed to reload v4l2loopback kernel module:\n\n{}'.format(proc.stderr.read()))
	
	return get_devices()
	
