#!/usr/bin/env python
import glob
import os
import shutil
import sys

import yaml  # pip install pyyaml

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_CHALLS = os.path.join(os.path.dirname(TOOLS_DIR), 'original-challenges')
CHALLENGE_PATH = os.path.join(os.path.dirname(TOOLS_DIR), 'cqe-challenges')

# Load the manual patches
with open(os.path.join(TOOLS_DIR, 'manual_patches.yaml')) as f:
    mpatches = yaml.safe_load(f)


def debug(s):
    sys.stdout.write(str(s))
    sys.stdout.flush()


def apply_manual_patches(fname, src):
    # type: (str, str) -> str
    # Apply everything in 'all' first
    for match, rep in mpatches['all'].iteritems():
        src = src.replace(match, rep)

    # Apply any patches specific to this file
    if fname in mpatches:
        for match, rep in mpatches[fname].iteritems():
            src = src.replace(match, rep)
    return src


def try_delete(path):
    try:
        os.remove(path)
    except OSError:
        pass


def patch_files_in_dir(path):
    for fname in listdir(path):
        debug('\tPatching {}...'.format(fname))
        fpath = os.path.join(path, fname)

        # Read in the contents of the file
        with open(fpath) as f:
            src = f.read()

        # Apply all manual patches
        patched = apply_manual_patches(fname, src)

        # Write the patched file
        with open(fpath, 'w') as f:
            f.write(patched)
        debug('done => {}\n'.format(fname))


def patch_challenge(chal):
    debug('\nPatching {}...\n'.format(chal))

    # Some challenges have multiple binaries with the source in cb_* directories
    dirs = listdir(os.path.join(CHALLENGE_PATH, chal))
    cbdirs = filter(lambda d: d.startswith('cb_'), dirs)

    if len(cbdirs) > 0:
        # Process each of these as a separate challenge binary
        for d in cbdirs:
            patch_challenge(os.path.join(chal, d))
    else:
        lib_path = os.path.join(CHALLENGE_PATH, chal, 'lib')
        src_path = os.path.join(CHALLENGE_PATH, chal, 'src')
        inc_path = os.path.join(CHALLENGE_PATH, chal, 'include')

        # Delete these files if they exist
        del_list = ['libcgc.h', 'ctors.cc', 'dtors.cc', 'cpp.cc', 'libcpp.cc']
        for pth in [lib_path, src_path, inc_path]:
            for f in del_list:
                try_delete(os.path.join(pth, f))

        # Patch all lib files
        debug('Patching lib files...\n')
        patch_files_in_dir(lib_path)

        # Patch all source files
        debug('Patching src files...\n')
        patch_files_in_dir(src_path)
        patch_files_in_dir(inc_path)


def listdir(path):
    if not os.path.isdir(path):
        return []
    return sorted(os.listdir(path))


def clear_challenges(chal_paths):
    """Delete patched challenge directories"""
    for chal in chal_paths:
        try:
            shutil.rmtree(chal)
        except OSError:
            pass


def main():
    # Check which challenges to patch
    if len(sys.argv) > 1:
        # Filter out any invalid challenges
        chals = set(sys.argv[1:]).intersection(listdir(ORIGINAL_CHALLS))

        # Delete the old challenge folders
        clear_challenges([os.path.join(CHALLENGE_PATH, c) for c in chals])
    else:
        # Get all challenges
        chals = listdir(ORIGINAL_CHALLS)

        # Prompt before deleting all old challenges
        existing_chals = glob.glob(os.path.join(CHALLENGE_PATH, '*', ''))
        if len(existing_chals) > 0:
            res = raw_input('Patched challenges already exist. Delete and regenerate? (y/n): ') or 'n'
            if res[0] in 'yY':
                clear_challenges(existing_chals)

    # Copy over one challenge at a time and patch it
    for chal in chals:  # Only a few for now
        chal_dir = os.path.join(ORIGINAL_CHALLS, chal)
        dest_dir = os.path.join(CHALLENGE_PATH, chal)
        if os.path.isdir(chal_dir) and not os.path.isdir(dest_dir):
            shutil.copytree(chal_dir, dest_dir)
            patch_challenge(chal)


if __name__ == '__main__':
    main()
