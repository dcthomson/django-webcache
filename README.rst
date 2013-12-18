django-webcache
===============

django web caching app that supports throttling, expiration and
compression.

This uses code from django 1.6 for throttling transactions. If you
are using django 1.5 or lower you might get lucky enough to hit the race
condition if there are concurrent requests. In this event, it will just
skip the throttle on that lookup.

Usage
-----

All variables **except url** have defaults that can be overridden in the
settings.py file

.. code-block:: python

   from urlopen import cache
   from urlopen import throttle
   from urlopen import cache_and_throttle

Cache
-----

.. code-block:: python

   cache(url[, data=postdata][, location="path"][, expires=n |, expires=(n,m)][, overwrite=False][, compression=False])
   
+-------------+-------------------------------------+-------------------------------------------------------------------------------------------------------------------------------+
| variable    | type                                | description                                                                                                                   |
+=============+=====================================+===============================================================================================================================+
| url         | string                              | The url to retrieve / cache                                                                                                   |
+-------------+-------------------------------------+-------------------------------------------------------------------------------------------------------------------------------+
| data        | string                              | POST data string                                                                                                              |
+-------------+-------------------------------------+-------------------------------------------------------------------------------------------------------------------------------+
| location    | string                              | The directory to save the cached pages to                                                                                     |
+-------------+-------------------------------------+-------------------------------------------------------------------------------------------------------------------------------+
| expires     | integer or 2 item tuple of integers | Number of seconds until the cache expires, or a range from which a random number of seconds will be chosen for the expiration |
+-------------+-------------------------------------+-------------------------------------------------------------------------------------------------------------------------------+
| overwrite   | boolean                             | Retrieve url and cache even if cache already exists                                                                           |
+-------------+-------------------------------------+-------------------------------------------------------------------------------------------------------------------------------+
| compression | string                              | Compress the cache                                                                                                            |
+-------------+-------------------------------------+-------------------------------------------------------------------------------------------------------------------------------+

Throttle
--------

.. code-block:: python

   throttle(url[, data=postdata][, delay=n |, delay=(n,m)])

+---------------+---------------------------------------+-------------------------------------------------------------------------------------------------+
| variable      | type                                  | description                                                                                     |
+===============+=======================================+=================================================================================================+
| url           | string                                | The url to retrieve / cache                                                                     |
+---------------+---------------------------------------+-------------------------------------------------------------------------------------------------+
| data          | string                                | POST data string                                                                                |
+---------------+---------------------------------------+-------------------------------------------------------------------------------------------------+
| delay         | integer or 2 item tuple of integers   | Number of seconds to throttle, or a range from which a random number will be chosen to throttle |
+---------------+---------------------------------------+-------------------------------------------------------------------------------------------------+


Cache and Throttle
------------------

.. code-block:: python

   cache_and_throttle(url[, data=postdata][, location="path"][, expires=n |, expires=(n,m)][, overwrite=False][, compression=False][, delay=n |, delay=(n,m)])

+---------------+---------------------------------------+---------------------------------------------------------------------------------------------------------------------------------+
| variable      | type                                  | description                                                                                                                     |
+===============+=======================================+=================================================================================================================================+
| url           | string                                | The url to retrieve / cache                                                                                                     |
+---------------+---------------------------------------+---------------------------------------------------------------------------------------------------------------------------------+
| data          | string                                | POST data string                                                                                                                |
+---------------+---------------------------------------+---------------------------------------------------------------------------------------------------------------------------------+
| location      | string                                | The directory to save the cached pages to                                                                                       |
+---------------+---------------------------------------+---------------------------------------------------------------------------------------------------------------------------------+
| expires       | integer or 2 item tuple of integers   | Number of seconds until the cache expires, or a range from which a random number of seconds will be chosen for the expiration   |
+---------------+---------------------------------------+---------------------------------------------------------------------------------------------------------------------------------+
| overwrite     | boolean                               | Retrieve url and cache even if cache already exists                                                                             |
+---------------+---------------------------------------+---------------------------------------------------------------------------------------------------------------------------------+
| compression   | string                                | Compress the cache                                                                                                              |
+---------------+---------------------------------------+---------------------------------------------------------------------------------------------------------------------------------+
| delay         | integer or 2 item tuple of integers   | Number of seconds to throttle, or a range from which a random number of seconds will be chosen to throttle                      |
+---------------+---------------------------------------+---------------------------------------------------------------------------------------------------------------------------------+

Examples
--------

.. code-block:: python

    import webcache.urlopen

    pyurl = "http://www.python.org/"

    """just caching"""
    response = urlopen.cache(pyurl)

    """cache and override default cache file directory"""
    response = urlopen.cache(pyurl, location=self.path)

    """cache and override default expiration time in seconds"""
    response = urlopen.cache(pyurl, expires=10)

    """cache and override default overwrite setting
       will overwrite old cache even if not expired"""
    response = urlopen.cache(pyurl, overwrite=True)

    """cache and override default compression with gzip compression"""
    response = urlopen.cache(pyurl, compression='gzip')

    """throttle will wait 10 seconds since the previous web page retrieval of something
       from the same site. For example http://www.python.org/about will throttle if
       another lookup of http://www.python.org exists in the last 10 seconds"""
    response = urlopen.throttle(pyurl, delay=10)

    """throttle using random range"""
    response = urlopen.throttle(pyurl, delay=(60, 120))

    """combination of cache and throttle"""
    response = urlopen.cache_and_throttle(pyurl, location=self.path, delay=10)

Developed By
============

-  Drew Thomson - drooby@gmail.com

Special Thanks
==============

-  Staffan Malmgren
-  His original code:
   http://code.activestate.com/recipes/491261-caching-and-throttling-for-urllib2/

License
=======

The MIT License (MIT)

Copyright (c) 2013 Drew Thomson

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
