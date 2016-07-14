# -*- coding: utf8 -*-
import os


def check_and_create_filepath(filepath):
	""" Creates intermediate directories to given path to file

	Args:
		filepath (string): relative path to file
	"""
	if not os.path.exists(os.path.dirname(filepath)):
		try:
			os.makedirs(os.path.dirname(filepath))
		except Exception as e:
			print 'failed to check & create filepath: %s' % filepath
			print e