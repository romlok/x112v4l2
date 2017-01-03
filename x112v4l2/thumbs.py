"""
	Functionality for dealing with our thumbnails
"""
import os
import tempfile
import shutil

CACHE_PATH = os.path.join(tempfile.gettempdir(), 'x112v4l2', 'thumbs')


def mkdir():
	""" Create the directory in which we store thumbnails """
	return os.makedirs(CACHE_PATH, exist_ok=True)
	
def rmdir():
	""" Remove the temporary thumbs and directory """
	return shutil.rmtree(CACHE_PATH)
	

def create_all():
	"""
		Create thumbnails for all (interesting) X11 windows
		
		Returns a dict of {win_id: filename}
	"""
	return {}
	
