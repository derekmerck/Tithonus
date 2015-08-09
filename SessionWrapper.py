import logging
import requests
import json
from bs4 import BeautifulSoup
from posixpath import join as urljoin
from urlparse import urlparse

# Cookie jar for sharing proxy credentials
cookie_jar = {}


class SessionWrapper(requests.Session):
    # Convenience functions for requests.Session

    def __init__(self, **kwargs):
        super(SessionWrapper, self).__init__()

        self.address = kwargs.get('address')
        self.auth = (kwargs.get('user'), kwargs.get('pword'))

        if self.address:
            self.hostname = urlparse(self.address).hostname
        else:
            self.hostname = None

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info('Created session wrapper for %s' % self.hostname)

    def format_url(self, *url):
        # Simple join, but can override in derived classes and still use 'do_' macros
        url = urljoin(self.address, *url)
        return url

    def do_return(self, r):
        # Return dict if possible, but content otherwise (for image data)
        #self.logger.info(r.headers.get('content-type'))
        if r.status_code is not 200:
            self.logger.warn('REST interface returned error %s', r.status_code)
            ret = r.content
            msg = ret
        elif r.headers.get('content-type') == 'application/json':
            try:
                ret = r.json()
                if len(ret) < 50:
                    msg = ret
                else:
                    msg = 'a long json declaration'
            except ValueError, e:
                ret = r.content
                msg = 'a bad json declaration'
        else:
            ret = r.content
            msg = 'Non-json data'
        self.logger.debug('Returning %s', msg)
        return ret

    def do_delete(self, *url, **kwargs):
        params = kwargs.get('params')
        headers = kwargs.get('headers')
        url = self.format_url(*url)
        self.logger.debug('Deleting url: %s' % url)
        r = self.delete(url, params=params, headers=headers)
        return self.do_return(r)

    def do_get(self, *url, **kwargs):
        params = kwargs.get('params')
        headers = kwargs.get('headers')
        url = self.format_url(*url)
        self.logger.debug('Getting url: %s' % url)
        r = self.get(url, params=params, headers=headers)
        return self.do_return(r)

    def do_put(self, *url, **kwargs):
        params = kwargs.get('params')
        headers = kwargs.get('headers')
        data = kwargs.get('data')
        if type(data) is dict:
            headers = {'content-type': 'application/json'}
            data = json.dumps(data)
        url = self.format_url(*url)
        self.logger.debug('Putting url: %s' % url)
        r = self.put(url, params=params, headers=headers, data=data)
        return self.do_return(r)

    def do_post(self, *url, **kwargs):
        params = kwargs.get('params')
        headers = kwargs.get('headers')
        data = kwargs.get('data')
        if type(data) is dict:
            headers = {'content-type': 'application/json'}
            data = json.dumps(data)
            self.logger.info(data)
        url = self.format_url(*url)
        self.logger.debug('Posting to url: %s' % url)
        r = self.post(url, params=params, headers=headers, data=data)
        return self.do_return(r)


class JuniperSessionWrapper(SessionWrapper):
    # Init and url construction for Juniper vpn connections

    def __init__(self, **kwargs):
        super(JuniperSessionWrapper, self).__init__(**kwargs)

        self.j_address = kwargs.get('j_address')
        self.j_user    = kwargs.get('j_user')
        self.j_pword   = kwargs.get('j_pword')
        self.verify = False

        # Check to see if credentials are registered
        if cookie_jar.get(self.j_address):
            # Set cookies
            self.cookies.update(cookie_jar.get(self.j_address))
        else:
            # Submit login credentials
            url = urljoin(self.j_address, 'dana-na/auth/url_default/login.cgi')
            data = {'tz_value': '-300', 'realm': 'Users', 'username': self.j_user, 'password': self.j_pword}
            r = self.post(url, data=data, verify=False)

            # Get the DSIDFormDataStr and respond to the request to start a new session
            h = BeautifulSoup(r.content, 'html.parser')
            dsid_field = h.find(id='DSIDFormDataStr')
            self.logger.debug('DSID %s' % dsid_field)
            data = {dsid_field['name']: dsid_field['value'], 'btnContinue': 'Continue%20the%20session'}
            r = self.post(url, data=data, verify=False)
            # Now you are logged in and session cookies are saved for future requests.

            # Stash the session cookies for other juniper sessions to the same proxy address
            cookie_jar[self.j_address] = self.cookies

    def format_url(self, *url):
        # This is the format:
        #   https://remote.vpn.com/,DanaInfo=hostname/api/url?query
        url = urljoin(self.j_address, ',DanaInfo=%s' % self.hostname, *url)
        return url


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    pass

