#!/bin/sh
#
# Remove and reinstall the v4l2loopback kernel driver
#
# All arguments to this script are passed to modprobe
# when the module is reinstalled.
#
set -e

/sbin/modprobe -r v4l2loopback
/sbin/modprobe v4l2loopback "$@"

# The very first time the module is installed after boot,
# it appears that the permissions on /dev/video0 may not
# be set correctly until a short time has passed.
if [ -r /dev/video0 ]; then
	sleep 0.5
fi
