#!/usr/bin/env python3

import argparse
from os import chmod, chown, makedirs, path, sep, stat, walk
from shutil import copymode, copystat
from subprocess import call
from stat import *

VERSION='0.1'

# Allows for invoking attributes as methods/functions
class AttributeDict(dict):
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value

class XDeltaImpl(object):
    @staticmethod
    def diff(old_file, new_file, target_file):
        command = ['xdelta3', '-f', '-e']
        if old_file:
            command.append('-s')
            command.append(old_file)

        command.append(new_file)
        command.append(target_file)

        if args.debug: print("Generating xdelta: %s" % command)
        call(command)

class XDelta3DirPatcher(object):
    def __init__(self, args):
        print("Initializing patcher")

        self.args = args

    def copy_attributes(self, src_file, dest_file):
        if args.debug: print("Copying mode data")
        copymode(src_file, dest_file)

        if args.debug: print("Copying stat data (sans UID/GID")
        copystat(src_file, dest_file)

        if args.debug: print("Copying UID & GID")
        uid = stat(src_file).st_uid
        gid = stat(src_file).st_gid

        chown(dest_file,uid,gid)

    def _find_file_delta(self, rel_path, new_file, old_root, new_root, target_root):
        print("\nProcessing %s" % new_file)

        target_path = path.join(target_root, rel_path)
        if not path.exists(target_path):
            makedirs(target_path)

        old_path = path.join(old_root, rel_path, new_file)
        new_path = path.join(new_root, rel_path, new_file)
        target_path = path.join(target_path, new_file)

        if args.debug: print([old_path, new_path, target_path])

        if not path.isfile(old_path):
            old_path = None
            if args.debug: print("Old file not present. Ignoring source in XDelta")

        XDeltaImpl.diff(old_path, new_path, target_path)

        self.copy_attributes(new_path, target_path)

    def run(self):
        print("Running delta3...")

        target_dir = path.join(args.target_dir, 'xdelta')

        for root, dirs, new_files in walk(args.new_dir):
            rel_path = path.relpath(root, args.new_dir).split(sep)[0]

            print('-'*10, root, '-'*10)
            print(new_files)
            for new_file in new_files:
                self._find_file_delta(rel_path, new_file, args.old_dir, args.new_dir, target_dir)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates and applies XDelta3-based directory diff tgz files')

    subparsers = parser.add_subparsers(dest='action')
    parser_apply = subparsers.add_parser('apply',
            help='Apply a diff from a directory. See "apply -help" for more options')

    parser_diff = subparsers.add_parser('diff',
            help='Generate a diff from a directory. See "apply -help" for more options')

    # Arguments to apply a diff
    parser_apply.add_argument('patch_dir',
            help='Folder containing the old version of the files')

    parser_apply.add_argument('target_dir',
            help='Folder containing the old version of the files')

    # Arguments to create a diff
    parser_diff.add_argument('old_dir',
            help='Folder containing the old version of the files')

    parser_diff.add_argument('new_dir',
            help='Folder containing the new version of the files')

    parser_diff.add_argument('target_dir',
            help='Destination folder for the generated diff')

    # Generic arguments
    parser.add_argument('--debug',
            help='Enable debugging output',
            action='store_true')

    parser.add_argument('--version',
            action='version',
            version='%(prog)s v' + VERSION)

    args = AttributeDict(vars(parser.parse_args()))

    if args.action:
        XDelta3DirPatcher(args).run()
    else:
        parser.print_help()