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

class Toolbar(gtk.HBox):
    def __init__(self, prnt):
        gtk.HBox.__init__(self)
        self.prnt = prnt
        self.rcontinue = gtk.Button("rcontinue")
        self.rcontinue.connect("clicked", self.prnt.rcontinue_click, None)
        self.rstep = gtk.Button("rstep")
        self.rstep.connect("clicked", self.prnt.rstep_click, None)
        self.step = gtk.Button("step")
        self.step.connect("clicked", self.prnt.step_click, None)
        self.next = gtk.Button("next")
        self.next.connect("clicked", self.prnt.next_click, None)
        self.rnext = gtk.Button("rnext")
        self.rnext.connect("clicked", self.prnt.rnext_click, None)
        self.cont = gtk.Button("continue")
        self.cont.connect("clicked", self.prnt.continue_click, None)
        self.restart = gtk.Button("restart")
        self.restart.connect("clicked", self.prnt.restart_click, None)
        self.show_breaks = gtk.Button("show_breaks")
        self.show_breaks.connect("clicked", self.prnt.show_break_click, None)
        self.pack_start(self.rcontinue, False, False, 0)
        self.pack_start(self.rnext, False, False, 0)
        self.pack_start(self.rstep, False, False, 0)
        self.pack_start(self.step, False, False, 0)
        self.pack_start(self.next, False, False, 0)
        self.pack_start(self.cont, False, False, 0)
        self.pack_start(self.restart, False, False, 0)
        self.step.show()
        self.next.show()
        self.rnext.show()
        self.restart.show()
        self.show_breaks.show()
        self.rcontinue.show()
        self.cont.show()
        self.rstep.show()
        self.show()

    def modify_font(self, font):
        print "Modify font"
        print "Child", self.next.child
        self.next.child.modify_font(font)
        self.step.child.modify_font(font)
        self.cont.child.modify_font(font)
        self.rcontinue.child.modify_font(font)
        self.rstep.child.modify_font(font)
        self.rnext.child.modify_font(font)
        self.restart.child.modify_font(font)

    def activate(self):
        self.next.set_sensitive(True)
        self.step.set_sensitive(True)
        self.cont.set_sensitive(True)
        self.rcontinue.set_sensitive(True)
        self.rstep.set_sensitive(True)
        self.rnext.set_sensitive(True)
        self.restart.set_sensitive(True)

    def deactivate(self):
        self.next.set_sensitive(False)
        self.step.set_sensitive(False)
        self.cont.set_sensitive(False)
        self.rcontinue.set_sensitive(False)
        self.rstep.set_sensitive(False)
        self.rnext.set_sensitive(False)
        self.restart.set_sensitive(False)