'''
Created on May 28, 2013

@author: Drew
'''
import time
import os
import urllib2
import httplib
import StringIO
import datetime
import gzip
import django
import settings
import random
import errno
from hashlib import md5
from django.utils import timezone
from django.db.models import Q
from django.db import transaction
from random import sample
from string import digits, ascii_uppercase, ascii_lowercase
from os import path
from urlparse import urlparse, parse_qsl
from models import Cache
from models import Throttle
from models import Access
from models import PostData
from models import Url

__version__ = (0,3)
__author__ = "Staffan Malmgren <staffan@tomtebo.org>"
__author__ = "Drew Thomson"

""" would have been cool to put this in the model or at least in
    django somewhere"""
def get_or_create_url(urlstr, data=False):
    urls = Url.objects.filter(url=urlstr)
    if data:
        data = parse_qsl(data, keep_blank_values=True)
        postnum = len(data)
    else:
        postnum = 0
    for url in urls:
        postdatas = PostData.objects.filter(url=url)
        if len(postdatas) != postnum:
            continue
        postdataequal = True
        if data:
            for pair in data:
                for postdata in postdatas:
                    if postdata.key == pair[0] and postdata.value == pair[1]:
                        break
                else:
                    postdataequal = False
                    break
                continue
        if postdataequal:
            return (url, False)
    # save url and postdata
    dburl = Url.objects.create(url=urlstr)
    if data:
        for pair in data:
            PostData.objects.create(url=dburl, key=pair[0], value=pair[1])
    return (dburl, True)

        

class ThrottlingProcessor(urllib2.BaseHandler):
    """Prevents overloading the remote web server by delaying requests.

    Causes subsequent requests to the same web server to be delayed
    a specific amount of seconds. The first request to the server
    always gets made immediately"""
    
    def __init__(self, delay=settings.DEFAULT_THROTTLE_DELAY, accessed=False):
        """The number of seconds to wait between subsequent requests"""
        try:
            int(delay)
        except TypeError:
            if len(delay) >= 2:
                if delay[0] < delay[1]:
                    delay = random.randrange(delay[0], delay[1])
                else:
                    delay = random.randrange(delay[1], delay[0])
        self.delay = delay
        self.throttle = False
        self.throttled = False
        self.throttlecount = 0
        self.accessed = accessed
        self.urlmodel = False
    
    def default_open(self,request):
        utcnow = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
        url = request.get_full_url()
        parsed = urlparse(url)
        netloc = parsed.netloc
        if request.has_data():
            data = request.get_data()
        else:
            data = False
        self.urlmodel = get_or_create_url(url, data=data)[0]
        self.throttle = Throttle(url=self.urlmodel)
        delaytime = utcnow - datetime.timedelta(seconds=self.delay)
        
        def myatomic(netloc):
            lastrun = Throttle.objects.filter(url__netloc=netloc,
                                              runat__gte=delaytime,
                                     ).order_by('-runat')
            if lastrun:
                lastrun = lastrun[0]
                runat = lastrun.runat + datetime.timedelta(seconds=self.delay)
            else:
                # netloc not found, run now
                runat = utcnow
            self.throttle.runat = runat
            self.throttle.save()
            return runat

        if django.VERSION[0] >= 2 or (django.VERSION[0] == 1 and django.VERSION[1] >= 6):
            with transaction.atomic():
                runat = myatomic(netloc)
        else:
            runat = myatomic(netloc)
        
        s = runat - utcnow 
        if s.seconds > 0:
            self.throttlecount = s.seconds
            self.throttled = True
            self.throttle.status = 'W'
            self.throttle.save()
            time.sleep(s.seconds)
        utcnow = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
        self.throttle.status = 'R'
        self.throttle.save()
        return None

    def http_response(self,request,response):
        if self.throttle:
            if not self.accessed:
                self.accessed = Access(url=self.urlmodel)
            utcnow = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
            self.accessed.accessed = utcnow
            self.accessed.returncode = response.code
            self.accessed.throttle = True
            self.accessed.throttleseconds = self.throttlecount
            self.throttle.completed = utcnow
            self.throttle.status = 'C'
            self.accessed.save()
            self.throttle.save()
        if self.throttled:
            response.info().addheader("x-throttling", "%s seconds" % 
                                      self.delay)
        return response


