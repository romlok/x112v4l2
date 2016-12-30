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
