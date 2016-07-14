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



# def cocatenate_files(filepaths, dst_filepath):
# 	""" 
# 	"""
# 	temp_filepath = 'file.tmp'
# 	try:
# 		with open(temp_filepath, 'w') as temp_file:
# 			try:
# 				for fpath in filepaths:
# 					if not os.path.exists(os.path.dirname(fpath)) or not os.path.exists(fpath):
# 						continue

# 					with open(fpath) as infile:
# 						for line in infile:
# 							temp_file.write(line)
# 			except Exception as e:
# 				print 'failed to concatenate %s' % fpath
# 				print e
# 	except Exception as outer_exception:
# 		print 'failed to concatenate %s -> %s' % (str(filepaths), dst_filepath)
# 		print outer_exception

# 	rename_file(temp_filepath, dst_filepath)