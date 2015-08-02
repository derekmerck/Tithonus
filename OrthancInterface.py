from Interface import Interface
from DICOMInterface import DICOMInterface
from HierarchicalData import Study, Subject
import logging
import os

class OrthancInterface(Interface):
    # <https://docs.google.com/spreadsheets/d/1muKHMIb9Br-59wfaQbDeLzAfKYsoWfDSXSmyt6P4EM8/pubhtml?gid=525933398&single=true>

    def __init__(self, **kwargs):
        super(OrthancInterface, self).__init__(**kwargs)

    # Derived Class Implementations
    def series_from_id(self, series_id):
        raise NotImplementedError

    def study_from_id(self, study_id):
        # Check if study is already in interface
        if self.studies.get(study_id):
            return self.studies.get(study_id)

        # Assemble the study data
        study_info = self.do_get('studies', study_id)

        # Get subject
        subject = self.subject_from_id(study_info['ParentPatient'])

        # Assemble the study data
        study = Study(study_id=study_info['MainDicomTags']['AccessionNumber'], parent=subject)
        study.study_id[self] = study_id

        self.studies[study_id] = study

        # TODO: Need to grab institution, mdname, to deidentify correctly
        # InstitutionName = 0008,0080
        # ReferringPhysiciansName = 0008,0090

        return study

    def subject_from_id(self, subject_id):
        # Check if study is already in interface
        if self.subjects.get(subject_id):
            return self.subjects.get(subject_id)

        # Assemble the subject data
        subject_info = self.do_get('patients', subject_id)

        subject = Subject(subject_id=subject_info['MainDicomTags']['PatientID'],
                          subject_name=subject_info['MainDicomTags']['PatientName'],
                          subject_dob=subject_info['MainDicomTags']['PatientBirthDate'])
        subject.subject_id[self] = subject_id

        self.subjects[subject_id] = subject
        return subject

    def find(self, level, query, source=None):
        worklist = None
        data = {'Level': level, 'Query': query}
        if source:
            # Checking a different modality
            resp_id = self.do_post('modalities', source.aetitle, 'query', data=data).get('ID')

            answers = self.do_get('queries', resp_id, 'answers')
            for a in answers:
                # Add to available studies, flag as present on source
                worklist = self.do_get('queries', resp_id, 'answers', a, 'content?simplify')
                # TODO: Process worklist id's to produce a list of studies...
                # Each remote study must be tagged with id[source]=(query_id, answer_id)
        else:
            # Add to available studies
            worklist = self.do_post('tools/find', data=data)
            # TODO: Process worklist id's to produce a list of studies...

        return worklist

    def send(self, item, target):
        raise NotImplementedError

    def retreive(self, item, source):
        # Retreiving from DICOM modality or Orthanc peer
        if isinstance(source, DICOMInterface):
            # Copy from modality
            self.do_post('queries', item.study_id.get('query_id'), 'answers', item.study_id.get('answer_id'), data=self.aetitle)
        else:
            raise NotImplementedError

    def download_data(self, study):
        study.data = self.do_get('studies', study.study_id[self], 'archive')

    def upload_data(self, study):
        # If there is study.data, send it.
        # If there is study.available_on_source, retreive it and create a new id
        pass

    def all_studies(self):
        study_ids = self.do_get('studies')
        self.studies = {study_id: self.study_from_id(study_id) for study_id in study_ids}

    # Orthanc ONLY functions

    def anonymize(self, study):

        rule_author = "RIH 3D Lab"
        rule_name = "General DICOM Deidentification Rules"
        rule_version = "v1.0"

        anon_script = {
            "Replace": {
                "0010-0010": study.subject.subject_name.a, # PatientsName
                "0010-0020": study.subject.subject_id.a,   # PatientID
                "0010-0030": study.subject.subject_dob.a,  # PatientsBirthDate
                "0008-0050": study.study_id.a,             # AccessionNumber
                "0012-0062": "YES",        # Deidentified
                "0010-0021": rule_author,  # Issuer of Patient ID
                "0012-0063": "{0} {1} {2}".format(rule_author, rule_name, rule_version) # Deidentification method
                },
            "Keep": [
                "0008-0080",                # InstitutionName
                "0010-0040",                # PatientsSex
                "0010-1010",                # PatientsAge
                "StudyDescription",
                "SeriesDescription"],
            "KeepPrivateTags": None
            }

        anon_study_id = self.do_post('studies', study.study_id[self], 'anonymize', data=anon_script)['ID']
        # Can unlink original data
        study.study_id[self, 'original'] = study.study_id[self]
        study.study_id[self] = anon_study_id


def orthanc_tests():

    logger = logging.getLogger(orthanc_tests.__name__)

    # Instantiate
    source = OrthancInterface(address="http://localhost:8042")
    source.all_studies()
    logger.debug(source.studies)
    assert '163acdef-fe16e651-3f35f584-68c2103f-59cdd09d' in source.studies.keys()

    # Test Download
    source.download_archive(source.studies.values()[0], 'orthanc_tmp_archive')
    assert os.path.getsize('orthanc_tmp_archive.zip') == 35884083
    os.remove('orthanc_tmp_archive.zip')

    # TODO: Orthanc query DICOM node
    # Query a different DICOM node
    # r = source.query('study', {'PatientName': 'ZNE*'}, '3dlab-dev0')
    # assert r['PatientID'] == u'ZA4VSDAUSJQA6'


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    orthanc_tests()