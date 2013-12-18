'''
Created on May 17, 2013

@author: Drew
'''
from django.contrib import admin
from models import Url
from models import Cache
from models import Throttle
from models import Access

class UrlAdmin(admin.ModelAdmin):
    list_display = ('url', 'netloc', 'md5', 'created')
    ordering = ['url']
admin.site.register(Url, UrlAdmin)

class CacheAdmin(admin.ModelAdmin):
    list_display = ('url', 'directory', 'filename', 'compression',
                    'expires', 'created', 'updated')
    raw_id_fields = ('url',)
    ordering = ['-updated']
admin.site.register(Cache, CacheAdmin)

class ThrottleAdmin(admin.ModelAdmin):
    list_display = ('url', 'status', 'created', 'runat', 'completed')
    raw_id_fields = ('url',)
    ordering = ['-created']
admin.site.register(Throttle, ThrottleAdmin)

class AccessAdmin(admin.ModelAdmin):
    list_display = ('url', 'cache', 'throttle', 'accessed', 'throttleseconds',
                    'fromweb', 'returncode')
    raw_id_fields = ('url',)
    date_hierarchy = 'accessed'
    ordering = ['-accessed']
admin.site.register(Access, AccessAdmin)