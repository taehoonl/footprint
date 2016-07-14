import collector
import feeder
import logger
from config import config


if __name__ == '__main__':
	l = logger.Logger()
	c = collector.Collector(l)
	c.start()
	
