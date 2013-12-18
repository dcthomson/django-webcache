from django.utils import unittest
import settings
import os
import shutil
import time
import urllib
from urlopen import throttle
from urlopen import cache
from urlopen import cache_and_throttle
from models import Cache
from models import Throttle
from models import Access


class WebCacheTestCase(unittest.TestCase):
    
    url = "http://www.python.org/"
    path = os.path.join(settings.CACHE_DIRECTORY, ".testcache")
    def setUp(self):
        # Clearing cache
        if os.path.exists(self.path):
            for f in os.listdir(self.path):
                os.unlink("%s/%s" % (self.path, f))
        else:
            os.makedirs(self.path)
        
    def tearDown(self):
        # Clearing cache and throttle
        qs = Cache.objects.all()
        for cache in qs:
            cache.delete()
        qs = Throttle.objects.all()
        for throttle in qs:
            throttle.delete()
        if os.path.exists(self.path):
            shutil.rmtree(self.path)
        time.sleep(2)
        
          
    def testCache(self):
        resp = cache(self.url, location=self.path)
        self.assert_('x-cache' not in resp.info())
        resp = cache(self.url, location=self.path)
        self.assert_('x-cache' in resp.info())
          
    def testCacheExpire(self):
        resp = cache(self.url, location=self.path, expires=10)
        self.assert_('x-cache' not in resp.info())
        resp = cache(self.url, location=self.path, expires=10)
        self.assert_('x-cache' in resp.info())
        time.sleep(15)
        resp = cache(self.url, location=self.path, expires=10)
        self.assert_('x-cache' not in resp.info())
           
    def testCacheOverwrite(self):
        cache(self.url, location=self.path)
        age1 = Access.objects.filter(url__url=self.url, 
                                     cache=True).order_by('-accessed')[0].accessed
        time.sleep(2)
        cache(self.url, location=self.path, overwrite=True)
        age2 = Access.objects.filter(url__url=self.url, 
                                     cache=True).order_by('-accessed')[0].accessed
        self.failIf(age1 == age2)
           
    def testCacheCompression(self):
        resp = cache(self.url, location=self.path, compression='gzip')
        self.assert_('x-cache' not in resp.info())
        resp = cache(self.url, location=self.path, compression='gzip')
        self.assert_('x-cache' in resp.info())
        
    def testCachePost(self):
        postdata1 = urllib.urlencode({'test': 'first'})
        postdata2 = urllib.urlencode({'test': 'first', 'testagain': 'second'})
        resp = cache(self.url, location=self.path, data=postdata1)
        self.assert_('x-cache' not in resp.info())
        resp = cache(self.url, location=self.path, data=postdata2)
        self.assert_('x-cache' not in resp.info())
        resp = cache(self.url, location=self.path, data=postdata1)
        self.assert_('x-cache' in resp.info())
         
    def testThrottle(self):
        throttle(self.url, delay=10)
        age1 = Access.objects.filter(url__url=self.url,
                                     throttle=True).order_by('-accessed')[0].accessed
        throttle(self.url, delay=10)
        age2 = Access.objects.filter(url__url=self.url,
                                     throttle=True).order_by('-accessed')[0].accessed
        s = age2 - age1
        self.assert_(s.seconds > 5)
         
        throttle(self.url, delay=10)
        age1 = Access.objects.filter(url__url=self.url,
                                     throttle=True).order_by('-accessed')[0].accessed
        throttle(self.url + "about/", delay=10)
        age2 = Access.objects.filter(url__url=self.url + "about/",
                                     throttle=True).order_by('-accessed')[0].accessed
        s = age2 - age1
        self.assert_(s.seconds > 5)
        
        
    def testCombined(self):
        cache_and_throttle(self.url, location=self.path, delay=10)
        age1 = Access.objects.filter(url__url=self.url).order_by('-accessed')[0].accessed
        resp = cache_and_throttle(self.url, location=self.path, delay=10)
        self.assert_('x-cache' in resp.info())
        age2 = Access.objects.filter(url__url=self.url).order_by('-accessed')[0].accessed
        resp = cache_and_throttle(self.url + "about/", location=self.path, delay=10)
        self.assert_('x-cache' not in resp.info())
        age3 = Access.objects.filter(url__url=self.url + "about/").order_by('-accessed')[0].accessed
        s = age2 - age1
        self.assert_(s.seconds < 10)
        s = age3 - age1
        self.assert_(s.seconds > 5)