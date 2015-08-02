# Polynyms extend `dict` to provide a set of ids for different contexts
#
# The orthonym is the name that the anonym is derived/hashed from
# Any other context may assign its own name to this object

import hashlib
import logging

class Polynym(dict):

    @staticmethod
    def identity_rule(s):
        return s

    @staticmethod
    def md5_rule(s):
        return hashlib.md5(s)

    def __init__(self, o=None, pseudonyms=None, anonym_rule=None):

        super(Polynym, self).__init__()
        # Contexts are keys for the ids dictionary

        # Whenever the orthonym is set, it will call this rule and set the 'anonym' propery
        if anonym_rule:
            self.anonym_rule = anonym_rule
        else:
            self.anonym_rule = Polynym.identity_rule

        # An unqualified "id" is considered the orthonym (true name)
        # and will be returned as the default id
        self['orthonym'] = o

        if pseudonyms:
            self.update(pseudonyms)

    def __setitem__(self, key, value):
        if key == 'orthonym':
            anonym = self.anonym_rule(value)
            dict.__setitem__(self, 'anonym', anonym)
            dict.__setitem__(self, 'orthonym', value)
        elif key == 'anonym':
            if self.anonym_rule(self.get('orthonym')) != value:
                dict.__setitem__(self, 'orthonym', None)
            dict.__setitem__(self, 'anonym', value)
        else:
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

    def __cmp__(self, other):
        # Polynyms are considered equivalent if the share _anonyms_ (same value and rule)
        if self.a == other.a:
            return True
        else:
            return False

def polynym_tests():

    logger=logging.getLogger(Polynym.__name__)
    logger.debug('Testing Polynym')

    # Test creation
    p = Polynym(o="Hi", anonym_rule=Polynym.md5_rule)
    assert p.o == "Hi"
    assert p.a.hexdigest() == 'c1a5298f939e87e8f962a5edfc206918'

    # Test alter orthonym
    p.o = 'Hello'
    assert p.o == "Hello"
    assert p.a.hexdigest() == '8b1a9953c4611296a827abf8c47804d7'

    # Test alter anonym
    p.a = 'Bonjour'
    assert p.o == None
    assert p.a == 'Bonjour'

    # Test add new key
    p['alias'] = 'Good day!'
    assert p['alias'] == 'Good day!'


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    polynym_tests()

