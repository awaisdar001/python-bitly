#!/usr/bin/python2.4
#
# Copyright 2009 Empeeric LTD. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.utils import simplejson
import urllib,urllib2
import urlparse
import string

BITLY_BASE_URL = "http://api.bit.ly/"
BITLY_API_VERSION = "2.0.1"

VERBS_PARAM = { 
         'shorten':'longUrl',               
         'expand':'shortUrl', 
         'info':'shortUrl',
         'stats':'shortUrl',
         'errors':'',
}

class BitlyError(Exception):
  '''Base class for bitly errors'''
  
  @property
  def message(self):
    '''Returns the first argument used to construct this error.'''
    return self.args[0]

class Api():
    """ API class for bit.ly """
    def __init__(self, login, apikey):
        self.login = login
        self.apikey = apikey
        self._urllib = urllib2
        
    def shorten(self,longURL):
        """ Given a long url, returns a shorter one.  """
        if not longURL.startswith("http"):
            longURL = "http://" + longURL
            
        request = self._getURL("shorten",longURL)
        result = self._fetchUrl(request)
        json = simplejson.loads(result)
        self._CheckForError(json)
        if json['results'][longURL]['shortKeywordUrl'] == "":
            return json['results'][longURL]['shortUrl']
        else:
            return json['results'][longURL]['shortKeywordUrl']

    def expand(self,shortURL):
        """ Given a bit.ly url or hash, return long source url """
        request = self._getURL("expand",shortURL)
        result = self._fetchUrl(request)
        json = simplejson.loads(result)
        self._CheckForError(json)
        return json['results'][string.split(shortURL, '/')[-1]]['longUrl']

    def info(self,shortURL):
        """ 
        Given a bit.ly url or hash, 
        return information about that page, 
        such as the long source url
        """
        request = self._getURL("info",shortURL)
        result = self._fetchUrl(request)
        json = simplejson.loads(result)
        self._CheckForError(json)
        return json['results'][string.split(shortURL, '/')[-1]]

    def stats(self,shortURL):
        """ Given a bit.ly url or hash, return traffic and referrer data.  """
        request = self._getURL("stats",shortURL)
        result = self._fetchUrl(request)
        json = simplejson.loads(result)
        self._CheckForError(json)
        return Stats.NewFromJsonDict(json['results'])

    def errors(self):
        """ Get a list of bit.ly API error codes. """
        request = self._getURL("errors","")
        result = self._fetchUrl(request)
        json = simplejson.loads(result)
        self._CheckForError(json)
        return json['results']
        
    def setUrllib(self, urllib):
        '''Override the default urllib implementation.
    
        Args:
          urllib: an instance that supports the same API as the urllib2 module
        '''
        self._urllib = urllib
    
    def _getURL(self,verb,patamVal):   
        params = {}
        params.update({
          'version': BITLY_API_VERSION,
          'format': 'json',
          'login': self.login,
          'apiKey': self.apikey,
          })
        
        verbParam = VERBS_PARAM[verb]   
        if verbParam:
            params.update({ verbParam: patamVal, })
   
        encoded_params = urllib.urlencode(params)
        return "%s%s?%s" % (BITLY_BASE_URL,verb,encoded_params)
       
    def _fetchUrl(self,url):
        '''Fetch a URL
    
        Args:
          url: The URL to retrieve
    
        Returns:
          A string containing the body of the response.
        '''
    
        # Open and return the URL 
        url_data = self._urllib.urlopen(url).read()
        return url_data    

    def _CheckForError(self, data):
        """Raises a BitlyError if bitly returns an error message.
    
        Args:
          data: A python dict created from the bitly json response
        Raises:
          BitlyError wrapping the bitly error message if one exists.
        """
        # bitly errors are relatively unlikely, so it is faster
        # to check first, rather than try and catch the exception
        if 'ERROR' in data or data['statusCode'] == 'ERROR':
            raise BitlyError, data['errorMessage']
       
class Stats(object):
    '''A class representing the Statistics returned by the bitly api.
    
    The Stats structure exposes the following properties:
    status.user_clicks # read only
    status.clicks # read only
    '''
    
    def __init__(self,user_clicks=None,total_clicks=None):
        self.user_clicks = user_clicks
        self.total_clicks = total_clicks
    
    @staticmethod
    def NewFromJsonDict(data):
        '''Create a new instance based on a JSON dict.
    
        Args:
          data: A JSON dict, as converted from the JSON in the bitly API
        Returns:
          A bitly.Stats instance
        '''
        return Stats(user_clicks=data.get('userClicks', None),
                      total_clicks=data.get('clicks', None))

        
if __name__ == '__main__':
    testURL="www.google.com"
    a=Api(login="pythonbitly",apikey="R_06871db6b7fd31a4242709acaf1b6648")
    short=a.shorten(testURL)
    print "Short URL = %s" % short
    long=a.expand(short)
    print "Expanded URL = %s" % long
    info=a.info(short)
    print "Info: %s" % info
    stats=a.stats(short)
    print "User clicks %s, total clicks: %s" % (stats.user_clicks,stats.total_clicks)
    errors=a.errors()
    print "Errors: %s" % errors