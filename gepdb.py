#!/usr/bin/env python

# example helloworld.py

import pygtk
pygtk.require('2.0')
import gtk
import gtksourceview2
import gobject
import pango

import sys
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


class SnapshotBox(gtk.VBox):
    def __init__(self, prnt):
        gtk.VBox.__init__(self)
        self.prnt = prnt

        self.treestore = gtk.TreeStore(str, str)
        self.treestore.append(None, ('Test','Loc'))
        self.var_renderer = gtk.CellRendererText()
        #self.timeline_renderer.set_property('background', 'red')
        self.lbl = gtk.Label('Snapshots')
        self.lbl.show()
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_headers_visible(False)
        
        self.treeview.show()
        #print "Treestore", self.treestore.append(None, ('Blah','blue', 'green'))
        self.treedict = {}
        self.tvcolumn1 = gtk.TreeViewColumn('Column 0', self.var_renderer, text=0)
        self.tvcolumn2 = gtk.TreeViewColumn('Column 1', self.var_renderer, text=1)
        
        self.treeview.append_column(self.tvcolumn1)
        self.treeview.append_column(self.tvcolumn2)
        
        #self.pack_start(self.timelinebox, False, False, 0)
        self.pack_start(self.lbl, False, False, 0)
        self.pack_start(self.treeview, True, True, 0)
        self.show()

    def update_snapshots(self):
        "Send to the debuggee the request to update the resources"
        self.prnt.debuggee_send('timeline_snapshots', update=False)
    
    def add_snapshot(self, id, ic):
        "Add a resource to the store"
        self.treestore.append(None, (id, ic))
        
    def clear_snapshots(self):
        "Clears all resources from the window"
        self.treestore.clear()
    
    def modify_font(self, font_desc):
        self.treeview.modify_font(font_desc)
        self.lbl.modify_font(font_desc)

class ResourceBox(gtk.VBox):
    def __init__(self, prnt):
        gtk.VBox.__init__(self)
        self.prnt = prnt

        self.treestore = gtk.TreeStore(str, str)
        self.treestore.append(None, ('Test','Loc'))
        self.var_renderer = gtk.CellRendererText()
        #self.timeline_renderer.set_property('background', 'red')
        self.lbl = gtk.Label('Resources')
        self.lbl.show()
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_headers_visible(False)
        
        self.treeview.show()
        #print "Treestore", self.treestore.append(None, ('Blah','blue', 'green'))
        self.treedict = {}
        self.tvcolumn1 = gtk.TreeViewColumn('Column 0', self.var_renderer, text=0)
        self.tvcolumn2 = gtk.TreeViewColumn('Column 1', self.var_renderer, text=1)
        
        self.treeview.append_column(self.tvcolumn1)
        self.treeview.append_column(self.tvcolumn2)
        
        #self.pack_start(self.timelinebox, False, False, 0)
        self.pack_start(self.lbl, False, False, 0)
        self.pack_start(self.treeview, True, True, 0)
        self.iter_dict = {}
        self.rows = 0
        self.show()

    def update_resources(self):
        "Send to the debuggee the request to update the resources"
        self.prnt.debuggee_send('resources', update=False)
    
    def add_resource(self, type, location):
        "Add a resource to the store"
        iter = self.treestore.append(None, (type, location))
        self.iter_dict[(type,location)] = iter
        self.rows += 1
        #self.treestore.append(iter, ('Test', 'Test'))
        #self.treestore.append(iter, ('Test', 'Test'))
        
    def add_resource_entry(self, type, location, ic, id):
        "Add resource data to the resource"
        self.treestore.append(self.iter_dict[(type,location)], (ic, id))
        for i in range(self.rows):
            self.treeview.expand_row(str(i), True)
    
    def clear_resources(self):
        "Clears all resources from the window"
        self.rows = 0
        self.iter_dict = {}
        self.treestore.clear()
        
    def modify_font(self, font_desc):
        self.treeview.modify_font(font_desc)
        self.lbl.modify_font(font_desc)        

