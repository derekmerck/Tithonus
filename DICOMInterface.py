from Interface import Interface
from HierarchicalData import Series, Study, Subject
import logging

class DICOMInterface(Interface):

    def __init__(self, **kwargs):
        super(DICOMInterface, self).__init__(**kwargs)

    def find(self, level, question, source=None):
        return self.proxy.find(level, question, self)

    def download_data(self, item):
        self.proxy.copy(item, self, self.proxy)
        self.proxy.download_data(item)

def dicom_tests():

    logger = logging.getLogger(dicom_tests.__name__)

    # Instantiate
    from OrthancInterface import OrthancInterface
    proxy = OrthancInterface(address='http://localhost:8043', aetitle='3dlab-dev1')
    source = DICOMInterface(proxy=proxy, aetitle='3dlab-dev0')

    # Test query-by-proxy
    r = source.find('Patient', {'PatientName': 'ZNE*'})
    assert r['PatientID'] == 'ZA4VSDAUSJQA6'

    # Test download
    source.download_archive()


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    dicom_tests()