class CacheHandler(urllib2.BaseHandler):
    """Stores responses in a persistent on-disk cache.

    If a subsequent request is made for the same URL, the stored
    response is returned, saving time, resources and bandwidth"""
    def __init__(self,
                 location=settings.CACHE_DIRECTORY,
                 expires=settings.EXPIRES,
                 overwrite=settings.OVERWRITE,
                 compression=settings.COMPRESSION,
                 accessed=False):
        
        """The location of the cache directory"""
        self.location = location
        try:
            os.makedirs(self.location)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise
        
        """Cache expiration datetime"""
        self.expires = expires
        if expires:
            try:
                int(expires)
            except:
                if len(expires) >= 2:
                    if expires[0] < expires[1]:
                        expires = random.randrange(expires[0], expires[1])
                    else:
                        expires = random.randrange(expires[1], expires[0])
            utcnow = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
            self.expires = utcnow + datetime.timedelta(seconds=expires)
        
        """Cache overwrite flag"""
        self.overwrite = overwrite
        
        """Compression type"""
        self.compression = compression
        
        self.accessed = accessed
        
            
    def default_open(self,request):
        if request.has_data():
            data = request.get_data()
        else:
            data = False
        if ((not self.overwrite) and
             CachedResponse.ExistsInCache(request.get_full_url(), data)):
            return CachedResponse(self.location, 
                                  request, 
                                  setCacheHeader=True)    
        else:
            return None # let the next handler try to handle the request

    def http_response(self, request, response):
        if not self.accessed:
            if request.has_data():
                data = request.get_data()
            else:
                data = False
            self.accessed = Access(url=get_or_create_url(request.get_full_url(), data=data)[0])
        if not self.accessed.accessed:
            self.accessed.accessed = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
        self.accessed.cache = True
        if 'x-cache' not in response.info():
            CachedResponse.StoreInCache(self.location, 
                                        request, 
                                        response,
                                        self.expires,
                                        self.compression)
            if not self.accessed.returncode:
                self.accessed.returncode = response.code
            self.accessed.save()
            return CachedResponse(self.location, 
                                  request, 
                                  setCacheHeader=False)
        else:
            self.accessed.fromweb = False
            self.accessed.save()
            return CachedResponse(self.location, 
                                  request, 
                                  setCacheHeader=True)


