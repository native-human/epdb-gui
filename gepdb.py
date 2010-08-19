#!/usr/bin/env python

# example helloworld.py

import pygtk
pygtk.require('2.0')
import gtk
import gtksourceview2 

import sys
import keyword, token, tokenize, cStringIO, string
import pexpect
import re
import argparse

class RestartDlg(gtk.Dialog):
    def __init__(self, parent):
        gtk.Dialog.__init__(self, title='Restart', parent=None, flags=0)
        self.prnt = parent
        restartbutton = gtk.Button('Restart')
        restartbutton.connect("clicked", self.restart_button_clicked)
        self.action_area.pack_start(restartbutton, True, True, 0)
        norestartbutton = gtk.Button("Don't restart")
        norestartbutton.connect("clicked", self.norestart_button_clicked)
        self.action_area.pack_start(norestartbutton, True, True, 0)
        norestartbutton.show()
        restartbutton.show()
        textlabel = gtk.Label('You have finished the end of the program. Do you want to restart?')
        self.vbox.pack_start(textlabel, True, True, 0)
        textlabel.show()
        
        #dialog.run()
    def restart_button_clicked(self, widget, data=None):
        print 'Restart clicked'
        self.prnt.restart()
        self.destroy()
    def norestart_button_clicked(self, widget, data=None):
        print 'No restart clicked'
        self.prnt.norestart()
        self.destroy()
        
class MessageDlg(gtk.Dialog):
    def __init__(self, title='', message='', action=None):
        
        gtk.Dialog.__init__(self, title=title)
        okbutton = gtk.Button('Ok')
        textlabel = gtk.Label(message)
        self.action_area.pack_start(okbutton, True, True, 0)
        if not action is None:
            print 'Register callback'
            okbutton.connect('clicked', action)
        self.vbox.pack_start(textlabel, True, True, 0)
        okbutton.connect('clicked', lambda x: self.destroy())

        textlabel.show()
        okbutton.show()
    
class Toolbar(gtk.HBox):
    def __init__(self, prnt):
        gtk.HBox.__init__(self)
        self.prnt = prnt
        self.rcontinue = gtk.Button("RContinue")
        self.rcontinue.connect("clicked", self.prnt.rcontinue_click, None)
        self.stepback = gtk.Button("rstep")
        self.stepback.connect("clicked", self.prnt.rstep_click, None)
        #self.stepback.connect_object("clicked", gtk.Widget.destroy, self.window)
        self.step = gtk.Button("Step")
        self.step.connect("clicked", self.prnt.step_click, None)
        self.next = gtk.Button("Next")
        self.next.connect("clicked", self.prnt.next_click, None)
        self.rnext = gtk.Button("rnext")
        self.rnext.connect("clicked", self.prnt.rnext_click, None)
        self.cont = gtk.Button("Continue")
        self.cont.connect("clicked", self.prnt.continue_click, None)
        self.restart = gtk.Button("Restart")
        self.restart.connect("clicked", self.prnt.restart_click, None)
        #self.buttonbox = gtk.HBox()
        self.pack_start(self.rcontinue, False, False, 0)
        self.pack_start(self.rnext, False, False, 0)
        self.pack_start(self.stepback, False, False, 0)
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
        #self.buttonbox.show()
        self.stepback.show()
        self.show()

