
import twisted
from twisted.internet import gtk2reactor
gtk2reactor.install()
from twisted.internet import interfaces, reactor, protocol, error, address, defer, utils
from twisted.protocols import basic
import pygtk

pygtk.require('2.0')
import gtk
import gtksourceview2
import gobject
import pango
import tempfile

import sys
import os.path
import keyword, token, tokenize, cStringIO, string
import pexpect
import re
import argparse

from timelinebox import TimelineBox
from varbox import Varbox
from snapshotbox import SnapshotBox
from statusbar import Statusbar
from toolbar import Toolbar
from outputbox import OutputBox
from resourcebox import ResourceBox
from editwindow import EditWindow
from messagebox import MessageBox

from dbgcom import DbgComChooser, DbgComFactory, DbgComProtocol, DebuggerCom, DbgProcessProtocol
from guiactions import GuiActions

IMAGEDIR = "/usr/share/gepdb"
    
class GuiPdb:
    ui = '''<ui>
        <menubar name="MenuBar">
          <menu action="File">
            <menuitem action="Open"/>
            <separator/>
            <menuitem action="Quit"/>
          </menu>
          <menu action="View">
            <menuitem action="ChangeFont"/>
          </menu>
        </menubar>
        </ui>'''
    unused = """
        <popup name="TimelineMenu">
            <menuitem action="ActivateTimeline"/>
            <menuitem action="RemoveTimeline"/>
        </popup>
        <popup name="VarMenu">
            <menuitem action="RemoveVar"/>
        </popup>
    """

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        return False  # False means window get destroyed

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        self.debuggercom.quit()
        gtk.main_quit()
        reactor.stop()

    def append_output(self, txt):
        iter = self.outputbox.outputbuffer.get_end_iter()
        #print "append_txt", repr(txt)
        self.outputbox.outputbuffer.insert(iter, txt)
        self.outputbox.output.scroll_mark_onscreen(self.outputbox.outputbuffer.get_insert())

    def append_debugbuffer(self, txt):
        iter = self.outputbox.debugbuffer.get_end_iter()
        self.outputbox.debugbuffer.insert(iter, txt)
        self.outputbox.debug.scroll_mark_onscreen(self.outputbox.debugbuffer.get_insert())
        #text_view.scroll_mark_onscreen(text_buffer.get_insert())
    
    def open_clicked(self, widget, data=None):
        def chooser_cancel(widget, data=None):
            chooser.destroy()

        def chooser_ok(widget, data=None):
            #print "chooser ok", chooser.get_filename()
            self.filename = chooser.get_filename()
            self.outputbox.outputbuffer.set_text('')
            self.outputbox.debugbuffer.set_text('')
            self.timelinebox.reset()
            txt = open(self.filename, 'r').read()
            
            self.snapshotbox.clear_snapshots()
            self.resourcebox.clear_resources()
            self.timelinebox.reset()
            self.varbox.reset()
            self.parameters = ""
            #self.debuggercom.new_debuggee(self.filename, self.parameters)
            self.debuggercom.quit()
            self.dbgprocess = DbgProcessProtocol(self.guiactions)
            self.tempfilename = tempfile.mktemp(dir=self.tempdir)
            factory = DbgComFactory(self.guiactions)
            if self.listen:
                self.listen.stopListening()
            self.listen = reactor.listenUNIX(self.tempfilename, factory)
            r = reactor.spawnProcess(self.dbgprocess, 'epdb', ["epdb", "--uds", self.tempfilename, self.filename], usePTY=True)
            #r = reactor.spawnProcess(self.dbgprocess, 'wc', ["wc", self.filename])
            #print "Reactor.SpawnProcess called: ", r, self.dbgprocess
            self.toolbar.activate()
            chooser.destroy()
            
        chooser = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN)
        #chooser.set_current_folder("/home/patrick/myprogs/gui")
        chooser.connect("file-activated", chooser_ok)
        okbutton = gtk.Button(stock=gtk.STOCK_OK)
        okbutton.connect("clicked", chooser_ok)
        okbutton.show()
        cancelbutton = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancelbutton.connect("clicked", chooser_cancel)
        cancelbutton.show()
        chooser.action_area.pack_start(cancelbutton, False, False, 0)
        chooser.action_area.pack_start(okbutton, False, False, 0)
        chooser.show()
        
    def changefontdlg(self, widget, data=None):
        #print "Change font dialog"
        #window = gtk.FontSelectionDialog("Change font for application")
        if not self.font_dialog:
            window = gtk.FontSelectionDialog("Font Selection Dialog")
            self.font_dialog = window
    
            window.set_position(gtk.WIN_POS_MOUSE)
    
            window.connect("destroy", self.font_dialog_destroyed)
    
            window.ok_button.connect("clicked",
                                     self.font_selection_ok)
            window.ok_button.connect_object("clicked",
                                                lambda wid: wid.destroy(),
                                                self.font_dialog)
            window.cancel_button.connect_object("clicked",
                                                lambda wid: wid.destroy(),
                                                self.font_dialog)
        window = self.font_dialog
        if not (window.flags() & gtk.VISIBLE):
            window.show()
        
        else:
            window.destroy()
            self.font_dialog = None
    
    def font_selection_ok(self, button):
        def change_menu_font(element, font_desc):
            if isinstance(element, gtk.Container):
                for e in element.get_children():
                    change_menu_font(e, font_desc)
            elif isinstance(element, gtk.Bin):
                change_menu_font(e.get_child(), font_desc)
            elif isinstance(element, gtk.Label):
                element.modify_font(font_desc)
        self.font = self.font_dialog.get_font_name()
        if self.window:
            font_desc = pango.FontDescription(self.font)
            if font_desc:
                self.text.modify_font(font_desc)
                #self.debug.modify_font(font_desc)
                self.varbox.modify_font(font_desc)
                self.timelinebox.modify_font(font_desc)
                self.toolbar.modify_font(font_desc)
                self.resourcebox.modify_font(font_desc)
                self.snapshotbox.modify_font(font_desc)
                self.outputbox.modify_font(font_desc)
                self.statusbar.modify_font(font_desc)
                
                change_menu_font(self.menubar, font_desc)
                #self.menubar.modify_font(font_desc)
                
    def font_dialog_destroyed(self, data=None):
        self.font_dialog = None
    
    def lbvpane_expose(self, pane, event):
        "Adjust the pane slider to the middle, when starting."
        rect = self.lbvpane.get_allocation()
        self.lbvpane.set_position(rect.height/2)
        self.lbvpane.disconnect(self.lbvpane_expose_handlerid)
    
    def __init__(self, *args):
        self.tempdir = tempfile.mkdtemp()
        self.guiactions = GuiActions(self)
        self.debuggercom = DbgComChooser()
        self.debuggercom.set_active_dbgcom(DebuggerCom(self.guiactions))
        #self.debuggercom = DebuggerCom(self.guiactions)
        self.listen = None
        
        if len(args) > 0:
            self.filename = args[0]
            self.parameters = " ".join(args[1:])
        else:
            self.filename = None
            
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(640,480)
        self.window.connect("delete_event", self.delete_event)
    
        self.window.connect("destroy", self.destroy)
    
        bugicon = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(IMAGEDIR,"bug.png"), 64, 64)
        self.window.set_icon_list(bugicon)
    
        uimanager = gtk.UIManager()
        self.uimanager = uimanager
    
        self.font_dialog = None
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManagerExample')
        self.actiongroup = actiongroup
        # Create actions
        actiongroup.add_actions([('Quit', gtk.STOCK_QUIT, '_Quit', None,
                                  'Quit the Program', self.destroy),
                                 ('Open', gtk.STOCK_OPEN, '_Open ...', None,
                                  'Open a new file for debugging', self.open_clicked),
                                 ('File', None, '_File'),
                                 ('View', None, '_View'),
                                 ('ChangeFont', None, 'Change Font ...', None, 'Change Font', self.changefontdlg),
                                 ('RadioBand', None, '_Radio Band'),
                                 #('Breakpoint', None, '_Breakpoint', None, "Toggle Breakpoint", self.toggle_breakpoint)
                                 ])
        actiongroup.get_action('Quit').set_property('short-label', '_Quit')
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(self.ui)
        
        self.toplevelbox = gtk.VBox()
        self.toplevelhpaned1 = gtk.HPaned()
        self.toplevelhpaned2 = gtk.HPaned()
        self.leftbox = gtk.VBox()
        self.lbvpane = gtk.VPaned()
        self.timelinebox = TimelineBox(self.debuggercom, self.guiactions)
        self.varbox = Varbox(self.debuggercom, self.guiactions)
        self.resourcebox = ResourceBox(self.debuggercom)
        self.leftbox.show()
        self.leftbox.pack_start(self.lbvpane, True, True, 0)
        self.lbvpane.pack1(self.timelinebox)
        self.lbvpane.pack2(self.varbox)
        self.lbvpane.show()
        self.rightbox = gtk.VBox()
        self.snapshotbox = SnapshotBox(self.debuggercom)
        self.rbvpane = gtk.VPaned()
        self.rbvpane.pack1(self.resourcebox, resize=True, shrink=True)
        self.rbvpane.pack2(self.snapshotbox, resize=True, shrink=True)
        self.rbvpane.show()
        self.rightbox.pack_start(self.rbvpane)
        self.rightbox.show()
        
        self.mainbox = gtk.VBox()
        self.edit_window = EditWindow(self.debuggercom)
        self.edit_window.show()
        
        self.messagebox = MessageBox()
        
        self.vpaned = gtk.VPaned()
        
        self.mainbox.pack_start(self.messagebox, False, False, 0)
        self.mainbox.pack_start(self.vpaned, True, True, 0)
        self.vpaned.pack1(self.edit_window, resize=True, shrink=True)
        self.outputbox = OutputBox(self.debuggercom, self.guiactions)
        self.vpaned.pack2(self.outputbox, resize=False, shrink=False)
        
        self.toplevelhpaned1.pack1(self.leftbox, resize=False, shrink=False)
        self.toplevelhpaned1.pack2(self.mainbox, resize=True, shrink=True)
        self.toplevelhpaned2.pack1(self.toplevelhpaned1, resize=True, shrink=True)
        self.toplevelhpaned2.pack2(self.rightbox, resize=False, shrink=False)
        
        self.toolbar = Toolbar(self.debuggercom, self.guiactions)
        
        self.menubar = uimanager.get_widget('/MenuBar')
        self.breakpointmenu = uimanager.get_widget('/BreakpointMenu')
        self.toplevelbox.pack_start(self.menubar, False)
        self.menubar.show()
        self.statusbar = Statusbar(self)


        self.toplevelbox.pack_start(self.toolbar, False, False, 0)
        self.toplevelbox.pack_start(self.toplevelhpaned2, True, True, 0)
        self.toplevelbox.pack_start(self.statusbar, False, False, 0)
        
        self.window.add(self.toplevelbox)
        self.window.show()
        self.mainbox.show()
        
        self.toplevelhpaned1.show()
        self.toplevelhpaned2.show()

        self.vpaned.show()
        self.toplevelbox.show()
        
        if len(args) > 0:
            #self.debuggercom.new_debuggee(self.filename, self.parameters)
            self.dbgprocess = DbgProcessProtocol(self.guiactions)
            self.tempfilename = tempfile.mktemp(dir=self.tempdir)
            factory = DbgComFactory(self.guiactions)
            self.listen = reactor.listenUNIX(self.tempfilename, factory)
            r = reactor.spawnProcess(self.dbgprocess, 'epdb', ["epdb", "--uds", self.tempfilename, self.filename], usePTY=True)
            #r = reactor.spawnProcess(self.dbgprocess, 'wc', ["wc", self.filename])
            #print "Reactor.SpawnProcess called: ", r, self.dbgprocess
            #p = sp.Popen(["python3", "/usr/lib/python3.1/dist-packages/epdb.py", "--uds", '/tmp/dbgcom', self.filename], stdout=sp.PIPE)
        
        if not self.debuggercom.is_active():
            self.toolbar.deactivate()
        
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(IMAGEDIR,"breakpoint.png"), 64, 64)
        
        self.lbvpane_expose_handlerid = self.lbvpane.connect('expose-event', self.lbvpane_expose)
    
    def main(self):
        #try:
        self.reactor = reactor
        reactor.run()
        gtk.main()
        #except KeyboardInterrupt:
        #    print 'Cleanup'
        #    gtk.main_quit()
        #    self.debuggercom.quit()
        #    reactor.stop()