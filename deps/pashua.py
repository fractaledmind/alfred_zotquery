"""
Pashua.py - Interface to Pashua

import Pashua

# Create a configuration for a simple dialog ...
var = \"\"\"
# Lines starting with a hash character are
# comments, empty lines are ignored

# Set transparency: 0 is transparent, 1 is opaque
transparency=0.95

# Set window title
title=Our first example. Isn't it simple?

# Define a checkbox "I like Python", default: checked
python.type=checkbox
python.label=I like Python
python.checked=1

# Define radiobuttons
book.type=radiobutton
book.label=Which Python bible do you prefer?
book.option=Progamming in Python
book.option=The Python Cookbook
book.selected=Python in a Nutshell

# Define a popup menu
editor.type=popup
editor.label=What's your favorite Python editor for the Mac?
editor.width=320
editor.option=AlphaX
editor.option=Alphatk
editor.option=BBedit
editor.option=Emacs
editor.option=jEdit
editor.option=NEdit (X11)
editor.option=Pepper
editor.option=SubEthaEdit
editor.option=vi/vim
editor.option=Xemacs
editor.option=Something else
editor.selected=BBedit

# Add a filesystem browser
fs.type=fsbrowser
fs.label=Some file or folder location
fs.width=320
fs.path=/Applications

# A separator line
-

# Define a text field , default: "user"
user.type=textfield
user.label=Enter your username
user.width=320
user.text=useR

# Define a password field
pwd.label=Enter your password
pwd.type=password
pwd.width=320

# Define a password field
host.label=Enter a hostname or IP to connect to
host.type=combobox
host.width=320
host.option=www.apple.com
host.option=www.bluem.net
host.selected=localhost

# Add a cancel button
cncl.type=cancelbutton

\"\"\"

# ... and save the result in result
result = Pashua.run(var);

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

import os.path
import sys
import tempfile

# Configuration variables
VERSION = '0.9.4.1'
PATH = ''
BUNDLE_PATH = "Pashua.app/Contents/MacOS/Pashua"

PASHUA_PLACES = [os.path.join(os.path.dirname(sys.argv[0]), "Pashua"), 
                 os.path.join(os.path.dirname(sys.argv[0]), BUNDLE_PATH),
                 os.path.join(".", BUNDLE_PATH),
                 os.path.join("/Applications", BUNDLE_PATH),
                 os.path.join(os.path.expanduser("~/Applications"), BUNDLE_PATH),
                 os.path.join("/usr/local/bin", BUNDLE_PATH)]


# Globals
PASHUA_DIR = None

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
            file_obj.write(config_data)
            file_obj.close()
    except IOError, diagnostic:
        # pass it on up, but with an extra diagnostic clue
        raise IOError("Error accessing Pashua config file '{}': {}".format(
                                                                    config_file,
                                                                    diagnostic))
    # Try to figure out the path to pashua
    if pashua_path:
        PASHUA_PLACES.insert(0, pashua_path + '/' + BUNDLE_PATH)

    if not PASHUA_DIR:
        if PATH:
            PASHUA_PLACES.insert(0, PATH)
        pashua_dir = locate_pashua(PASHUA_PLACES)
        if not pashua_dir:
            raise IOError("Unable to locate the Pashua application.")

    # Pass encoding as command-line argument, if necessary
    # Take a look at Pashua's documentation for a list of encodings
    if encoding:
        cli_arg = "-e {}".format(encoding)
    else:
        cli_arg = ""

    # Call pashua binary with config file as argument and read result
    cli = "'{dir}' {arg} {file}".format(
                                    dir=pashua_dir,
                                    arg=cli_arg,
                                    file=config_file)
    result = os.popen(cli, "r").readlines()

    # Remove config file
    os.unlink(config_file)

    # Parse result
    result_dict = {}
    for line in result:
        key, val = line.split('=')
        result_dict[key] = val.rstrip()
    return result_dict
