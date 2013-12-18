from django.db import models
import datetime
from hashlib import md5 as md5hash
import os
import glob
import errno
from urlparse import urlparse
from django.utils import timezone

# Create your models here.

class Url(models.Model):
    url = models.URLField(max_length=255)
    netloc = models.CharField(max_length=100, editable=False)
    md5 = models.CharField(db_index=True, max_length=32, blank=True, editable=False)
    created = models.DateTimeField(null=True, editable=False)
    
    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
        self.md5 = md5hash(self.url).hexdigest()
        parsed = urlparse(self.url)
        self.netloc = parsed.netloc
        super(Url, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return self.url
        
        
class PostData(models.Model):
    url = models.ForeignKey(Url, db_index=True)
    key = models.CharField(max_length=240)
    value = models.CharField(max_length=240)
    

class Cache(models.Model):
    url = models.ForeignKey(Url, db_index=True)
    # TODO: change to FilePathField?
    directory = models.CharField(max_length=512, blank=True, null=True)
    filename = models.CharField(max_length=32,
                              blank=True,
                              null=True,
                              editable=False)
    # compression
    GZIP = 'gzip'
    COMPRESSION_CHOICES = {
        (GZIP, 'gzip'),
    }
    compression = models.CharField(max_length=4, blank=True, null=True,
                                   choices=COMPRESSION_CHOICES)
    expires = models.DateTimeField(db_index=True, blank=True, null=True)
    updated = models.DateTimeField(null=True, editable=False)
    created = models.DateTimeField(null=True, editable=False)
    
    def save(self, *args, **kwargs):
        utcnow = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
        if not self.created:
            self.created = utcnow
        self.updated = utcnow
        super(Cache, self).save(*args, **kwargs)
        
    
    def delete(self):
        try:
            for f in glob.glob(os.path.join(self.directory, self.filename) + ".*"):
                os.remove(f)
        except OSError, e:
            if e.errno == errno.ENOENT:  # errno.ENOENT = no such file or directory
                super(Cache, self).delete()
            else:
                print "log that file could not be deleted"
                pass
        except TypeError:
            pass
        else:
            super(Cache, self).delete()
     
    def __unicode__(self):
        return self.url.url
    
    
class Throttle(models.Model):
    url = models.ForeignKey(Url, db_index=True)
    # status
    STATUS_CHOICES = {
        ('R', 'running'),
        ('C', 'completed'),
        ('W', 'waiting'),
    }
    status = models.CharField(max_length=1, blank=True, null=True,
                                   choices=STATUS_CHOICES)
    created = models.DateTimeField(null=True, editable=False)
    runat = models.DateTimeField()
    completed = models.DateTimeField(null=True, editable=False)
    
    def save(self, *args, **kwargs):
        if not self.created:
            self.created = datetime.datetime.utcnow().replace(tzinfo=timezone.utc)
        super(Throttle, self).save(*args, **kwargs)
        
    def __unicode__(self):
        return self.url.url


class Access(models.Model):
    url = models.ForeignKey(Url, db_index=True)
    cache = models.BooleanField(default=False)
    throttle = models.BooleanField(default=False)
    throttleseconds = models.IntegerField(default=0)
    accessed = models.DateTimeField(db_index=True, editable=False)
    fromweb = models.BooleanField(default=True)
    returncode = models.SmallIntegerField(null=True)
    
    def __unicode__(self):
        return self.url.url
    
    class Meta:
        verbose_name_plural = "accesses"
