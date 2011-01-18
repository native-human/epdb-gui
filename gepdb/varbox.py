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

class Varbox(gtk.VBox):
    def __init__(self, prnt):
        gtk.VBox.__init__(self)
        self.prnt = prnt

        self.treestore = gtk.TreeStore(str, str, str)
 
        self.var_renderer = gtk.CellRendererText()
        #self.timeline_renderer.set_property('background', 'red')
        self.lbl = gtk.Label('Variables')
        
        self.scrolledwindow = gtk.ScrolledWindow()
        self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolledwindow.show()
        
        self.lbl.show()
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_headers_visible(False)
        self.entrybox = gtk.HBox()
        self.entry = gtk.Entry()
        self.entry.show()
        self.entry.connect("activate", self.entry_activate)
        self.entrybox.pack_start(self.entry, True, True, 0)
        self.addbutton = gtk.Button('Add')
        self.addbutton.connect('clicked', self.on_varadd_clicked)
        self.addbutton.show()
        self.entrybox.pack_start(self.addbutton, False, False, 0)
        self.entrybox.show()
        
        self.treeview.show()
        #print "Treestore", self.treestore.append(None, ('Blah','blue', 'green'))
        self.treedict = {}
        self.tvcolumn1 = gtk.TreeViewColumn('Column 0', self.var_renderer, text=0, background=2)
        self.tvcolumn2 = gtk.TreeViewColumn('Column 1', self.var_renderer, text=1, background=2)
        
        self.treeview.append_column(self.tvcolumn1)
        self.treeview.append_column(self.tvcolumn2)
        
        #self.pack_start(self.timelinebox, False, False, 0)
        self.pack_start(self.lbl, False, False, 0)
        self.pack_start(self.entrybox, False, False, 0)
        self.pack_start(self.scrolledwindow, True, True, 0)
        self.scrolledwindow.add(self.treeview)
        self.show()
        
    
    def reset(self):
        self.treestore.clear()
        self.treedict = {}
        
    def add_var(self, name):
        if name in self.treedict:
            self.prnt.statusbar.message("Variable name already exists")
        else:
            id = self.treestore.append(None, (name, None, 'white'))
            self.treedict[name] = id
            self.entry.set_text('')
        self.update_all_variables()

    def entry_activate(self, entry, event=None):
        txt = entry.get_text()
        self.add_var(txt)

    def on_varadd_clicked(self, widget, data=None):
        txt = self.entry.get_text()
        self.add_var(txt)

    def update_all_variables(self):
        #print("update variable")
        for var in self.treestore:
            #print var, var[0]
            #print 'p %s\n' % var[0]
            self.prnt.debuggee_send('p %s\n' % var[0], update=False)
            #self.prnt.debuggee.send('p %s\n' % var[0])
            #self.prnt.handle_debuggee_output()
    
    def update_variable(self, var, value):
        #print 'update variable', self.treestore.get(self.treedict[var],0,1)
        self.treestore.set(self.treedict[var], 1, value)
        self.treestore.set(self.treedict[var], 2, 'white')
        
    def update_variable_error(self, var):
        self.treestore.set(self.treedict[var], 2, 'red')
        self.treestore.set(self.treedict[var], 1, None)

    def modify_font(self, font_desc):
        self.treeview.modify_font(font_desc)
        self.entry.modify_font(font_desc)
        self.addbutton.child.modify_font(font_desc)
        self.lbl.modify_font(font_desc)

    def deactivate(self):
        self.entry.set_sensitive(False)
        self.addbutton.set_sensitive(False)
        
    def activate(self):
        self.entry.set_sensitive(True)
        self.addbutton.set_sensitive(True)
