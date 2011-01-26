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

from timelinebox import TimelineBox
from varbox import Varbox
from snapshotbox import SnapshotBox
from statusbar import Statusbar
from toolbar import Toolbar
from outputbox import OutputBox
from resourcebox import ResourceBox
from editwindow import EditWindow
from messagebox import MessageBox

IMAGEDIR = "/usr/share/gepdb"

class GuiActions:
    def __init__(self, window):
        self.window = window

    def update(self):
        self.window.varbox.update_all_variables()
        self.window.resourcebox.update_resources()
        self.window.snapshotbox.update_snapshots()
        
    def append_debugbuffer(self, line):
        self.window.append_debugbuffer(line)
        
    def show_line(self, filename, lineno):
        self.window.edit_window.show_line(filename, lineno)
        
    def expect_input(self):
        self.window.outputbox.input_entry.set_sensitive(True)
        self.window.outputbox.input_entry.grab_focus()
        self.window.varbox.deactivate()
        self.window.timelinebox.deactivate()
        self.window.toolbar.deactivate()
        self.window.statusbar.set_mode('INPUT')
        
    def clear_resources(self):
        self.window.resourcebox.clear_resources()
        
    def clear_snapshots(self):
        self.window.snapshotbox.clear_snapshots()
        
    def add_resource(self, type, location):
        self.window.resourcebox.add_resource(type, location)
    
    def add_resource_entry(self, type, location, ic, id):
        self.window.resourcebox.add_resource_entry(type, location, ic, id)
     
    def add_snapshot(self, id, ic):   
        self.window.snapshotbox.add_snapshot(id, ic)
        
    def set_output_text(self, text):
        self.window.outputbox.outputbuffer.set_text(text)        
    
    def append_output(self, text):
        self.window.append_output(text)
        
    def set_mode(self, mode):
        self.window.statusbar.set_mode(mode)
    
    def set_ic(self, ic):
        self.window.statusbar.set_ic(ic)

    def set_time(self, time):
        self.window.statusbar.set_ic(time)

    def update_variable(self, var, value):
        self.window.varbox.update_variable(var, value)
    
    def update_variable_error(self, var):
        self.window.varbox.update_variable_error(var)
        
    def show_syntax_error(self, file, lineno):
        self.window.messagebox.show_message("Syntax Error\n")
        self.show_line(file, lineno)
        #self.lineiter = self.textbuffer.get_iter_at_line(lineno-1)
        #self.textbuffer.place_cursor(self.lineiter)
        self.window.toolbar.deactivate()
        
    def reset(self):
        self.window.outputbox.outputbuffer.set_text('')
        self.window.outputbox.debugbuffer.set_text('')
        self.window.timelinebox.reset()
        self.window.edit_window.restart()
        
        self.window.snapshotbox.clear_snapshots()
        self.window.resourcebox.clear_resources()
        self.window.timelinebox.reset()
        self.window.varbox.reset()
    
    def update_snapshots(self):
        self.window.snapshotbox.clear_snapshots()
        self.window.snapshotbox.update_snapshots()
        
    def activate(self):
        self.window.varbox.activate()
        self.window.timelinebox.activate()
        self.window.toolbar.activate()
    
