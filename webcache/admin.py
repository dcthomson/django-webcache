'''
Created on May 17, 2013

@author: Drew
'''
import urllib
from django.contrib import admin
from django import forms
from models import Url
from models import Cache
from models import Throttle
from models import Access
from models import PostData

class UrlAdmin(admin.ModelAdmin):
    list_display = ('url', 'postdata', 'netloc', 'md5', 'created')
    
    def postdata(self, obj):
        data = PostData.objects.filter(url=obj)
        postdict = {}
        for pd in data:
            postdict[pd.key] = pd.value
        return urllib.urlencode(postdict)
    
    ordering = ['url']
admin.site.register(Url, UrlAdmin)

class PostDataAdmin(admin.ModelAdmin):
    list_display = ('url', 'key', 'value')
    raw_id_fields = ('url',)
    ordering = ['url', 'key']
    
    # show textfield instead of textarea for key and value
    def formfield_for_dbfield(self, db_field, **kwargs):
        formfield = super(PostDataAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'key' or db_field.name == 'value':
            formfield.widget = forms.TextInput(attrs=formfield.widget.attrs)
        return formfield
admin.site.register(PostData, PostDataAdmin)

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