#!/usr/bin/env python3
"""
	Main script for the x112v4l2 application GUI
"""
from x112v4l2.gtk import ui


if __name__ == '__main__':
	window = ui.MainUI()
	window.run()
	
