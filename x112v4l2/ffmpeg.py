"""
	Gubbins for interfacing with ffmpeg
"""
import subprocess


def screenshot(screen_id, geometry, filename):
	"""
		Creates a screenshot image from the X screen
		
		`screen_id` should be the full name (including display name)
		of the X11 screen to capture. Eg: ":0.0".
		`geometry` should be a dict-like object providing values
		for x, y, width, and height.
		`filename` is the filesystem location where the
		screenshot will be written.
		
		The return value is a subprocess.Popen instance.
		
		NB. All output of the ffmpeg process is devnull'ed.
	"""
	cmd = [
		'ffmpeg',
		# Input options
		'-f', 'x11grab',
		'-s', '{}x{}'.format(geometry['width'], geometry['height']),
		'-i', '{screen}+{x},{y}'.format(
			screen=screen_id,
			x=geometry['x'],
			y=geometry['y'],
		),
		# Output options
		'-vframes', '1',
		'-y', # Overwrite without asking
		filename,
	]
	return subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	
def stream(screen_id, geometry, fps, filename):
	"""
		Streams an area of a screen to a v4l2 device node
		
		`screen_id` should be the full name (including display name)
		of the X11 screen to capture. Eg: ":0.0".
		`geometry` should be a dict-like object providing values
		for x, y, width, and height.
		`fps` should be the desired frames-per-second of the stream.
		`filename` is the filesystem location where the v4l2 camera
		device node is located.
		
		The return value is a subprocess.Popen instance.
		
		NB. All output of the ffmpeg process is devnull'ed.
	"""
	cmd = [
		'ffmpeg',
		# Need input
		'-f', 'x11grab',
		'-r', fps,
		'-s', '{}x{}'.format(geometry['width'], geometry['height']),
		'-i', '{screen}+{x},{y}'.format(
			screen=screen_id,
			x=geometry['x'],
			y=geometry['y'],
		),
		# Output control
		'-vcodec', 'rawvideo',
		'-pix_fmt', 'yuv420p',
		'-threads', '0',
		'-f', 'v4l2', filename
	]
	return subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	

def capture_window(window, filename):
	"""
		Take a screenshot of the given X `window`
	"""
	return screenshot(
		screen_id=window.screen.full_id,
		geometry=window.get_abs_geometry(),
		filename=filename,
	)
	
def stream_window(window, fps, filename):
	"""
		Stream the given X `window`
	"""
	return stream(
		screen_id=window.screen.full_id,
		geometry=window.get_abs_geometry(),
		fps=fps,
		filename=filename,
	)
	
