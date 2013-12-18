import urllib2
from time import sleep
import settings
from Urllib2BaseHandlers import ThrottlingProcessor, CacheHandler
from Urllib2BaseHandlers import get_or_create_url
import traceback
from models import Access
# from models import Url

#TODO: fix up error logging

def cache(*args, **kwargs):
    url = args[0]
    postdata = False
    if 'data' in kwargs:
        postdata = kwargs['data']
        del kwargs['data']
    for _ in range(settings.RETRY_COUNT + 1):
        try:
            opener = urllib2.build_opener(CacheHandler(**kwargs))
            if postdata:
                return opener.open(url, postdata)
            else:
                return opener.open(url)
        except:
            # log error
            traceback.print_exc()
            print "RETRYING cache"
            sleep(settings.RETRY_PAUSE)
            continue
        raise
    

def throttle(*args, **kwargs):
    url = args[0]
    postdata = False
    if 'data' in kwargs:
        postdata = kwargs['data']
        del kwargs['data']
    for _ in range(settings.RETRY_COUNT + 1):
        try:
            opener = urllib2.build_opener(ThrottlingProcessor(**kwargs))
            if postdata:
                return opener.open(url, postdata)
            else:
                return opener.open(url)
        except:
            # log error
            traceback.print_exc()
            print "RETRYING throttle"
            sleep(settings.RETRY_PAUSE)
            continue
        raise


def cache_and_throttle(*args, **kwargs):
    url = args[0]
    delay = False
    postdata = False
    if 'delay' in kwargs:
        delay = kwargs['delay']
        del kwargs['delay']
    if 'data' in kwargs:
        postdata = kwargs['data']
        del kwargs['data']
    """ create Access model instance here so that both cache and throttle
        will use the same instance (db row)"""
    kwargs['accessed'] = Access(url=get_or_create_url(url, data=postdata)[0])
    kwargs['accessed'].throttle = True
    for _ in range(settings.RETRY_COUNT + 1):
        try:
            if delay:
                opener = urllib2.build_opener(CacheHandler(**kwargs),
                                              ThrottlingProcessor(delay,
                                                                  accessed=kwargs['accessed']))
            else:
                opener = urllib2.build_opener(CacheHandler(**kwargs),
                                              ThrottlingProcessor(accessed=kwargs['accessed']))
            if postdata:
                return opener.open(url, postdata)
            else:
                return opener.open(url)
        except:
            # log error
            traceback.print_exc()
            print "RETRYING cache_and_throttle"
            sleep(settings.RETRY_PAUSE)
            continue
        raise