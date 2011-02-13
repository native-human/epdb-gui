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
import tempfile

from dbgcom import DbgProcessProtocol, DbgComFactory

class Toolbar(gtk.HBox):
    def __init__(self, dbgcom, guiactions):
        gtk.HBox.__init__(self)
        self.dbgcom = dbgcom
        self.guiactions = guiactions
        self.rcontinue = gtk.Button("rcontinue")
        self.rcontinue.connect("clicked", self.rcontinue_click, None)
        self.rstep = gtk.Button("rstep")
        self.rstep.connect("clicked", self.rstep_click, None)
        self.step = gtk.Button("step")
        self.step.connect("clicked", self.step_click, None)
        self.next = gtk.Button("next")
        self.next.connect("clicked", self.next_click, None)
        self.rnext = gtk.Button("rnext")
        self.rnext.connect("clicked", self.rnext_click, None)
        self.cont = gtk.Button("continue")
        self.cont.connect("clicked", self.continue_click, None)
        self.snapshot = gtk.Button("snapshot")
        self.snapshot.connect("clicked", self.snapshot_click, None)

        self.restart = gtk.Button("restart")
        self.restart.connect("clicked", self.restart_click, None)
        self.show_breaks = gtk.Button("show_breaks")
        self.show_breaks.connect("clicked", self.show_break_click, None)
        self.pack_start(self.rcontinue, False, False, 0)
        self.pack_start(self.rnext, False, False, 0)
        self.pack_start(self.rstep, False, False, 0)
        self.pack_start(self.step, False, False, 0)
        self.pack_start(self.next, False, False, 0)
        self.pack_start(self.cont, False, False, 0)
        self.pack_start(self.snapshot, False, False, 0)
        self.pack_start(self.restart, False, False, 0)
        self.step.show()
        self.next.show()
        self.rnext.show()
        self.restart.show()
        self.show_breaks.show()
        self.rcontinue.show()
        self.cont.show()
        self.rstep.show()
        self.snapshot.show()
        self.show()

    def modify_font(self, font):
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
        self.snapshot.set_sensitive(True)

    def deactivate(self):
        self.next.set_sensitive(False)
        self.step.set_sensitive(False)
        self.cont.set_sensitive(False)
        self.rcontinue.set_sensitive(False)
        self.rstep.set_sensitive(False)
        self.rnext.set_sensitive(False)
        self.restart.set_sensitive(False)
        self.snapshot.set_sensitive(False)
        
    
    def rstep_click(self, widget, data=None):
        self.dbgcom.sendLine('rstep')
        #print('rstep')

    def restart_click(self, widget, data=None):
        # TODO make this function work
        if self.guiactions.window.listen:
            
            params = getattr(self.dbgcom, 'params', '')
            dlgentry = gtk.Entry()
            dlgentry.set_text(params)
            dlglbl = gtk.Label("Parameters: ")
            #dialog = gtk.Dialog(title="pass parameters", parent=self.window, flags=gtk.DIALOG_MODAL, buttons=("OK", 1))
            dialog = gtk.Dialog(title="pass parameters", flags=gtk.DIALOG_MODAL, buttons=("OK", 1))
            dialog.vbox.pack_start(dlglbl, True, True, 0)
            dialog.vbox.pack_start(dlgentry, True, True, 0)
            dlgentry.show()
            dlglbl.show()
            answer = dialog.run()
            print "parameter", dlgentry.get_text()
            self.parameters = dlgentry.get_text() 
            dialog.destroy()
            
            ###
            self.guiactions.reset()
            
            # TODO refactor the code so that it doesn't reference guiactions.window
            reactor = self.guiactions.window.reactor
            self.guiactions.window.listen.stopListening()
            self.dbgcom.quit()
            self.guiactions.window.dbgprocess = DbgProcessProtocol(self.guiactions)
            self.guiactions.window.tempfilename = tempfile.mktemp(dir=self.guiactions.window.tempdir)
            factory = DbgComFactory(self.guiactions)
            self.listen = reactor.listenUNIX(self.guiactions.window.tempfilename, factory)
            r = reactor.spawnProcess(self.guiactions.window.dbgprocess, 'epdb',
                            ["epdb", "--uds", self.guiactions.window.tempfilename, self.guiactions.window.filename],
                            usePTY=True)
        else:
            "TODO error message"

    def show_break_click(self, widget, data=None):
        self.dbgcom.sendLine('show_break')

    def next_click(self, widget, data=None):
        self.dbgcom.sendLine("next")

    def rnext_click(self, widget, data=None):
        self.dbgcom.sendLine('rnext')

    def continue_click(self, widget, data=None):
        self.dbgcom.sendLine("continue")
        
    def rcontinue_click(self, widget, data=None):
        self.dbgcom.sendLine("rcontinue")
    
    def step_click(self, widget, data=None):
        self.dbgcom.sendLine('step')
        
    def snapshot_click(self, widget, data=None):
        self.dbgcom.sendLine('snapshot')