class DebuggerCom:
    def __init__(self, guiactions):
        self.guiactions = guiactions
        self.debuggee = None
        self.params = ""
        
    def new_debuggee(self, filename, params=""):
        self.filename = filename
        self.params = ""
        if self.debuggee:
            self.send("quit")
        self.debuggee = pexpect.spawn("python3 -m epdb {0} {1}".format(self.filename, self.params), timeout=None)
        self.send()
        
    def is_active(self):
        return not self.debuggee is None
        
    def quit(self):
        if self.is_active():
            self.send("quit")
        
    def send(self, line=None, update=True):
        if line:
            if not line.endswith('\n'):
                line += '\n'
            ignorelines = 1
            #print "SEND LINE TO DEBUGGEE: ", line
            self.debuggee.send(line)
        else:
            ignorelines = 0
        returnmode = self.handle_debuggee_output(ignorelines=ignorelines)
        if returnmode == 'normal':
            if update:        
                self.guiactions.update()
        elif returnmode == 'intermediate':
            pass
        else:
            print "Unknown return mode"
    
    def handle_debuggee_output(self, ignorelines=1):
        returnmode = 'normal'
        try:
            while True:
                line = self.debuggee.readline()
                if line == '':
                    break
                if ignorelines > 0:
                    #print "line ignored:", line
                    ignorelines -= 1
                    continue
                #print(line)
                m = re.match('> ([<>/a-zA-Z0-9_\.]+)\(([0-9]+)\).*', line)
                if m:
                    #self.append_debugbuffer(line)
                    self.guiactions.append_debugbuffer(line)
                    if m.group(1) == '<string>':
                        continue
                    lineno = int(m.group(2))
                    self.guiactions.show_line(m.group(1), lineno)
                    #self.edit_window.show_line(m.group(1), lineno)
                    
                elif line.startswith('-> '):
                    pass
                    #print 'At line: ', line[3:]
                    #break
                    
                elif line.startswith('(Pdb)') or line.startswith('(Epdb)'):
                    #print 'Normal break'
                    returnmode = 'normal'
                    break
                elif line.startswith("***"):
                    print line
                    self.guiactions.append_debugbuffer(line)
                elif line.startswith('#'):
                    bpsuc = re.match('#Breakpoint ([0-9]+) at ([<>/a-zA-Z0-9_\.]+):([0-9]+)', line)
                    clbpsuc = re.match("#Deleted breakpoint ([0-9]+)", line)
                    icm = re.match("#ic: (\d+) mode: (\w+)", line)
                    timem = re.match("#time: ([\d.]*)", line)
                    #print "interesting line '{0}'".format(line.replace(" ", '_'))
                    prm = re.match("#var#([<>/a-zA-Z0-9_\. \+\-]+)#([<>/a-zA-Z0-9_\.'\" ]*)#\r\n", line)
                    perrm = re.match("#varerror# ([<>/a-zA-Z0-9_\. \+\-]+)\r\n", line)
                    resm = re.match("#resource#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
                    resem = re.match("#resource_entry#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
                    tsnapm = re.match("#tsnapshot#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
                    synterr = re.match("#syntax_error#([<>/a-zA-Z0-9_\. \+\-]*)#([0-9]+)#\r\n", line)
                    if line.startswith('#*** Blank or comment'):
                        self.breakpointsuccess = False
                    elif line.startswith("#expect input#"):
                        self.guiactions.expect_input()
                        #self.outputbox.input_entry.set_sensitive(True)
                        #self.outputbox.input_entry.grab_focus()
                        #self.varbox.deactivate()
                        #self.timelinebox.deactivate()
                        #self.toolbar.deactivate()
                        #self.statusbar.set_mode('INPUT')
                        returnmode = 'intermediate'
                        break
                    elif line.startswith("#show resources#"):
                        self.guiactions.clear_resources()
                        #self.resourcebox.clear_resources()
                    elif line.startswith("#timeline_snapshots#"):
                        self.guiactions.clear_snapshots()
                        #self.snapshotbox.clear_snapshots()
                    elif resm:
                        #print "resm", resm.group(1), resm.group(2)
                        self.guiactions.add_resource(resm.group(1), resm.group(2))
                        #self.resourcebox.add_resource(resm.group(1), resm.group(2))
                    elif resem:
                        self.guiactions.add_resource_entry(resem.group(1), resem.group(2), resem.group(3), resem.group(4))
                        #self.resourcebox.add_resource_entry(resem.group(1), resem.group(2), resem.group(3), resem.group(4))
                    elif tsnapm:
                        #print tsnapm, tsnapm.group(1), tsnapm.group(2)
                        #self.snapshotbox.add_snapshot(tsnapm.group(1), tsnapm.group(2))
                        self.guiactions.add_snapshot(tsnapm.group(1), tsnapm.group(2))
                    elif line.startswith('#-->'):
                        #self.outputbox.outputbuffer.set_text('')
                        self.guiactions.set_output_text('')
                    elif line.startswith('#->'):
                        self.guiactions.append_output(line[3:])
                        #self.append_output(line[3:])
                    elif bpsuc:
                        #self.append_debugbuffer(line)
                        self.guiactions.append_debugbuffer(line)
                        self.breakpointno = bpsuc.group(1)
                        self.breakpointsuccess = True
                    elif clbpsuc:
                        self.clearbpsuccess = True
                    elif line.startswith("#newtimeline successful"):
                        self.newtimelinesuc = True
                    elif line.startswith("#Switched to timeline"):
                        self.timelineswitchsuc = True
                    elif icm:
                        ic = icm.group(1)
                        mode = icm.group(2)
                        self.guiactions.set_mode(mode)
                        self.guiactions.set_ic(ic)
                        #self.statusbar.set_mode(mode)
                        #self.statusbar.set_ic(ic)
                    elif timem:
                        t = timem.group(1)
                        self.guiactions.set_time(t)
                        #self.statusbar.set_time(t)
                    elif prm:
                        print 'Got prm update', line
                        var = prm.group(1)
                        value = prm.group(2)
                        #self.varbox.update_variable(var, value)
                        self.guiactions.update_variable(var, value)
                        #print var, value
                    elif perrm:
                        print 'Got var err update'
                        var = perrm.group(1)
                        #print var
                        #self.varbox.update_variable_error(var)
                        self.guiactions.update_variable_error(var)
                    elif synterr:
                        print "Syntax Error"
                        file = synterr.group(1)
                        lineno = int(synterr.group(2))
                        
                        self.guiactions.show_syntax_error(file, lineno)
                        #self.messagebox.show_message("Syntax Error\n")
                        #self.lineiter = self.textbuffer.get_iter_at_line(lineno-1)
                        #self.textbuffer.place_cursor(self.lineiter)
                        #self.toolbar.deactivate()
                        
                        #self.text.scroll_mark_onscreen(self.textbuffer.get_insert())
                    else:
                        'print "OTHER LINE", line'
                        self.guiactions.append_debugbuffer(line[1:])
                elif line.startswith('--Return--'):
                    print 'Return'
                    self.guiactions.append_output(line)
                    #dialog = RestartDlg(self)
                    #dialog.run()
                #elif line.startswith('The program finished and will be restarted'):
                #    print 'Finished: ', line
                #    dlg = MessageDlg(title='Restart', message='The program has finished and will be restarted now', action=self.restart)
                #    dlg.run()
                #    #break
                else:
                    #print line
                    self.guiactions.append_output(line)
                    self.guiactions.append_output(line)
        except pexpect.TIMEOUT:
            print "TIMEOUT"
            #gtk.main_quit()
        #self.text.scroll_mark_onscreen(self.textbuffer.get_insert())
        return returnmode


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
        <popup name="TimelineMenu">
            <menuitem action="ActivateTimeline"/>
            <menuitem action="RemoveTimeline"/>
        </popup>
        <popup name="VarMenu">
            <menuitem action="RemoveVar"/>
        </popup>
        </ui>'''

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        return False  # False means window get destroyed

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        self.debuggercom.quit()
        gtk.main_quit()

    def append_output(self, txt):
        iter = self.outputbox.outputbuffer.get_end_iter()
        print "append_txt", repr(txt)
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
            # Delete breakpoints
            #self.breakpointdict = {}
            #start = self.textbuffer.get_start_iter()
            #end = self.textbuffer.get_end_iter()
            #self.textbuffer.remove_source_marks(start, end, category=None)
            #self.textbuffer.set_text(txt)
            
            self.snapshotbox.clear_snapshots()
            self.resourcebox.clear_resources()
            self.timelinebox.reset()
            self.varbox.reset()
            self.parameters = ""
            self.debuggercom.new_debuggee(self.filename)
            self.toolbar.activate()
            chooser.destroy()
            
        chooser = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN)
        chooser.set_current_folder("/home/patrick/myprogs/gui")
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
        self.guiactions = GuiActions(self)
        self.debuggercom = DebuggerCom(self.guiactions)
        
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
        self.varbox = Varbox(self)
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
            self.debuggercom.new_debuggee(self.filename, self.parameters)
        
        if not self.debuggercom.is_active():
            self.toolbar.deactivate()
        
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(IMAGEDIR,"breakpoint.png"), 64, 64)
        
        self.lbvpane_expose_handlerid = self.lbvpane.connect('expose-event', self.lbvpane_expose)
    
    def main(self):
        try:
            gtk.main()
        except KeyboardInterrupt:
            print 'Cleanup'
            self.debuggercom.quit()