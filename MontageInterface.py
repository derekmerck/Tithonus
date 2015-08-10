import logging
from Interface import Interface


class MontageInterface(Interface):

    def __init__(self, **kwargs):
        super(MontageInterface, self).__init__(**kwargs)

    def subject_from_id(self, subject_id):
        pass

    def study_from_id(self, study_id):
        pass

    def series_from_id(self, series_id):
        pass

    def find(self, level, question, source=None):
        return self.do_get('api/v1/index/%s/search' % source, params={'q': question, 'format': 'json'})
        # TODO: Implement study_from_id so we can return a worklist referencing the PACS


def test_montage():

    logger = logging.getLogger(test_montage.__name__)

    # Test DICOM Q/R/DL
    from tithonus import read_yaml
    repos = read_yaml('repos.yaml')

    source = Interface.factory('montage', repos)

    # Look in collection "rad" for query string "fracture"
    r = source.find('study', 'fracture', 'rad')
    assert(r['meta']['total_count'] > 1400000)

    # # Test shared juniper session cookies
    # source2 = Interface.factory('montage', repos)
    #
    # # Look in collection "rad" for query string "fracture"
    # r = source2.find('study', 'fracture', 'rad')
    # assert(r['meta']['total_count'] > 1400000)

    # source3 = Interface.factory('3dlab+lsmaster', repos)
    # source3.all_studies()


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_montage()
