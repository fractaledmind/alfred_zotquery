"""
pashua.py - Interface to Pashua

DESCRIPTION

Pashua is an application that can be used to provide some type
of dialog GUI for Python and shell applications under Mac OS X.
Pashua.py is the glue between your script and Pashua. To learn
more about Pashua, take a look at the application's Readme file.
Pashua's homepage is http://www.bluem.net/downloads/pashua_en/

EXAMPLES

Most GUI elements that are available are demonstrated in the example
above, so there's not much more to show ;-) To learn more about the
configuration syntax, take a look at the file Syntax.rtf which is
included in the disk image.

Please note in order for the example to work, the Pashua application
must be in the current path, in /Applications/ or in ~/Applications/
If none of these paths apply, you will have to specify it manually
  Pashua.PATH = '/path/to/appfolder';
before you call Pashua.run(). Alternatively, you may specify the
path (the directory that contains Pashua.app, without trailing slash)
as 3rd argument to run()

AUTHOR / TERMS AND CONDITIONS

Pashua is copyright (c) 2003-2005 Carsten Bluem <carsten@bluem.net>

This Python module is based on a Perl module by Carsten Bluem and
was ported to Python by James Reese. Further modifications were
contributed by Canis Lupus and Carsten Bluem.

You can use and /or modify this module any way you like.
This software comes with NO WARRANTY of any kind.

"""

import sys
import os.path
import tempfile

# Configuration variables

VERSION = '0.9.5'
PATH = ''
BUNDLE_PATH = "Pashua.app/Contents/MacOS/Pashua"

PASHUA_PLACES = [
    os.path.join(os.path.dirname(sys.argv[0]), "Pashua"),
    os.path.join(os.path.dirname(sys.argv[0]), BUNDLE_PATH),
    os.path.join(".", BUNDLE_PATH),
    os.path.join("/Applications", BUNDLE_PATH),
    os.path.join(os.path.expanduser("~/Applications"), BUNDLE_PATH),
    os.path.join("/usr/local/bin", BUNDLE_PATH)
]

# Search for the pashua binary
def locate_pashua(places):
    """
    Find Pashua by looking in each of places in order, returning the path,
    or None if no Pashua was found.
    """
    for folder in places:
        if os.path.exists(folder):
            return folder


# Calls the pashua binary, parses its result
# string and generates a dictionary that's returned.
def run(config_data, encoding=None, pashua_path=None):
    """
    Create a temporary config file holding `config_data`, and run
    Pashua passing it the pathname of the config file on the
    command line.
    """

    # Write configuration to temporary config file
    config_file = tempfile.mktemp()

    try:
        with open(config_file, "w") as file_obj:
            file_obj.write(config_data.encode(encoding))
            file_obj.close()
    except IOError, clue:
        # pass it on up, but with an extra diagnostic clue
        raise IOError("Error accessing '%s': %s" % (config_file, clue))

    # Try to figure out the path to pashua
    pashua_dir = None
    if pashua_path:
        #PASHUA_PLACES.insert(0, pashua_path + '/' + BUNDLE_PATH)
        if 'Contents/MacOS' in pashua_path:
            pashua_dir = pashua_path
        else:
            pashua_path = pashua_path + '/' + BUNDLE_PATH
            if 'Contents/MacOS' in pashua_path:
                pashua_dir = pashua_path

    if not pashua_dir:
        if PATH:
            PASHUA_PLACES.insert(0, PATH)
        pashua_dir = locate_pashua(PASHUA_PLACES)
        if not pashua_dir:
            raise IOError("Unable to locate the Pashua application.")

    # Pass encoding as command-line argument, if necessary
    # Take a look at Pashua's documentation for a list of encodings
    if encoding:
        cli_arg = "-e %s" % (encoding)
    else:
        cli_arg = ""

    # Call pashua binary with config file as argument and read result
    cmd = "'%s' %s %s" % (pashua_dir, cli_arg, config_file)

    res = os.popen(cmd, "r").readlines()

    # Remove config file
    os.unlink(config_file)

    # Parse results
    res_dct = {}
    for line in res:
        key, val = line.split('=')
        res_dct[key] = val.rstrip()

    return res_dct
