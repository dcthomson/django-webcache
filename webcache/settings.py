import webcache
import os

CACHE_DIRECTORY           = os.path.join(os.path.abspath((webcache.__path__)[0]), 'cache')
DEFAULT_THROTTLE_DELAY    = 5           # can also be a tuple range
#DEFAULT_THROTTLE_DELAY   = (60, 120)   # random delay between 1 and 2 minutes 
COMPRESSION               = False
EXPIRES                   = False       # ex. 60 * 60 * 24 * 7 = 1 week
OVERWRITE                 = False
RETRY_COUNT               = 2
RETRY_PAUSE               = 60 * 15     # 15 minutes