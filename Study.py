from Polynym import Polynym

class HierarchicalDataNode(object):
    """
    A base class used to describe the tiered many->one relationships between
       instances -> series -> studies -> visits -> subjects -> projects
    """

    def __init__(self, parent=None, children=None, data=None):
        super(HierarchicalDataNode,self).__init__()
        self.parent = parent
        self.children = children
        self.data = data


class Instance(HierarchicalDataNode):
    # A leaf node, `data` is a single 2D image

    def __init__(self, instance_id=None, parent=None, anonym_rule=None):
        super(Instance, self).__init__(parent=parent)
        self.instance_id = Polynym(instance_id, anonym_rule=anonym_rule)


class Series(HierarchicalDataNode):
    # An ordered set of images; `data` is a single volume or set of images
    # Parent is study, children are instances

    def __init__(self, series_id=None, parent=None, children=None, anonym_rule=None):
        super(Series, self).__init__(parent=parent, children=children)
        self.series_id = Polynym(series_id, anonym_rule=anonym_rule)

        self.series_type = '' # Protocol, e.g., HEAD W WO CONTRAST
        self.study = self.parent
        self.instances = self.children


class Study(HierarchicalDataNode):
    # Parent is either Visit or Subject, children are Series

    def __init__(self, study_id=None, parent=None, children=None, anonym_rule=None):
        super(Study, self).__init__(parent=parent, children=children)
        self.study_id = Polynym(study_id, anonym_rule=anonym_rule)
        self.subject = self.parent  # Or visit...
        self.series = self.children

        # Metadata
        self.study_type = ''  # Pre/intra/post

    @property
    def accession(self):
        return self.study_id.get('accession')
    @accession.setter
    def accession(self, value):
        self.study_id['accession']=value

    def __str__(self):
        return "{0}/{1}({2})".format(self.study_id.o, self.study_id.w, self.subject.subject_name.o)

    def __repr__(self):
        return self.__str__()


class Visit(HierarchicalDataNode):
    # This is an optional intermediate node between study (accession) and subject
    # For example, if there are multiple 4D acquisitions (studies) or separate body parts

    def __init__(self, visit_id=None, parent=None, children=None):
        super(Visit, self).__init__(parent=parent, children=children)
        self.visit_id = Polynym(visit_id)
        self.subject = self.parent
        self.studies = self.children

        # Metadata
        self.visit_type = ''  # Baseline, follow-up, treatment, etc.
        self.visit_date = ''  # Anonymize this, too, or do we need it?
        self.institution = ''


class Subject(HierarchicalDataNode):
    # Parent is project, children are visits/studies

    def __init__(self, subject_id=None, subject_name=None, subject_dob=None, anonym_rule=None,
                 parent=None, children=None):
        super(Subject, self).__init__(parent=parent, children=children)
        self.subject_id = Polynym(subject_id, anonym_rule=anonym_rule)
        self.project = self.parent
        self.studies = self.children  # Or visits

        # Metadata
        self.subject_name = Polynym(subject_name)
        self.dob = Polynym(subject_dob)
        self.home_institution = ''  # For project tracking


class Project(HierarchicalDataNode):
    # This is a root node, it has no parents, children are subjects

    def __init__(self, project_id=None, children=None):
        super(Project, self).__init__(children=children)
        self.project_id = project_id
        self.subjects = children

if __name__ == "__main__":

    item = Instance('my_item', anonym_rule=Polynym.md5_rule)

    print item.instance_id.o
    print item.instance_id.a