from Interface import Interface
from Polynym import DicomSeries, DicomStudy, DicomSubject
import logging


class XNATInterface(Interface):

    var_dict = {'study_type': 'xnat:mrSessionData/fields/field[name=study_type]/field'}

    def __init__(self, **kwargs):
        super(XNATInterface, self).__init__(**kwargs)

    # TODO: XNAT build series, studies, and subjects correctly
    def series_from_id(self, series_id):
        return DicomSeries(series_id=series_id, anonymized=True)

    def study_from_id(self, study_id):
        return DicomStudy(study_id=study_id, anonymized=True)

    def subject_from_id(self, subject_id):
        return DicomSubject(subject_id=subject_id, anonymized=True)

    def all_studies(self):
        resp = self.do_get('data/experiments')
        # Find all of the data labels
        results = resp.get('ResultSet').get('Result')
        for result in results:
            DicomStudy(result['ID'])

    def upload_data(self, item):
        # See <https://wiki.xnat.org/display/XKB/Uploading+Zip+Archives+to+XNAT>

        if isinstance(item, DicomSeries):
            params = {'overwrite': 'delete',
                      'project': item.subject.project.project_id,
                      'subject': item.subject.subject_id,
                      'session': item.study.study_id}
            headers = {'content-type': 'application/zip'}
            self.do_post('data/services/import?format=html', params=params, headers=headers, data=item.data)
        else:
            self.logger.warn('XNATInterface can only upload series items')

    def delete(self, worklist):
        # Unfortunately need the project for a delete, but perhaps easier with a 'root' project?

        if not isinstance(worklist, list):
            worklist = [worklist]

        for item in worklist:
            params = {'remove_files': 'true'}
            self.do_delete('data/archive/projects', item.subject.project_id,
                           'subjects', item.subject.subject_id[self],
                           'experiments', item.study_id[self], params=params)

    # XNAT specific

    def set_study_attribute(self, study, key):
        value = study.__dict__[key]
        params = {self.var_dict[key]: value}
        self.do_put('data/archive/projects', study.subject.project.project_id,
                    'subjects', study.subject.subject_id[self],
                    'experiments', study.study_id[self], params=params)


def test_xnat():

    logger = logging.getLogger(test_xnat.__name__)

    # Need to test:
    # 1. xnat-dev is up
    # 2. mtp01 is empty
    # 3. can upload a study to mtp01 w correct subject name, study name, etc.
    # 4. can download the study from mtp01
    pass


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    test_xnat()
