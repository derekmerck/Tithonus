from Utilities import zipdir

import requests
import json
from posixpath import join as urljoin
import logging
import os

class Interface(object):

    @classmethod
    def factory(name, _config):
        # Accepts a config dict and returns an interface
        config = _config[name]
        if config['type'] == 'xnat':
            return XNATInterface(config, name=name)
        elif config['type'] == 'orthanc':
            return OrthancInterface(config, name=name)
        elif config['type'] == 'orthanc':
            # TODO: prevent accidental infinite recursion
            raise NotImplementedError
            # proxy = Interface.facotry(config['proxy_name'], _config)
            # return DICOMInterface(config.name)
        else:
            # logger.warn("Unknown repo type in config")
            pass

        return interface

    def __init__(self, **kwargs):
        super(Interface, self).__init__()
        self.address = kwargs.get('address')
        self.aetitle = kwargs.get('aetitle')
        self.auth = (kwargs.get('user'), kwargs.get('pword'))
        self.name = kwargs.get('name')
        self.api_key = kwargs.get('api_key')
        self.series = {}
        self.studies = {}
        self.subjects = {}

        self.logger = logging.getLogger('Tithonus.Interface')
        self.logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    # Each interface needs a specialized factory for HDN types
    def subject_from_id(self, subject_id):
        raise NotImplementedError

    def study_from_id(self, study_id):
        raise NotImplementedError

    def series_from_id(self, series_id):
        raise NotImplementedError

    # Each interface needs to be able to run query/retreives to identify data sets
    def all_studies(self):
        raise NotImplementedError

    def query(self, level, question, source=None):
        # Level is a HDN type: subject, studies, or series
        # Question is a dictionary of property names and values
        # by default, the source is this interface,
        # returns a WORKLIST, a list of session, study, or subject items
        raise NotImplementedError

    def send(self, worklist, source=None, target=None):
        # Sends data for items in WORKLIST from the source to the target
        # if the source is self and the target is a file, it downloads
        # if the source is a file and the target is self, it uploads
        raise NotImplementedError

    # Each interface needs to implement methods for moving data around
    def upload_data(self, item):
        pass

    def download_data(self, item):
        pass

    # Helper functions

    def do_return(self, r):
        # Return dict if possible, but content otherwise (for image data)
        #self.logger.info(r.headers.get('content-type'))
        if r.headers.get('content-type') == 'application/json':
            try:
                ret = r.json()
                if len(ret) < 50:
                    msg = ret
                else:
                    msg = 'a long json declaration'
            except ValueError, e:
                ret = r.content
                msg = 'bad json declaration'
        else:
            ret = r.content
            msg = 'Non-json data'
        self.logger.debug('Returning value for %s', msg)
        return ret

    def do_delete(self, *url, **kwargs):
        params = kwargs.get('params')
        headers = kwargs.get('headers')
        url = urljoin(self.address, *url)
        self.logger.debug('Deleting url: %s' % url)
        r = requests.delete(url, params=params, headers=headers, auth=self.auth)
        return self.do_return(r)

    def do_get(self, *url, **kwargs):
        params = kwargs.get('params')
        headers = kwargs.get('headers')
        url = urljoin(self.address, *url)
        self.logger.debug('Getting url: %s' % url)
        r = requests.get(url, params=params, headers=headers, auth=self.auth)
        return self.do_return(r)

    def do_put(self, *url, **kwargs):
        params = kwargs.get('params')
        headers = kwargs.get('headers')
        data = kwargs.get('data')
        if type(data) is dict:
            headers = {'content-type': 'application/json'}
            data = json.dumps(data)
        url = urljoin(self.address, *url)
        self.logger.debug('Putting url: %s' % url)
        r = requests.put(url, params=params, headers=headers, auth=self.auth, data=data)
        return self.do_return(r)

    def do_post(self, *url, **kwargs):
        params = kwargs.get('params')
        headers = kwargs.get('headers')
        data = kwargs.get('data')
        if type(data) is dict:
            headers = {'content-type': 'application/json'}
            data = json.dumps(data)
            self.logger.info(data)
        url = urljoin(self.address, *url)
        self.logger.debug('Posting to url: %s' % url)
        r = requests.post(url, params=params, headers=headers, auth=self.auth, data=data)
        return self.do_return(r)

    def upload_archive(self, item, fn):
        if os.path.isdir(fn):
            self.logger.info('Uploading image folder %s', fn)
            item.data = zipdir(fn)
        elif os.path.isfile(fn):
            self.logger.info('Uploading image archive %s', fn)
            f = open(fn, 'rb')
            item.data = f.read()
        self.upload_data(item)

    def download_archive(self, item, fn):
        self.logger.info('Downloading image archive %s', fn)
        self.download_data(item)
        if fn is not None:
            f = open(fn + '.zip', 'wb')
            f.write(item.data)
            f.close()


if __name__ == "__main__":

    interface = Interface(address="http://localhost:8042")
    interface.do_get('studies')
