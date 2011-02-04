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

class OutputBox(gtk.Notebook):
    def __init__(self, dbgcom, guiactions):
        gtk.Notebook.__init__(self)
        self.dbgcom = dbgcom
        self.guiactions = guiactions
        self.debugbuffer = gtk.TextBuffer()
        self.debug = gtk.TextView(self.debugbuffer)
        self.debug.set_editable(False)
        
        self.debug_sw = gtk.ScrolledWindow()
        self.debug_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.debug_sw.add(self.debug)
        
        self.outputbox = gtk.VBox()
        self.outputbuffer = gtk.TextBuffer()
        self.output = gtk.TextView(self.outputbuffer)
        self.output.set_editable(False)
    
        self.output_sw = gtk.ScrolledWindow()
        self.output_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.output_sw.add(self.output)
        
        self.input_entry = gtk.Entry()
        self.input_entry.set_sensitive(False)
        self.input_entry.show()
        self.input_entry.connect("activate", self.input_entry_activate)
        self.outputbox.pack_start(self.output_sw, True, True, 0)
        self.outputbox.pack_start(self.input_entry, False, False, 0)
        self.outputbox.show()
        
        #self.notebook = gtk.Notebook()
        self.set_tab_pos(gtk.POS_TOP)
        self.output_tab_lbl = gtk.Label('Output')
        self.output_tab_lbl.show()
        self.debug_tab_lbl = gtk.Label('Debug')
        self.debug_tab_lbl.show()
        
        self.append_page(self.outputbox, self.output_tab_lbl)
        self.append_page(self.debug_sw, self.debug_tab_lbl)
        self.show()
        self.output.show()
        self.output_sw.show()
        self.debug.show()
        self.debug_sw.show()
        
    def input_entry_activate(self, entry):
        text = entry.get_text()
        entry.set_text('')
        entry.set_sensitive(False)
        self.dbgcom.sendLine(text+'\n')
        self.guiactions.activate()
        
    def modify_font(self, font_desc):
        self.debug.modify_font(font_desc)
        self.output.modify_font(font_desc)
        self.debug_tab_lbl.modify_font(font_desc)
        self.output_tab_lbl.modify_font(font_desc)
        self.input_entry.modify_font(font_desc)