class GuiPdb:
    ui = '''<ui>
        <menubar name="MenuBar">
          <menu action="File">
            <menuitem action="Quit"/>
          </menu>
        </menubar>
        <popup name="BreakpointMenu">
            <menuitem action="Breakpoint"/>
        </popup>
        </ui>'''
    def norestart(self):
        self.running = False
    
    def restart(self, widget=None):
        #self.running = True
        print 'Restart'
        self.outputbuffer.set_text('')

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        return False  # False means window get destroyed

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()

    def toggle_breakpoint(self, widget, data=None):
        print "toggle breakpoint", self.breakpointlineno
        if not self.breakpointdict.get(self.breakpointlineno):
            self.debuggee.send('break %s\n'%self.breakpointlineno)
            self.handle_debuggee_output()
            if self.breakpointsuccess:
                mark = self.textbuffer.create_source_mark(None, "breakpoint",
                        self.textbuffer.get_iter_at_line(self.breakpointlineno-1))
                self.breakpointdict[self.breakpointlineno] = self.breakpointno
            else:
                "TODO put can't set breakpoint into status line"
                print self.breakpointdict
        else:
            bpno = self.breakpointdict.get(self.breakpointlineno)
            if not bpno:
                print "TODO put error in status line"
                return
            
            self.clearbpsuccess = None
            self.debuggee.send('clear {0}\n'.format(bpno))
            self.handle_debuggee_output()
            if self.clearbpsuccess == True:
                start = self.textbuffer.get_iter_at_line(self.breakpointlineno-1)
                end = self.textbuffer.get_iter_at_line(self.breakpointlineno)
                self.textbuffer.remove_source_marks(start, end, category=None)
                del self.breakpointdict[self.breakpointlineno]
                "Toggle breakpoint"
                "clear from dictionary"
            elif self.clearbpsuccess == False:
                "Error message"
            else:
                print 'Critical Error'
            #print "Deleting breakpoints not implemented yet"

    def rstep_click(self, widget, data=None):
        # dialog =  gtk.Dialog(title="Restart", parent=None, flags=0)
        #self.dialog = dialog
        
        #dialog = RestartDlg(self)
        #dialog.run()
        self.debuggee.send('rstep\n')
        self.handle_debuggee_output()
        print('rstep')

    def restart_click(self, widget, data=None):
        print('Restart')
        self.debuggee.send('restart\n')
        self.handle_debuggee_output()

    def next_click(self, widget, data=None):
        print('Next')
        self.debuggee.send('next\n')
        self.handle_debuggee_output()

    #def rstepback_click(self, widget, data=None):
    #    print('RStepback')
    #    self.debuggee.send('stepback\n')
    #    self.handle_debuggee_output()

    def rnext_click(self, widget, data=None):
        #dlg = MessageDlg(title='Restart', message='The program is restarting now')
        #dlg.run()
        print('RNext')
        self.debuggee.send('rnext\n')
        self.handle_debuggee_output()

    def continue_click(self, widget, data=None):
        print('Continue')
        self.debuggee.send('continue\n')
        self.handle_debuggee_output()
        #print self.text.get_visible_rect()

    def rcontinue_click(self, widget, data=None):
        #print('TODO RContinue')
        self.debuggee.send('rcontinue\n')
        self.handle_debuggee_output()
        #self.iter = self.textbuffer.get_iter_at_line(5)
        #self.textbuffer.place_cursor(self.iter)
    
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

    def handle_debuggee_output(self):
        print 'handle_output called'
        try:
            while True:
                line = self.debuggee.readline()
                #print('line')
                m = re.match('> ([<>/a-zA-Z0-9_\.]+)\(([0-9]+)\).*', line)
                if m:
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
                    pass
                elif line.startswith('#'):
                    self.append_debugbuffer(line[1:])
                    #Breakpoint 1 at /home/patrick/myprogs/epdb/example.py:8
                    bpsuc = re.match('#Breakpoint ([0-9]+) at ([<>/a-zA-Z0-9_\.]+):([0-9]+)', line)
                    clbpsuc = re.match("#Deleted breakpoint ([0-9]+)", line)
                    if line.startswith('#*** Blank or comment'):
                        self.breakpointsuccess = False
                    elif bpsuc:
                        self.breakpointno = bpsuc.group(1)
                        self.breakpointsuccess = True
                    elif clbpsuc:
                        self.clearbpsuccess = True
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
                    print line
                    self.append_output(line)
        except pexpect.TIMEOUT:
            print "TIMEOUT"
            #gtk.main_quit()

    def step_click(self, widget, data=None):
        print 'Step clicked'
        #if not self.running:
        #    print 'Debuggee is not running'
        #    return 
        self.debuggee.send('step\n')
        print 'Debuggee step sended'
        self.handle_debuggee_output()
        print('Step')

    def cursor_moved(self, widget,  step_size, count, extend_selection):
        print('Moved')
        self.textbuffer.place_cursor(self.lineiter)
        
    def text_clicked(self, widget, event):
        print('Clicked')

        self.textbuffer.place_cursor(self.lineiter)

    def append_output(self, txt):
        iter = self.outputbuffer.get_end_iter()
        self.outputbuffer.insert(iter, txt)
        self.output.scroll_mark_onscreen(self.outputbuffer.get_insert())
        print 'inserted'

    def append_debugbuffer(self, txt):
        iter = self.debugbuffer.get_end_iter()
        self.debugbuffer.insert(iter, txt)
        self.debug.scroll_mark_onscreen(self.debugbuffer.get_insert())
        #text_view.scroll_mark_onscreen(text_buffer.get_insert())

    def button_release_sv(self, view, event):
        if event.window == view.get_window(gtk.TEXT_WINDOW_LEFT):
            print "gutter clicked LEFT"
            if event.button == 3:
                print "Button Right"
                
                #visible = widget.get_visible_rect()
                #it = view.get_buffer().get_iter_at_line(linenumber)
                
                x_buf, y_buf = view.window_to_buffer_coords(gtk.TEXT_WINDOW_LEFT,
                                                    int(event.x), int(event.y))
                linenoiter, linenocoord = view.get_line_at_y(y_buf)
                print "coords", x_buf, y_buf
                print "lineno", linenoiter.get_line()
                self.breakpointlineno = linenoiter.get_line() + 1
                self.breakpointmenu.popup( None, None, None, event.button, event.get_time())
            #else:
            #    print "Other Button:", event.button
        #else:
        #    print "gutter clicked RIGHT"
        
    def __init__(self, filename):
        self.debuggee = pexpect.spawn("python3 -m epdb {0}".format(filename), timeout=0.5)
        
        self.running = True
        
        # create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(640,480)
        # When the window is given the "delete_event" signal (this is given
        # by the window manager, usually by the "close" option, or on the
        # titlebar), we ask it to call the delete_event () function
        # as defined above. The data passed to the callback
        # function is NULL and is ignored in the callback function.
        self.window.connect("delete_event", self.delete_event)
    
        # Here we connect the "destroy" event to a signal handler.  
        # This event occurs when we call gtk_widget_destroy() on the window,
        # or if we return FALSE in the "delete_event" callback.
        self.window.connect("destroy", self.destroy)
    
        #self.window.set_size_request(300, -1)
    
        # Sets the border width of the window.
        #self.window.set_border_width(10)
    
        self.toplevelbox = gtk.VBox()
        self.toplevelhbox = gtk.HBox()
        self.treestore = gtk.TreeStore(str)
        self.treestore.append(None, ['Test'])

        self.treeview = gtk.TreeView(self.treestore)
        self.tvcolumn = gtk.TreeViewColumn('Column 0')
        self.treeview.append_column(self.tvcolumn)
        self.cell = gtk.CellRendererText()
        self.tvcolumn.pack_start(self.cell, True)
        self.tvcolumn.add_attribute(self.cell, 'text', 0)

        self.outputbuffer = gtk.TextBuffer()
        self.output = gtk.TextView(self.outputbuffer)
        #self.append_output('Blah')
        #self.outputbuffer.set_text("Hallo Welt")
        self.output.set_editable(False)
        #self.output.set_property("height-request", 80)
    
        self.rightbox = gtk.VBox()
    
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
        
        self.output_sw = gtk.ScrolledWindow()
        self.output_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.output_sw.add(self.output)
        
        self.notebook = gtk.Notebook()
        self.notebook.set_tab_pos(gtk.POS_TOP)
        self.output_tab_lbl = gtk.Label('Output')
        self.output_tab_lbl.show()
        self.debug_tab_lbl = gtk.Label('Debug')
        self.debug_tab_lbl.show()
        self.notebook.append_page(self.output_sw, self.output_tab_lbl)
        self.notebook.append_page(self.debug_sw, self.debug_tab_lbl)

        
        self.rightbox.pack_start(self.vpaned, True, True, 0)
        self.vpaned.pack1(self.sw, resize=True, shrink=True)
        #self.vpaned.pack2(self.output, resize=False, shrink=False)
        self.vpaned.pack2(self.notebook, resize=False, shrink=False)
        #self.rightbox.pack_start(self.sw, True, True, 0)
        # self.rightbox.pack_start(self.buttonbox, False, False, 0)
        #self.rightbox.pack_start(self.output, False, False, 0)
        
        self.toplevelhbox.pack_start(self.treeview, False, False, 0)
        self.toplevelhbox.pack_start(self.rightbox, True, True, 0)
        
        self.toolbar = Toolbar(self)
        
        
        uimanager = gtk.UIManager()
        accelgroup = uimanager.get_accel_group()
        self.window.add_accel_group(accelgroup)
        actiongroup = gtk.ActionGroup('UIManagerExample')
        self.actiongroup = actiongroup
        # Create actions
        actiongroup.add_actions([('Quit', gtk.STOCK_QUIT, '_Quit', None,
                                  'Quit the Program', self.destroy),
                                 ('File', None, '_File'),
                                 ('Sound', None, '_Sound'),
                                 ('RadioBand', None, '_Radio Band'),
                                 ('Breakpoint', None, '_Breakpoint', None, "Toggle Breakpoint", self.toggle_breakpoint)])
        actiongroup.get_action('Quit').set_property('short-label', '_Quit')
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(self.ui)
        
        menubar = uimanager.get_widget('/MenuBar')
        self.breakpointmenu = uimanager.get_widget('/BreakpointMenu')
        print "Menu type", type(self.breakpointmenu)
        self.toplevelbox.pack_start(menubar, False)
        menubar.show()

        self.toplevelbox.pack_start(self.toolbar, False, False, 0)
        self.toplevelbox.pack_start(self.toplevelhbox, True, True, 0)
        #self.window.add(self.text)
        


        #self.window.add(self.toolbar)
        self.window.add(self.toplevelbox)
        self.window.show()
        self.rightbox.show()
        self.text.show()
        self.output.show()
        self.output_sw.show()
        self.debug.show()
        self.debug_sw.show()
        self.treeview.show()
        self.toplevelhbox.show()
        self.sw.show()
        self.vpaned.show()
        self.toplevelbox.show()
        self.notebook.show()
        
        self.handle_debuggee_output()
        
        #mark = self.textbuffer.create_source_mark("b1", "breakpoint", self.textbuffer.get_iter_at_line(1))
        self.breakpointdict = {} # lineno: bpno
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size("breakpoint.png", 64, 64)
        
        self.text.set_mark_category_icon_from_pixbuf("breakpoint", pixbuf)
        self.text.connect('button-release-event', self.button_release_sv)
    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start the application logic for the poll website')
    parser.add_argument('file', help='Give the filename to execute in debug mode', nargs=1)
    args = parser.parse_args()
    print args.file[0]

    guipdb = GuiPdb(args.file[0])
    guipdb.main()