class Varbox(gtk.VBox):
    def __init__(self, prnt):
        gtk.VBox.__init__(self)
        self.prnt = prnt

        self.treestore = gtk.TreeStore(str, str, str)
 
        self.var_renderer = gtk.CellRendererText()
        #self.timeline_renderer.set_property('background', 'red')
        self.lbl = gtk.Label('Variables')
        self.lbl.show()
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_headers_visible(False)
        self.entrybox = gtk.HBox()
        self.entry = gtk.Entry()
        self.entry.show()
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
        self.pack_start(self.treeview, True, True, 0)
        self.show()
        
    
    def reset(self):
        self.treestore.clear()
        self.treedict = {}
        
    def on_varadd_clicked(self, widget, data=None):
        #print 'Add variable', self.entry.get_text()
        txt = self.entry.get_text()
        if txt in self.treedict:
            pass
            # TODO statusline error
        else:
            id = self.treestore.append(None, (self.entry.get_text(), None, 'white'))
            self.treedict[txt] = id
            self.entry.set_text('')
        self.update_all_variables()
        #self.update_variable(txt, 'blup')

    def update_all_variables(self):
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

class TimelineBox(gtk.VBox):
    def __init__(self, prnt):
        
        gtk.VBox.__init__(self)
        
        self.prnt = prnt
        self.prnt.actiongroup.add_actions([
                    ('ActivateTimeline', None, '_Activate', None, "Activate Timeline",
                     None),
                    ('RemoveTimeline', None, '_Remove', None, "Remove Timeline",
                     None)
                    ])
        
        self.popup = self.prnt.uimanager.get_widget('/TimelineMenu')
        #print 'popup', self.popup
        self.lbl = gtk.Label("Timelines")
        self.treestore = gtk.TreeStore(gobject.TYPE_STRING, str)
        self.add_timeline('head')

        self.timeline_renderer = gtk.CellRendererText()
        self.timeline_renderer.set_property('background', 'red')
        
        self.treeview = gtk.TreeView(self.treestore)  # TODO rename to timeline treeview
        self.treeview.set_headers_visible(False)
        self.treeview.connect('button-press-event', self.on_treeview_button_press_event)
        self.treeview.connect("row-activated", self.on_treeview_activated)

        self.timelinebox = gtk.HBox()
        self.entry = gtk.Entry()
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
        self.pack_start(self.treeview, True, True, 0)
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
                self.popup.popup( None, None, None, event.button, time)
            return True
    
    def on_timeline_add_click(self, widget, data=None):
        #print 'Add clicked', self.entry.get_text()
        self.prnt.statusbar.push(self.prnt.context_id, "Add clicked")
        self.prnt.newtimelinesuc = None
        self.prnt.debuggee_send('newtimeline %s\n' % self.entry.get_text())
        #self.prnt.handle_debuggee_output()
        if self.prnt.newtimelinesuc == True:
            self.add_timeline(self.entry.get_text())
        else:
            #print self.prnt.newtimelinesuc
            "TODO put failed message into status line"
        self.entry.set_text('')
        self.prnt.snapshotbox.clear_snapshots()
        self.prnt.snapshotbox.update_snapshots()


    def on_treeview_activated(self, treeview, row, col):
        #print "treeview activated", row, col
        model = treeview.get_model()
        self.timelineswitchsuc = None
        #self.prnt.debuggee.send('switch_timeline %s\n' % model[row][0])
        #self.prnt.handle_debuggee_output()
        self.prnt.debuggee_send('switch_timeline %s\n' % model[row][0])
        if self.prnt.timelineswitchsuc:
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
        <popup name="BreakpointMenu">
            <menuitem action="Breakpoint"/>
        </popup>
        <popup name="TimelineMenu">
            <menuitem action="ActivateTimeline"/>
            <menuitem action="RemoveTimeline"/>
        </popup>
        <popup name="VarMenu">
            <menuitem action="RemoveVar"/>
        </popup>
        </ui>'''
    def norestart(self):
        self.running = False

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        return False  # False means window get destroyed

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()

    def toggle_breakpoint(self, widget, data=None):
        #print "toggle breakpoint", self.breakpointlineno
        if not self.breakpointdict.get(self.breakpointlineno):
            self.debuggee.send('break %s\n'%self.breakpointlineno)
            self.handle_debuggee_output()
            if self.breakpointsuccess:
                mark = self.textbuffer.create_source_mark(None, "breakpoint",
                        self.textbuffer.get_iter_at_line(self.breakpointlineno-1))
                print "Make breakpoint with no", self.breakpointno
                self.breakpointdict[self.breakpointlineno] = self.breakpointno
            else:
                "TODO put can't set breakpoint into status line"
                #print self.breakpointdict
        else:
            bpno = self.breakpointdict.get(self.breakpointlineno)
            if not bpno:
                print "TODO put error in status line"
                return
            
            self.clearbpsuccess = None
            print "Clear Breakpoint {0}".format(bpno)
            self.debuggee_send('clear {0}\n'.format(bpno))
            #self.debuggee.send('clear {0}\n'.format(bpno))
            #self.handle_debuggee_output()
            if self.clearbpsuccess == True:
                start = self.textbuffer.get_iter_at_line(self.breakpointlineno-1)
                end = self.textbuffer.get_iter_at_line(self.breakpointlineno)
                self.textbuffer.remove_source_marks(start, end, category=None)
                del self.breakpointdict[self.breakpointlineno]
                "Toggle breakpoint"
                "clear from dictionary"
            elif self.clearbpsuccess == False:
                print "Couldn't delete breakpoint"
                "Error message"
            else:
                print 'Critical Error'
            #print "Deleting breakpoints not implemented yet"

    def rstep_click(self, widget, data=None):
        self.debuggee_send('rstep')
        print('rstep')

    def restart_click(self, widget, data=None):
        print('Restart')
        self.outputbuffer.set_text('')
        self.debugbuffer.set_text('')
        self.timelinebox.reset()
        txt = open(self.filename, 'r').read()
        self.textbuffer.set_text(txt)
        self.debuggee = pexpect.spawn("python3 -m epdb {0}".format(self.filename), timeout=None)
        #self.handle_debuggee_output(ignorelines=0)
        self.debuggee_send()

    def next_click(self, widget, data=None):
        print('Next')
        self.debuggee_send('next')

    def rnext_click(self, widget, data=None):
        print('RNext')
        self.debuggee_send('rnext')

    def continue_click(self, widget, data=None):
        print('Continue')
        self.debuggee_send('continue')
    def rcontinue_click(self, widget, data=None):
        self.debuggee_send('rcontinue')
    
    def step_click(self, widget, data=None):
        print 'Step clicked'
        self.debuggee_send('step')
        
    
    def textview_expose(self, widget, event):
        if event.window != widget.get_window(gtk.TEXT_WINDOW_TEXT):
         
            return
        #print 'Expose event'
        visible_rect = widget.get_visible_rect()
        #it = widget.get_buffer().get_iter_at_line(4)
        it = self.lineiter
        y1,y2 = widget.get_line_yrange(it)
        #print visible_rect
        curline = widget.get_buffer().get_iter_at_mark(widget.get_buffer().get_insert() ).get_line()
        #print curline
        #print 'window: ', widget.get_window(gtk.TEXT_WINDOW_TEXT)
        width, height = widget.allocation.width, widget.allocation.height
        context = event.window.cairo_create()
        context.rectangle(0, 0, width, height)
        context.clip()
        context.set_line_width(1.0)
        context.set_source_rgba(1,1,
                                0,.25)
        context.rectangle(0,y1-visible_rect.y, width, y2)
        context.fill()

    def debuggee_send(self, line=None, update=True):
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
                self.varbox.update_all_variables()
                self.resourcebox.update_resources()
                self.snapshotbox.update_snapshots()
                print "NORMAL RETURN"
        elif returnmode == 'intermediate':
            print 'INTERMEDIATE RETURN'
            pass
        else:
            print "Unknown return mode"
            
    def handle_debuggee_output(self, ignorelines=1):
        #print 'handle_output called'
        returnmode = 'normal'
        try:
            while True:
                line = self.debuggee.readline()
                if ignorelines > 0:
                    #print "line ignored:", line
                    ignorelines -= 1
                    continue
                #print(line)
                m = re.match('> ([<>/a-zA-Z0-9_\.]+)\(([0-9]+)\).*', line)
                if m:
                    self.append_debugbuffer(line)
                    if m.group(1) == '<string>':
                        continue
                    lineno = int(m.group(2))
                    self.lineiter = self.textbuffer.get_iter_at_line(lineno-1)
                    self.textbuffer.place_cursor(self.lineiter)
                    print m.group(1)
                    
                elif line.startswith('-> '):
                    print 'At line: ', line[3:]
                    print
                    #break
                    
                elif line.startswith('(Pdb)') or line.startswith('(Epdb)'):
                    #print 'Normal break'
                    returnmode = 'normal'
                    break
                elif line.startswith("***"):
                    print line
                    self.append_debugbuffer(line)
                elif line.startswith('#'):
                    #self.append_debugbuffer(line[1:])
                    #Breakpoint 1 at /home/patrick/myprogs/epdb/example.py:8
                    bpsuc = re.match('#Breakpoint ([0-9]+) at ([<>/a-zA-Z0-9_\.]+):([0-9]+)', line)
                    clbpsuc = re.match("#Deleted breakpoint ([0-9]+)", line)
                    icm = re.match("#ic: (\d+) mode: (\w+)", line)
                    #print "interesting line '{0}'".format(line.replace(" ", '_'))
                    prm = re.match("#var# ([<>/a-zA-Z0-9_\. \+\-]+) \|\|\| ([<>/a-zA-Z0-9_\. ]+)\r\n", line)
                    perrm = re.match("#varerror# ([<>/a-zA-Z0-9_\. \+\-]+)\r\n", line)
                    resm = re.match("#resource#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
                    resem = re.match("#resource_entry#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
                    tsnapm = re.match("#tsnapshot#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
                    
                    if line.startswith('#*** Blank or comment'):
                        self.breakpointsuccess = False
                    elif line.startswith("#expect input#"):
                        self.input_entry.set_sensitive(True)
                        self.input_entry.grab_focus()
                        self.modelbl.set_markup(
                            'Mode: <span color="red">{0}</span>'.format('INPUT'))
                        returnmode = 'intermediate'
                        break
                    elif line.startswith("#show resources#"):
                        self.resourcebox.clear_resources()
                    elif line.startswith("#timeline_snapshots#"):
                        self.snapshotbox.clear_snapshots()
                    elif resm:
                        #print "resm", resm.group(1), resm.group(2)
                        self.resourcebox.add_resource(resm.group(1), resm.group(2))
                    elif resem:
                        self.resourcebox.add_resource_entry(resem.group(1), resem.group(2), resem.group(3), resem.group(4))
                    elif tsnapm:
                        print tsnapm, tsnapm.group(1), tsnapm.group(2)
                        self.snapshotbox.add_snapshot(tsnapm.group(1), tsnapm.group(2))
                    elif line.startswith('#-->'):
                        self.outputbuffer.set_text('')
                    elif line.startswith('#->'):
                        self.append_output(line[3:])
                    elif bpsuc:
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
                        self.modelbl.set_markup(
                            'Mode: <span color="red">{0}</span>'.format(mode))
                        self.iclbl.set_markup('Ic: {0}'.format(ic))
                        #print "New markup set", mode, ic
                    elif prm:
                        #print 'Got update', line
                        var = prm.group(1)
                        value = prm.group(2)
                        self.varbox.update_variable(var, value)
                        #print var, value
                    elif perrm:
                        #print 'Got var err update'
                        var = perrm.group(1)
                        #print var
                        self.varbox.update_variable_error(var)
                    else:
                        'print "OTHER LINE", line'
                        self.append_debugbuffer(line[1:])
                elif line.startswith('--Return--'):
                    print 'Return'
                    self.append_output(line)
                    #dialog = RestartDlg(self)
                    #dialog.run()
                elif line.startswith('The program finished and will be restarted'):
                    print 'Finished: ', line
                    dlg = MessageDlg(title='Restart', message='The program has finished and will be restarted now', action=self.restart)
                    dlg.run()
                    #break
                else:
                    #print line
                    self.append_output(line)
        except pexpect.TIMEOUT:
            print "TIMEOUT"
            #gtk.main_quit()
        self.text.scroll_mark_onscreen(self.textbuffer.get_insert())
        return returnmode

    def cursor_moved(self, widget,  step_size, count, extend_selection):
        #print('Moved')
        self.textbuffer.place_cursor(self.lineiter)
        
    def text_clicked(self, widget, event):
        #print('Clicked')
        self.textbuffer.place_cursor(self.lineiter)

    def append_output(self, txt):
        iter = self.outputbuffer.get_end_iter()
        print("append_txt", repr(txt))
        self.outputbuffer.insert(iter, txt)
        self.output.scroll_mark_onscreen(self.outputbuffer.get_insert())
        #print 'inserted'

    def append_debugbuffer(self, txt):
        iter = self.debugbuffer.get_end_iter()
        self.debugbuffer.insert(iter, txt)
        self.debug.scroll_mark_onscreen(self.debugbuffer.get_insert())
        #text_view.scroll_mark_onscreen(text_buffer.get_insert())

    def button_release_sv(self, view, event):
        if event.window == view.get_window(gtk.TEXT_WINDOW_LEFT):
            #print "gutter clicked LEFT"
            if event.button == 3:
                #print "Button Right"
                
                #visible = widget.get_visible_rect()
                #it = view.get_buffer().get_iter_at_line(linenumber)
                
                x_buf, y_buf = view.window_to_buffer_coords(gtk.TEXT_WINDOW_LEFT,
                                                    int(event.x), int(event.y))
                linenoiter, linenocoord = view.get_line_at_y(y_buf)
                #print "coords", x_buf, y_buf
                #print "lineno", linenoiter.get_line()
                self.breakpointlineno = linenoiter.get_line() + 1
                self.breakpointmenu.popup( None, None, None, event.button, event.get_time())
            #else:
 
            #    print "Other Button:", event.button
        #else:
        #    print "gutter clicked RIGHT"
    #def add_timeline(self, name):
    #    for e in self.treestore:
    #        e[1]='white'
    #    self.treestore.append(None, (name,'green'))
    
    def open_clicked(self, widget, data=None):
        def chooser_cancel(widget, data=None):
            chooser.destroy()

        def chooser_ok(widget, data=None):
            print "chooser ok", chooser.get_filename()
            self.filename = chooser.get_filename()
            self.outputbuffer.set_text('')
            self.debugbuffer.set_text('')
            self.timelinebox.reset()
            txt = open(self.filename, 'r').read()
            # Delete breakpoints
            self.breakpointdict = {}
            start = self.textbuffer.get_start_iter()
            end = self.textbuffer.get_end_iter()
            self.textbuffer.remove_source_marks(start, end, category=None)
            self.textbuffer.set_text(txt)
            
            self.snapshotbox.clear_snapshots()
            self.resourcebox.clear_resources()
            self.timelinebox.reset()
            self.varbox.reset()
            self.debuggee = pexpect.spawn("python3 -m epdb {0}".format(self.filename), timeout=None)
            #self.handle_debuggee_output(ignorelines=0)
            self.debuggee_send()
            chooser.destroy()
            
        print "open clicked"
        chooser = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN)
        chooser.set_current_folder("/home/patrick/myprogs/gui")
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
        self.font = self.font_dialog.get_font_name()
        if self.window:
            font_desc = pango.FontDescription(self.font)
            if font_desc:
                self.text.modify_font(font_desc)
                self.debug.modify_font(font_desc)
                self.varbox.modify_font(font_desc)
                self.timelinebox.modify_font(font_desc)
                self.toolbar.modify_font(font_desc)
                self.resourcebox.modify_font(font_desc)
                self.snapshotbox.modify_font(font_desc)
                
    def font_dialog_destroyed(self, data=None):
        self.font_dialog = None
        
    def input_entry_activate(self, entry):
        #print 'activate', entry.get_text()
        self.debuggee.send(entry.get_text()+'\n')
        entry.set_text('')
        entry.set_sensitive(False)
        self.debuggee_send()
        #self.handle_debuggee_output(ignorelines=0)
        
        #print "returned from handle_debuggee_output"
    
    def lbvpane_expose(self, pane, event):
        print "lbvpane_expose", pane
        rect = self.lbvpane.get_allocation()
        print "Size request", rect.width, rect.height, rect.x, rect.y
        self.lbvpane.set_position(rect.height/2)
        self.lbvpane.disconnect(
            self.lbvpane_expose_handlerid)
    
    def __init__(self, filename):
        self.filename = filename
        self.debuggee = pexpect.spawn("python3 -m epdb {0}".format(filename), timeout=None)
        
        self.running = True
        
        # create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(640,480)
        self.window.connect("delete_event", self.delete_event)
    
        self.window.connect("destroy", self.destroy)
    
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
                                 ('Breakpoint', None, '_Breakpoint', None, "Toggle Breakpoint", self.toggle_breakpoint)])
        actiongroup.get_action('Quit').set_property('short-label', '_Quit')
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(self.ui)
        
        self.toplevelbox = gtk.VBox()
        #self.toplevelhbox = gtk.HBox()
        self.toplevelhpaned1 = gtk.HPaned()
        self.toplevelhpaned2 = gtk.HPaned()
        self.leftbox = gtk.VBox()
        self.lbvpane = gtk.VPaned()
        self.timelinebox = TimelineBox(self)
        self.varbox = Varbox(self)
        self.resourcebox = ResourceBox(self)
        self.leftbox.show()
        self.leftbox.pack_start(self.lbvpane, True, True, 0)
        self.lbvpane.pack1(self.timelinebox)
        self.lbvpane.pack2(self.varbox)
        self.lbvpane.show()
        self.rightbox = gtk.VBox()
        self.snapshotbox = SnapshotBox(self)
        self.rbvpane = gtk.VPaned()
        self.rbvpane.pack1(self.resourcebox, resize=True, shrink=True)
        self.rbvpane.pack2(self.snapshotbox, resize=True, shrink=True)
        self.rbvpane.show()
        self.rightbox.pack_start(self.rbvpane)
        self.rightbox.show()
        #self.leftbox.pack_start(self.timelinebox, True, True, 0)
        #self.leftbox.pack_start(self.varbox, True, True, 0)
        
        self.outputbuffer = gtk.TextBuffer()
        self.output = gtk.TextView(self.outputbuffer)
        #self.append_output('Blah')
        #self.outputbuffer.set_text("Hallo Welt")
        self.output.set_editable(False)
        #self.output.set_property("height-request", 80)
    
        self.mainbox = gtk.VBox()
    
        self.textbuffer = gtksourceview2.Buffer()
        self.text = gtksourceview2.View(self.textbuffer)
        #self.text.set_property("can-focus", False)
        self.text.connect("expose-event", self.textview_expose)
        self.text.connect("move-cursor", self.cursor_moved)
        self.text.connect("button-release-event", self.text_clicked)
        self.text.set_editable(False)
        
        #self.textbuffer = self.text.get_buffer()
        txt = open(filename, 'r').read()
        self.textbuffer.set_text(txt)
        self.lineiter = self.textbuffer.get_iter_at_line(0)
        self.languagemanager = gtksourceview2.LanguageManager()
        
        l = self.languagemanager.get_language("python")
        self.textbuffer.set_language(l)
        self.text.set_show_line_marks(True)
        self.text.set_show_line_numbers(True)
        self.text.set_highlight_current_line(True)
        self.text.scroll_mark_onscreen(self.textbuffer.get_insert())
        self.vpaned = gtk.VPaned()

        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.add(self.text)
        
        self.debugbuffer = gtk.TextBuffer()
        self.debug = gtk.TextView(self.debugbuffer)
        self.debug.set_editable(False)
        
        self.debug_sw = gtk.ScrolledWindow()
        self.debug_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.debug_sw.add(self.debug)
        
        self.outputbox = gtk.VBox()
        self.output_sw = gtk.ScrolledWindow()
        self.output_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.output_sw.add(self.output)
        
        self.input_entry = gtk.Entry()
        #self.input_entry.set_editable(False)
        #gray = gtk.gdk.Color(red=30000, green=30000, blue=30000, pixel=5)
        #gray = gtk.gdk.Color('#999')
        #self.input_entry.modify_bg(gtk.STATE_NORMAL, gray)
        self.input_entry.set_sensitive(False)
        self.input_entry.show()
        self.input_entry.connect("activate", self.input_entry_activate)
        self.outputbox.pack_start(self.output_sw, True, True, 0)
        self.outputbox.pack_start(self.input_entry, True, True, 0)
        self.outputbox.show()
        
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        self.output_tab_lbl = gtk.Label('Output')
        self.output_tab_lbl.show()
        self.debug_tab_lbl = gtk.Label('Debug')
        self.debug_tab_lbl.show()
        self.notebook.append_page(self.outputbox, self.output_tab_lbl)
        self.notebook.append_page(self.debug_sw, self.debug_tab_lbl)
        
        self.mainbox.pack_start(self.vpaned, True, True, 0)
        self.vpaned.pack1(self.sw, resize=True, shrink=True)
        #self.vpaned.pack2(self.output, resize=False, shrink=False)
        self.vpaned.pack2(self.notebook, resize=False, shrink=False)
        #self.rightbox.pack_start(self.sw, True, True, 0)
        # self.rightbox.pack_start(self.buttonbox, False, False, 0)
        #self.rightbox.pack_start(self.output, False, False, 0)
        
        self.toplevelhpaned1.pack1(self.leftbox, resize=False, shrink=False)
        self.toplevelhpaned1.pack2(self.mainbox, resize=True, shrink=True)
        self.toplevelhpaned2.pack1(self.toplevelhpaned1, resize=True, shrink=True)
        self.toplevelhpaned2.pack2(self.rightbox, resize=False, shrink=False)
        #self.toplevelhbox.pack_start(self.leftbox, False, False, 0)
        #self.toplevelhbox.pack_start(self.rightbox, True, True, 0)
        
        self.toolbar = Toolbar(self)
        
        menubar = uimanager.get_widget('/MenuBar')
        self.breakpointmenu = uimanager.get_widget('/BreakpointMenu')
        #print "Menu type", type(self.breakpointmenu)
        self.toplevelbox.pack_start(menubar, False)
        menubar.show()

        self.statusbar = gtk.Statusbar()
        self.context_id = self.statusbar.get_context_id("gepdb")
        self.modelbl = gtk.Label("Mode label")
        self.modelbl.set_markup('Mode: <span color="red">normal</span>')
        self.modelbl.show()
        
        self.iclbl = gtk.Label("Ic label")
        self.iclbl.set_markup('Ic: 0')
        self.iclbl.show()
        self.statusbar.pack_start(self.iclbl, False, False, 0)
        self.statusbar.pack_start(self.modelbl, False, False, 20)
        self.statusbar.show()

        self.toplevelbox.pack_start(self.toolbar, False, False, 0)
        #self.toplevelbox.pack_start(self.toplevelhbox, True, True, 0)
        self.toplevelbox.pack_start(self.toplevelhpaned2, True, True, 0)
        self.toplevelbox.pack_start(self.statusbar, False, False, 0)
        #self.window.add(self.text)

        #self.window.add(self.toolbar)
        self.window.add(self.toplevelbox)
        self.window.show()
        self.mainbox.show()
        self.text.show()
        self.output.show()
        self.output_sw.show(
            
        )
        self.debug.show()
        self.debug_sw.show()
        #self.treeview.show()
        #self.toplevelhbox.show()
        self.toplevelhpaned1.show()
        self.toplevelhpaned2.show()
        self.sw.show()
        self.vpaned.show()
        self.toplevelbox.show()
        self.notebook.show()
        
        self.debuggee_send()
        #self.handle_debuggee_output(ignorelines=0)
        
        #mark = self.textbuffer.create_source_mark("b1", "breakpoint", self.textbuffer.get_iter_at_line(1))
        self.breakpointdict = {} # lineno: bpno
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size("breakpoint.png", 64, 64)
        
        self.text.set_mark_category_icon_from_pixbuf("breakpoint", pixbuf)
        self.text.connect('button-release-event', self.button_release_sv)
        self.lbvpane_expose_handlerid = self.lbvpane.connect('expose-event', self.lbvpane_expose)
    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start the application logic for the poll website')
    parser.add_argument('file', help='Give the filename to execute in debug mode', nargs=1)
    args = parser.parse_args()
    #print args.file[0]

    guipdb = GuiPdb(args.file[0])
    guipdb.main()

