# Polynyms extend `dict` to provide a set of ids for different contexts

import hashlib

class Polynym(dict):

    @staticmethod
    def identity_rule(s):
        return s

    @staticmethod
    def md5_rule(s):
        return hashlib.md5(s)

    def __init__(self, o=None, pseudonyms=None, anonym_rule=None, working_context=''):

        super(Polynym, self).__init__()
        # Contexts are keys for the ids dictionary

        # Whenever the orthonym is set, it will call this rule and set the 'anonym' propery
        if anonym_rule:
            self.anonym_rule = anonym_rule
        else:
            self.anonym_rule = Polynym.identity_rule
        self.working_context = working_context

        # An unqualified "id" is considered the orthonym (true name)
        # and will be returned as the default id
        self['orthonym'] = o

        if pseudonyms:
            self.update(pseudonyms)

    def __setitem__(self, key, value):
        if key == 'orthonym':
            anonym = self.anonym_rule(value)
            dict.__setitem__(self, 'anonym', anonym)
        if key == 'anonym':
            if self.anonym_rule(self.get('orthonym')) != value:
                dict.__setitem__(self, 'orthonym', None)
            dict.__setitem__(self, 'anonym', value)
        dict.__setitem__(self, key, value)

    @property
    def o(self):
        if self.get('orthonym'): return self.get('orthonym')
#        elif self.get('anonym'): return self.get('anonym')
        else: return None

    @o.setter
    def o(self, value):
        self['orthonym'] = value

    @property
    def a(self):
        if self.get('anonym'): return self.get('anonym')
        else: return None

    @a.setter
    def a(self, value):
        self['anonym'] = value

    @property
    def w(self):
        return self.get(self.working_context)

    @w.setter
    def w(self, value):
        self[self.working_context] = value

    def __cmp__(self, other):
        # Polynyms are considered equivalent if the share anonyms (same value and rule)
        if self.a == other.a:
            return True
        else:
            return False


if __name__ == "__main__":

    p = Polynym(o="Hi", anonym_rule=Polynym.md5_rule)
    print p.o
    print p.a
    p.o = 'Hello'
    print p.o
    print p.a
    p.a = 'Bonjour'
    print p.o
    print p.a
