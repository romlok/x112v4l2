"""
	Gubbins for interfacing with ffmpeg
"""
import math
import subprocess


def get_version():
	"""
		Get the version of ffmpeg which is installed
		
		Returns None if ffmpeg is not available
	"""
	proc = subprocess.Popen(
		['ffmpeg', '-version'],
		stdout=subprocess.PIPE,
		stderr=subprocess.DEVNULL,
	)
	if proc.wait():
		return None
	
	# Try to parse out the version number from the first line
	words = proc.stdout.readline().decode('utf8').split(' ')
	if words[1] == 'version':
		return words[2]
	
	# Uhh, dunno
	return '<Unknown>'
	

def compile_command(
	source_screen, source_x, source_y, source_width, source_height,
	output_filename,
	output_width=None,
	output_height=None,
	fps=0,
	scale=True,
	pad=True,
):
	"""
		Build an ffmpeg command suitable for the given arguments
		
		The return value is an iterable of command tokens, suitable
		for passing to subprocess.Popen().
		
		The `source_screen` should be either an X11 Screen instance,
		or the string full ID of a screen, eg. ":0.0".
		
		To take a single screenshot of the given source, provide an
		`fps` of 0.
		
		The source will be scaled to fit the output dimensions by
		default. If this is not desired, set the `scale` parameter
		to False.
		
		By default, pillar/letterbox padding is added to the scaled
		input. Set the `pad` parameter to False to disable this,
		and output an image/video using the source aspect ratio.
	"""
	# Validation/defaulting
	if not output_width:
		output_width = source_width
	if not output_height:
		output_height = source_height
	source_x = int(source_x)
	source_y = int(source_y)
	source_width = int(source_width)
	source_height = int(source_height)
	output_width = int(output_width)
	output_height = int(output_height)
	fps = int(fps)
	
	input_args = [
		'ffmpeg',
		'-loglevel', 'error',
		# Input options
		'-f', 'x11grab',
		# NB. High framerate for screenshots, so we're not left waiting
		'-framerate', str(fps if fps else 120),
		'-s', '{w}x{h}'.format(w=source_width, h=source_height),
		'-i', '{screen}+{x},{y}'.format(
			screen=getattr(source_screen, 'full_id', source_screen),
			x=source_x,
			y=source_y,
		),
	]
	
	# Filters (eg. scaling, letterboxing, etc.)
	filter_args = []
	if output_width != source_width or output_height != source_height:
		source_aspect = source_width / source_height
		output_aspect = output_width / output_height
		if scale and output_width != source_width and output_height != source_height:
			# Scale the video
			filter_args.append(
				'scale=width={w}:height={h}:force_original_aspect_ratio=decrease'.format(
					w=output_width,
					h=output_height,
				)
			)
		if pad and source_aspect != output_aspect:
			# Apply letterboxing
			filter_args.append(
				'pad=width={w}:height={h}:x=(ow-iw)/2:y=(oh-ih)/2'.format(
					w=output_width,
					h=output_height,
				)
			)
		
	if filter_args:
		filter_args = ['-vf', ', '.join(filter_args)]
	
	# Output
	output_args = []
	if not fps:
		# One-time screenshot
		output_args += [
			'-vframes', '1',
			'-y',
			output_filename,
		]
	else:
		# Persistent stream
		output_args += [
			'-vcodec', 'rawvideo',
			'-pix_fmt', 'yuv420p',
			'-threads', '0',
			'-f', 'v4l2',
			output_filename,
		]
	
	return input_args + filter_args + output_args
	

def screenshot(screen_id, geometry, filename, scale=None):
	"""
		Creates a screenshot image from the X screen
		
		`screen_id` should be the full name (including display name)
		of the X11 screen to capture. Eg: ":0.0".
		`geometry` should be a dict-like object providing values
		for x, y, width, and height.
		`filename` is the filesystem location where the
		screenshot will be written.
		If `scale` is supplied, it should be a dictionary of values
		understood by ffmpeg's "-vf scale=..." option.
		
		The return value is a subprocess.Popen instance.
		
		NB. All output of the ffmpeg process is devnull'ed.
	"""
	cmd = compile_command(
		source_screen=screen_id,
		source_x=geometry['x'],
		source_y=geometry['y'],
		source_width=geometry['width'],
		source_height=geometry['height'],
		output_filename=filename,
		output_width=scale['w'] if scale else None,
		output_height=scale['h'] if scale else None,
		fps=0,
		pad=False,
	)
	return subprocess.Popen(
		cmd,
		stdin=subprocess.DEVNULL,
		stdout=subprocess.DEVNULL,
	)
	
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
	cmd = compile_command(
		source_screen=screen_id,
		source_x=geometry['x'],
		source_y=geometry['y'],
		source_width=geometry['width'],
		source_height=geometry['height'],
		output_filename=filename,
		# Output video dimensions should be multiples of 2
		output_width=math.ceil(geometry['width'] / 2) * 2,
		output_height=math.ceil(geometry['height'] / 2) * 2,
		fps=fps,
		scale=False,
	)
	return subprocess.Popen(
		cmd,
		stdin=subprocess.DEVNULL,
		stdout=subprocess.DEVNULL,
	)
	

def capture_window(window, filename, **kwargs):
	"""
		Take a screenshot of the given X `window`
	"""
	return screenshot(
		screen_id=window.screen.full_id,
		geometry=window.get_abs_geometry(),
		filename=filename,
		**kwargs
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
	