class CachedResponse(StringIO.StringIO):
    """An urllib2.response-like object for cached responses.

    To determine whether a response is cached or coming directly from
    the network, check the x-cache header rather than the object type."""
    
    def ExistsInCache(url, data=False):
        utcnow = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
        myhash = md5(url).hexdigest()
        cache = Cache.objects.filter(url__md5=myhash)
        cache = cache.filter(Q(expires__gte=utcnow) | Q(expires__isnull=True))
        for c in cache:
            if c.url.url == url:
                poststr = {}
                if not data:
                    postnum = 0
                else:
                    poststr = parse_qsl(data, keep_blank_values=True)
                    postnum = len(poststr)
                dbpostdata = PostData.objects.filter(url=c.url)
                if postnum != len(dbpostdata):
                    continue
                postdataequal = True
                for pair in poststr:
                    for pd in dbpostdata:
                        if pd.key == pair[0] and pd.value == pair[1]:
                            break
                    else:
                        postdataequal = False
                        break
                    continue
                if postdataequal:
                    return c
        return False
    ExistsInCache = staticmethod(ExistsInCache)

    def StoreInCache(location, request, response, expires=False, compression=False):
        if request.has_data():
            data = request.get_data()
        else:
            data = False
        urlmodel = get_or_create_url(request.get_full_url(), data=data)[0]
        cache = Cache.objects.get_or_create(url=urlmodel)[0]
        
        if expires:
            cache.expires = expires
        else:
            cache.expires = None
        
        try:
            os.makedirs(location)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        headerfile = False
        bodyfile = False
        while not headerfile or not bodyfile:
            f = CachedResponse.RandFname(location)
            hfname = f + ".header"
            bfname = f + ".body"
            if compression:
                if compression == 'gzip':
                    hfname += '.gz'
                    bfname += '.gz'
            try:
                if compression:
                    # if windows we need to add: os.O_BINARY
                    try:
                        hf = os.open(os.path.join(location, hfname), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_BINARY)
                        bf = os.open(os.path.join(location, bfname), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_BINARY)
                    except AttributeError:
                        hf = os.open(os.path.join(location, hfname), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                        bf = os.open(os.path.join(location, bfname), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                        pass
                else:
                    hf = os.open(os.path.join(location, hfname), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
                    bf = os.open(os.path.join(location, bfname), os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            except OSError:
                try:
                    os.close(hf)
                    os.remove(os.path.join(location, hfname))
                except OSError:
                    pass
                try:
                    os.close(bf)
                    os.remove(os.path.join(location, bfname))
                except OSError:
                    pass    
                pass
            else:
                if compression:
                    headerfile = os.fdopen(hf, "wb")
                    bodyfile = os.fdopen(bf, "wb")
                else:
                    headerfile = os.fdopen(hf, "w")
                    bodyfile = os.fdopen(bf, "w")
                cache.directory = location
                cache.filename = f
        if compression:
            if compression == 'gzip':
                headerfile = gzip.GzipFile(fileobj=headerfile, mode='wb')
                bodyfile = gzip.GzipFile(fileobj=bodyfile, mode='wb')
            cache.compression = compression
        header = str(response.info())
        headerfile.write(header)
        headerfile.close()
        bodyfile.write(response.read())
        bodyfile.close()
        cache.save()
    StoreInCache = staticmethod(StoreInCache)
    
    def RandFname(location, length=32):
        chars = ascii_lowercase + ascii_uppercase + digits
        fname = "".join(sample(chars, length))
        return fname if not path.exists(os.path.join(location, fname)) else CachedResponse.RandFname(location, length)
    RandFname = staticmethod(RandFname)

    def CleanDBCache():
        utcnow = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
        oldcacheqs = Cache.objects.filter(expires__lte=utcnow)
        for oldcache in oldcacheqs:
            oldcache.delete()
    CleanDBCache = staticmethod(CleanDBCache)

    def __init__(self, location, request, setCacheHeader=True):
        self.location = location
        headerbuf = ''
        url = request.get_full_url()
        if request.has_data:
            cache = self.ExistsInCache(url, request.get_data())
        else:
            cache = self.ExistsInCache(url)
        if cache:
            bf = cache.filename + '.body'
            hf = cache.filename + '.header'
            if cache.compression == 'gzip':
                bodyfile = gzip.open(os.path.join(location, bf + '.gz'))
                headerfile = gzip.open(os.path.join(location, hf + '.gz'))
            else:
                bodyfile = open(os.path.join(location, bf))
                headerfile = open(os.path.join(location, hf))
            StringIO.StringIO.__init__(self, bodyfile.read())                
            headerbuf = headerfile.read()
        else:
            StringIO.StringIO.__init__(self)
        self.url     = url
        self.code    = 200
        self.msg     = "OK"
        if setCacheHeader:
            headerbuf += "x-cache: %s\r\n" % (self.location)
        self.header = httplib.HTTPMessage(StringIO.StringIO(headerbuf))

    def info(self):
        return self.header
    
    def geturl(self):
        return self.url
