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

class SnapshotBox(gtk.VBox):
    def __init__(self, dbgcom):
        gtk.VBox.__init__(self)
        self.dbgcom = dbgcom

        self.treestore = gtk.TreeStore(str, str)
        self.treestore.append(None, ('Test','Loc'))
        self.var_renderer = gtk.CellRendererText()
        #self.timeline_renderer.set_property('background', 'red')
        self.lbl = gtk.Label('Snapshots')
        self.lbl.show()
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_headers_visible(True)
        
        self.scrolledwindow = gtk.ScrolledWindow()
        self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolledwindow.show()
        
        self.treeview.show()
        #print "Treestore", self.treestore.append(None, ('Blah','blue', 'green'))
        self.treedict = {}
        self.tvcolumn1 = gtk.TreeViewColumn('id', self.var_renderer, text=0)
        self.tvcolumn2 = gtk.TreeViewColumn('ic', self.var_renderer, text=1)
        
        self.idlbl = gtk.Label('id')
        self.idlbl.show()
        
        self.iclbl = gtk.Label('ic')
        self.iclbl.show()
        self.tvcolumn1.set_widget(self.idlbl)
        self.tvcolumn2.set_widget(self.iclbl)
        
        self.treeview.append_column(self.tvcolumn1)
        self.treeview.append_column(self.tvcolumn2)
        
        self.scrolledwindow.add(self.treeview)
    
        self.treeview.connect("row-activated", self.on_treeview_activated)
        
        #self.pack_start(self.timelinebox, False, False, 0)
        self.pack_start(self.lbl, False, False, 0)
        self.pack_start(self.scrolledwindow, True, True, 0)
        self.show()

    def update_snapshots(self):
        "Send to the debuggee the request to update the resources"
        self.dbgcom.send('timeline_snapshots', update=False)
    
    def add_snapshot(self, id, ic):
        "Add a resource to the store"
        self.treestore.append(None, (id, ic))
        
    def clear_snapshots(self):
        "Clears all resources from the window"
        self.treestore.clear()
    
    def modify_font(self, font_desc):
        self.treeview.modify_font(font_desc)
        self.lbl.modify_font(font_desc)
        self.idlbl.modify_font(font_desc)
        self.iclbl.modify_font(font_desc)
    
    def on_treeview_activated(self, treeview, row, col):
        model = treeview.get_model()
        self.timelineswitchsuc = None
        self.dbgcom.send('activate_snapshot %s\n' % model[row][0])