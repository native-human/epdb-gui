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

class TimelineBox(gtk.VBox):
    def __init__(self, dbgcom, guiactions):
        
        gtk.VBox.__init__(self)
        
        self.dbgcom = dbgcom
        self.guiactions = guiactions
        #self.prnt.actiongroup.add_actions([
        #            ('ActivateTimeline', None, '_Activate', None, "Activate Timeline",
        #             None),
        #            ('RemoveTimeline', None, '_Remove', None, "Remove Timeline",
        #             None)
        #            ])
        #
        #self.popup = self.prnt.uimanager.get_widget('/TimelineMenu')
        
        #print 'popup', self.popup
        self.lbl = gtk.Label("Timelines")
        self.treestore = gtk.TreeStore(gobject.TYPE_STRING, str)
        self.add_timeline('head')

        self.timeline_renderer = gtk.CellRendererText()
        self.timeline_renderer.set_property('background', 'red')
        
        self.scrolledwindow = gtk.ScrolledWindow()
        self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolledwindow.show()
        
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_headers_visible(False)
        self.treeview.connect('button-press-event', self.on_treeview_button_press_event)
        self.treeview.connect("row-activated", self.on_treeview_activated)

        self.timelinebox = gtk.HBox()
        self.entry = gtk.Entry()
        self.entry.connect("activate", self.entry_activate)
        self.addbutton = gtk.Button('Add')
        self.addbutton.connect('clicked', self.on_timeline_add_click)
        
        self.timelinebox.pack_start(self.entry, True, True, 0)
        self.timelinebox.pack_start(self.addbutton, False, False, 0)
        
        self.timelinebox.show()
        self.entry.show()
        self.addbutton.show()
        self.lbl.show()
        
        self.tvcolumn = gtk.TreeViewColumn('Column 0', self.timeline_renderer, text=0, background=1)
        self.treeview.append_column(self.tvcolumn)
        
        self.treeview.show()
        self.pack_start(self.lbl, False, False, 0)
        self.pack_start(self.timelinebox, False, False, 0)
        self.pack_start(self.scrolledwindow, True, True, 0)
        self.scrolledwindow.add(self.treeview)
        self.show()
    
    def reset(self):
        "Reset the timelinebox to its initial state"
        self.treestore.clear()
        self.add_timeline('head')
    
    def on_treeview_button_press_event(self, treeview, event):
        if event.button == 3:
            x = int(event.x)
            y = int(event.y)
            time = event.time
            pthinfo = treeview.get_path_at_pos(x, y)
            if pthinfo is not None:
                path, col, cellx, celly = pthinfo
                treeview.grab_focus()
                treeview.set_cursor( path, col, 0)
                # TODO make popup menu to remove breakpoint
                #self.popup.popup( None, None, None, event.button, time)
            return True
    
    def new_timeline(self, name):
        self.dbgcom.newtimelinesuc = None
        self.dbgcom.sendLine('newtimeline %s\n' % name)
        #self.prnt.handle_debuggee_output()
        #if self.dbgcom.newtimelinesuc == True:
        #    self.add_timeline(self.entry.get_text())
        #else:
        #    #print self.prnt.newtimelinesuc
        #    "TODO put failed message into status line"
        self.entry.set_text('')
        #self.guiactions.update_snapshots()
        
    #def add_new_timeline(self, name):
    #    self.add_timeline(name)
    #    self.guiactions.update_snapshots()
    #
    def entry_activate(self, entry, event=None):
        return self.new_timeline(entry.get_text())
    
    def on_timeline_add_click(self, widget, data=None):
        self.new_timeline(self.entry.get_text())

    def on_treeview_activated(self, treeview, row, col):
        #print "treeview activated", row, col
        model = treeview.get_model()
        self.timelineswitchsuc = None
        #self.prnt.debuggee.send('switch_timeline %s\n' % model[row][0])
        #self.prnt.handle_debuggee_output()
        # TODO: this is not correct here. There is no parent.
        self.dbgcom.sendLine('switch_timeline %s\n' % model[row][0])
        if self.dbgcom.timelineswitchsuc:
            for e in self.treestore:
                e[1]='white'
            text = model[row][0]
            model[row][1] = 'green'
            #print "activated", treeview, text
            
    def add_timeline(self, name):
        for e in self.treestore:
            e[1]='white'
        self.treestore.append(None, (name,'green'))
    
    def modify_font(self, font_desc):
        self.treeview.modify_font(font_desc)
        self.addbutton.child.modify_font(font_desc)
        self.entry.modify_font(font_desc)
        self.lbl.modify_font(font_desc)
    
    def activate(self):
        self.addbutton.set_sensitive(True)
        self.entry.set_sensitive(True)
    
    def deactivate(self):
        self.addbutton.set_sensitive(False)
        self.entry.set_sensitive(False)
