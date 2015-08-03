import json
from posixpath import join as urljoin
import logging
import zipfile
import os
import io
import requests


class Interface(object):

    # -----------------------------
    # Public factory
    # -----------------------------

    @classmethod
    def factory(cls, name, _config):
        from OrthancInterface import OrthancInterface
        from XNATInterface import XNATInterface
        from DICOMInterface import DICOMInterface

        # Accepts a config dict and returns an interface
        config = _config[name]
        if config['type'] == 'xnat':
            return XNATInterface(name=name, **config)
        elif config['type'] == 'orthanc':
            return OrthancInterface(name=name, **config)
        elif config['type'] == 'orthanc':
            proxy = Interface.factory(config['proxy'], _config)
            return DICOMInterface(name=name, proxy=proxy, **config)
        else:
            logger = logging.getLogger(Interface.factory.__name__)
            logger.warn("Unknown repo type in config")
            pass

    # -----------------------------
    # Baseclass __init__
    # -----------------------------

    def __init__(self, **kwargs):
        super(Interface, self).__init__()
        self.address = kwargs.get('address')
        self.aetitle = kwargs.get('aetitle')
        self.auth = (kwargs.get('user'), kwargs.get('pword'))
        self.name = kwargs.get('name')
        self.api_key = kwargs.get('api_key')
        self.proxy = kwargs.get('proxy')
        # Should be "available studies" plus a registry of all studies somewhere else
        self.series = {}
        self.studies = {}
        self.subjects = {}

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info('Created interface')

    # -----------------------------
    # Abstract Public API:
    # - find
    # - send
    # - receive
    # - delete
    # -----------------------------

    # TODO: Rename to find ...
    def find(self, level, question, source=None):
        # Level is a HDN type: subject, studies, or series
        # Question is a dictionary of property names and values
        # by default, the source is _this_ interface,
        # returns a WORKLIST, a list of session, study, or subject items
        raise NotImplementedError

    def retrieve(self, item, source):
        raise NotImplementedError

    def send(self, item, target):
        raise NotImplementedError

    def delete(self, worklist):
        raise NotImplementedError

    # -----------------------------
    # Abstract Private/Hidden API:
    # - upload_data
    # - download_data
    # - subject_from_id
    # - study_from_id
    # - series_from_id
    # - all_studies (optional)
    # -----------------------------

    # Each interface needs to implement methods for moving data around
    def upload_data(self, item):
        raise NotImplementedError

    def download_data(self, item):
        raise NotImplementedError

    # Factories for HDN types
    def subject_from_id(self, subject_id):
        raise NotImplementedError

    def study_from_id(self, study_id):
        raise NotImplementedError

    def series_from_id(self, series_id):
        raise NotImplementedError

    # Optional but frequently useful shortcut
    def all_studies(self):
        raise NotImplementedError

    # -----------------------------
    # Baseclass Public API:
    # - copy
    # - move
    # - upload_archive
    # - download_archive
    # -----------------------------

    def copy(self, worklist, source, target, anonymize=False):
        # Sends data for items in WORKLIST from the source to the target
        # if the source is self and the target is a string/file, it downloads
        # if the source is a string/file and the target is self, it uploads
        # if the source is a DICOM node and the target is self, it retrieves

        # TODO: Create anonymized study if necessary and delete it when done

        if not hasattr(worklist, '__iter__'):
            worklist = [worklist]

        for item in worklist:
            # Figure out case
            if isinstance(source, basestring) and (target is None or target is self):
                # It's probably a file being uploaded
                self.upload_archive(item, source)
            elif source is self and isinstance(target, basestring):
                # It's probably a file being downloaded
                self.download_archive(item, target)
            elif source is self:
                # Sending to DICOM modality or Orthanc peer
                self.send(item, target)
            elif target is self:
                self.retrieve(item, source)

    def move(self, worklist, source, target, anonymize=False):
        self.copy(worklist, source, target, anonymize)
        self.delete(worklist)

    def upload_archive(self, item, fn):
        if os.path.isdir(fn):
            self.logger.info('Uploading image folder %s', fn)
            item.data = self.zipdir(fn)
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

    # -----------------------------
    # Private/Hidden Helpers
    # - do_get
    # - do_post
    # - do_put
    # - do_delete
    # - do_return
    # - zipdir
    # -----------------------------

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

    def zipdir(top, fno=None):

        file_like_object = None
        if fno is None:
            # logger.info('Creating in-memory zip')
            file_like_object = io.BytesIO()
            zipf = zipfile.ZipFile(file_like_object, 'w', zipfile.ZIP_DEFLATED)
        else:
            # logger.info('Creating in-memory zip')
            zipf = zipfile.ZipFile(fno, 'w', zipfile.ZIP_DEFLATED)

        for dirpath, dirnames, filenames in os.walk(top):
            for f in filenames:
                fn = os.path.join(dirpath, f)
                zipf.write(fn, os.path.relpath(fn, top))

        if fno is None:
            return file_like_object
        else:
            zipf.close()


def interface_tests():

    logger = logging.getLogger(interface_tests.__name__)

    # Test Interface Instatiate
    interface = Interface(address="http://localhost:8042")
    assert interface.do_get('studies') == [u'163acdef-fe16e651-3f35f584-68c2103f-59cdd09d']

    # Test Interface Factory
    interface = Interface.factory('test', {'test': {'type': 'orthanc', 'address': 'http://localhost:8042'}})
    assert interface.do_get('studies') == [u'163acdef-fe16e651-3f35f584-68c2103f-59cdd09d']


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    interface_tests()


