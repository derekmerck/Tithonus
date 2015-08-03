'''
In progress...

Tithonus

Gatekeeper script for mirroring deidentified and reformatted medical images
(Named after _P. Tithonus_, the Gatekeeper butterfly)

[Derek Merck](derek_merck@brown.edu)
Spring 2015

<https://github.com/derekmerck/Tithonus>

Dependencies: requests, yaml, GID_Mint

See README.md for usage, notes, and license info.
'''

import logging
import argparse
import os
import yaml
from Interface import Interface

logger = logging.getLogger('Tithonus Core')


# Effectively reduces the problem to implementing a generic query, copy, and delete for each interface
def find(source, query):
    return source.find(query['level'], query['Query'])


def copy(source, target, worklist, anonymize=False):
    if isinstance(source, basestring):
        # It's a local file being uploaded
        target.copy(worklist, source, target, anonymize)
    else:
        source.copy(worklist, source, target, anonymize)


def delete(source, worklist):
    source.delete(worklist)


def move(source, target, worklist, anonymize=False ):
    copy(source, target, worklist, anonymize)
    delete(source, worklist)


def mirror(source, target, query, anonymize=False):
    worklist = find(source, query)
    copy(source, target, worklist, anonymize)


def transfer(source, target, query, anonymize=False):
    worklist = find(source, query)
    move(source, target, worklist, anonymize)


def get_args():
    """Setup args and usage"""
    parser = argparse.ArgumentParser(description='Tithonus Core')

    parser.add_argument('command',
                        choices=['find', 'copy', 'delete', 'move', 'mirror', 'transfer'])
    parser.add_argument('source',
                        help='Source/working image repository as json or ID in config')
    parser.add_argument('target',
                        help='Target image repository json or as ID in config')
    parser.add_argument('-i', '--input',
                        help='Worklist of items to process or query/filter as json, yaml or csv file')
    parser.add_argument('-o', '--outfile',
                        help='File for output worklist from "find" function')
    parser.add_argument('-a', '--anonymize',
                        help='Anonymize patients and studies before copy/move (if source is orthanc-type)',
                        action='store_true',
                        default='False')
    parser.add_argument('-c', '--config',
                        help='Image repository configuration file',
                        default='repo.yaml')
    parser.add_argument('-V', '--version',
                        action='version',
                        version='%(prog)s (version ' + __version__ + ')')

    p = parser.parse_args()

    if os.path.isfile(p.config):
        f = open(p.config, 'r')
        y = yaml.load(f)
        f.close()
        logger.info('Read config: \n', y)

    return p


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    args = get_args()

    input_data = """
1234abcdXXY:
  project_id: protect3d
  subject_id: my_patient100
  study_id:   my_study-ABCD
  study_type: baseline_minus_10
  local_file: /Users/derek/Desktop/xnat_test/sample1
"""

    command = args.get('command')
    input = yaml.load(input_data)
    worklist = input
    query = input
    anonymize = args.anonymize
    output = args.get('output')

    source = None
    if args.get('source'):
        source_config = p.config[args.get('source')]
        source_config['name'] = args.get('source')
        source = Interface.factory(source_config)

    target = None
    if args.get('target'):
        target_config = p.config[args.get('target')]
        target_config['name'] = args.get('target')
        target = Interface.factory(target_config)

    if command == 'find':
        query = args.input
        find(source, query)
    elif command == 'copy':
        copy(source, target, worklist, anonymize)
    elif command == 'delete':
        delete(source, worklist)
    elif command == 'move':
        move(source, target, worklist, anonymize)
    elif command == 'mirror':
        mirror(source, target, query, anonymize)
    elif command == 'transfer':
        transfer(source, target, query, anonymize)
    else:
        logger.error('Command %s not available')
        raise NotImplementedError
