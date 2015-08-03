from Interface import Interface
# from HierarchicalData import Series, Study, Subject
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

    # Test DICOM Instantiate
    from OrthancInterface import OrthancInterface
    proxy = OrthancInterface(address='http://localhost:8043', name='3dlab-dev1')
    source = DICOMInterface(proxy=proxy, name='3dlab-dev0')

    # Test DICOM Query
    r = source.find('Patient', {'PatientName': 'ZNE*'})
    assert r['PatientID'] == 'ZA4VSDAUSJQA6'

    # TODO: Test DICOM Download


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    dicom_tests()