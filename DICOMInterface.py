from Interface import Interface
from HierarchicalData import Series, Study, Subject
import logging

class DICOMInterface(Interface):

    def __init__(self, **kwargs):
        super(DICOMInterface, self).__init__(**kwargs)

    def query(self, level, question, source=None):
        return self.proxy.query(level, question, self)

    def download_data(self, item):
        self.proxy.copy(item, self, self.proxy)
        self.proxy.download_data(item)

def dicom_tests():
    from OrthancInterface import OrthancInterface
    proxy = OrthancInterface(address='http://localhost:8043', aetitle='3dlab-dev1')
    source = DICOMInterface(proxy=proxy, aetitle='3dlab-dev0')
    source.query('Patient', {'PatientName': 'ZNE*'})


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    dicom_tests()