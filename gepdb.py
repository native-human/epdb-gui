#!/usr/bin/env python

# example helloworld.py

import pygtk
pygtk.require('2.0')
import gtk
import gtksourceview2
import gobject
import pango

import sys
import os.path
import keyword, token, tokenize, cStringIO, string
import pexpect
import re
import argparse

from gepdb.guipdb import GuiPdb    

class EditWindow(gtk.Notebook):
    def __init__(self):
        gtk.Notebook.__init__(self)
   


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start the application logic for the poll website')
    parser.add_argument('file', help='Give the filename to execute in debug mode', nargs=1)
    args = parser.parse_args()
    #print args.file[0]

    guipdb = GuiPdb(args.file[0])
    guipdb.main()

