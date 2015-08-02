from Interface import Interface
from HierarchicalData import Study, Subject
import logging

class XNATInterface(Interface):

    var_dict = {'study_type': 'xnat:mrSessionData/fields/field[name=study_type]/field'}

    def __init__(self, **kwargs):
        super(XNATInterface, self).__init__(**kwargs)

    def study_from_id(self, study_id):
        return Study(study_id)

    def subject_from_id(self, subject_id):
        return Study(study_id)

    def all_studies(self):
        resp = self.do_get('data/experiments')
        # Find all of the data labels
        results = resp.get('ResultSet').get('Result')
        # TODO: This isn't quite right -- need to build studies and subjects correctly
        _studies = [Study(result['ID'], accession=result['label']) for result in results]
        return _studies

    def upload_data(self, study):
        """See <https://wiki.xnat.org/display/XKB/Uploading+Zip+Archives+to+XNAT>"""

        params = {'overwrite': 'delete',
                  'project': study.subject.project.project_id,
                  'subject': study.subject.subject_id,
                  'session': study.study_id}
        headers = {'content-type': 'application/zip'}
        self.do_post('data/services/import?format=html', params=params, headers=headers, data=study.data)

    def delete_study(self, study):
        # Unfortunately need the project for a delete, but perhaps easier with a 'root' proj
        # TODO: Test xnat delete
        params = {'remove_files': 'true'}
        self.do_delete('data/archive/projects', study.subject.project.project_id,
                       'subjects', study.subject.subject_id[self],
                       'experiments', study.study_id[self], params=params)

    # XNAT specific

    def set_study_attribute(self, study, key):
        value = study.__dict__[key]
        params = {self.var_dict[key]: value}
        self.do_put('data/archive/projects', study.subject.project.project_id,
                    'subjects', study.subject.subject_id[self],
                    'experiments', study.study_id[self], params=params)


def xnat_tests():
    # Need to test:
    # 1. xnat-dev is up
    # 2. mtp01 is empty
    # 3. can upload a study to mtp01 w correct subject name, study name, etc.
    # 4. can download the study from mtp01
    pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    xnat_tests()