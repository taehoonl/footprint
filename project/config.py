# -*- coding: utf8 -*-

from ConfigParser import SafeConfigParser

class Config():
  """ Retrieves configuration settings using SafeConfigParser """

  def __init__(self, *files):
    self._parser = SafeConfigParser()
    self._parser.optionxform = str  # case sensitive

    found = self._parser.read(files)

    if not found:
      raise ValueError('No config file found')

  def get(self, section, name):
    return self._parser.get(section, name)

# initialize
config = Config('main.ini')