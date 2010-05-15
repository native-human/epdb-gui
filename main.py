##!/usr/bin/env python

# example helloworld.py

import pygtk
pygtk.require('2.0')
import gtk
import gtksourceview2 

import sys
import keyword, token, tokenize, cStringIO, string
import pexpect
import re

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
    def __init__(self, title='', message=''):
        gtk.Dialog.__init__(self, title=title)
        okbutton = gtk.Button('Ok')
        textlabel = gtk.Label(message)
        self.action_area.pack_start(okbutton, True, True, 0)
        okbutton.connect('clicked', lambda x: self.destroy())
        self.vbox.pack_start(textlabel, True, True, 0)
        textlabel.show()
        okbutton.show()
        

class Toolbar(gtk.HBox):
    def __init__(self, prnt):
        gtk.HBox.__init__(self)
        self.prnt = prnt
        self.rcontinue = gtk.Button("RContinue")
        self.rcontinue.connect("clicked", self.prnt.rcontinue_click, None)
        self.stepback = gtk.Button("Stepback")
        self.stepback.connect("clicked", self.prnt.stepback_click, None)
        #self.stepback.connect_object("clicked", gtk.Widget.destroy, self.window)
        self.step = gtk.Button("Step")
        self.step.connect("clicked", self.prnt.step_click, None)
        self.next = gtk.Button("Next")
        self.next.connect("clicked", self.prnt.next_click, None)
        self.nextback = gtk.Button("Nextback")
        self.nextback.connect("clicked", self.prnt.rnext_click, None)
        self.cont = gtk.Button("Continue")
        self.cont.connect("clicked", self.prnt.continue_click, None)
        self.restart = gtk.Button("Restart")
        self.restart.connect("clicked", self.prnt.restart_click, None)
        #self.buttonbox = gtk.HBox()
        self.pack_start(self.rcontinue, False, False, 0)
        self.pack_start(self.nextback, False, False, 0)
        self.pack_start(self.stepback, False, False, 0)
        self.pack_start(self.step, False, False, 0)
        self.pack_start(self.next, False, False, 0)
        self.pack_start(self.cont, False, False, 0)
        self.pack_start(self.restart, False, False, 0)
        self.step.show()
        self.next.show()
        self.nextback.show()
        self.restart.show()
        self.rcontinue.show()
        self.cont.show()
        #self.buttonbox.show()
        self.stepback.show()
        self.show()

class GuiPdb:

    def norestart(self):
        self.running = False
    
    def restart(self):
        self.running = True

    def delete_event(self, widget, event, data=None):
        print "delete event occurred"
        return False  # False means window get destroyed

    def destroy(self, widget, data=None):
        print "destroy signal occurred"
        gtk.main_quit()

    def stepback_click(self, widget, data=None):
        # dialog =  gtk.Dialog(title="Restart", parent=None, flags=0)
        dialog = RestartDlg(self)
        dialog.run()
        #self.dialog = dialog
        
        print('Stepback')

    def restart_click(self, widget, data=None):
        print('Restart')
        self.debuggee.send('restart\n')
        self.handle_debuggee_output()

    def next_click(self, widget, data=None):
        print('Next')
        self.debuggee.send('next\n')
        self.handle_debuggee_output()

    def rstepback_click(self, widget, data=None):
        print('RStepback')

    def rnext_click(self, widget, data=None):
        dlg = MessageDlg(title='Restart', message='The program is restarting now')
        dlg.run()
        print('RNext')

    def continue_click(self, widget, data=None):
        print('Continue')
        self.debuggee.send('continue\n')
        self.handle_debuggee_output()
        #print self.text.get_visible_rect()

    def rcontinue_click(self, widget, data=None):
        print('RContinue')
        self.iter = self.textbuffer.get_iter_at_line(5)
        self.textbuffer.place_cursor(self.iter)
    
    def textview_expose(self, widget, event):
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
        context.set_source_rgba(1,1,0,.25)
        context.rectangle(0,y1, width, y2)
        context.fill()

    def handle_debuggee_output(self):
        try:
            while True:
                line = self.debuggee.readline()
                #print('line')
                m = re.match('> ([<>/a-zA-Z0-9_\.]+)\(([0-9]+)\)\<module\>\(\).*', line)
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
                elif line.startswith('(Pdb)'):
                    pass
                elif line.startswith('--Return--'):
                    print 'Return'
                    self.append_output(line)
                    #dialog = RestartDlg(self)
                    #dialog.run()
                elif line.startswith('The program finished and will be restarted'):
                    print 'Finished: ', line
                    self.outputbuffer.set_text('')
                    dlg = MessageDlg(title='Restart', message='The program has finished and will be restarted now')
                    dlg.run()
                    #break
                else:
                    print line
                    self.append_output(line)
        except pexpect.TIMEOUT:
            pass

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

    def __init__(self):
        self.debuggee = pexpect.spawn("python3 -m pdb example.py", timeout=0.2)
        
        self.running = True
        
        # create a new window
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    
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
    
        # Sets the border width of the window.
        self.window.set_border_width(10)
    
        self.toplevelbox = gtk.VBox(False, 2)
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
        self.output.set_property("height-request", 100)
    
        self.rightbox = gtk.VBox()
    
        self.textbuffer = gtksourceview2.Buffer()
        self.text = gtksourceview2.View(self.textbuffer)
        #self.text.set_property("can-focus", False)
        self.text.connect("expose-event", self.textview_expose)
        self.text.connect("move-cursor", self.cursor_moved)
        self.text.connect("button-release-event", self.text_clicked)
        self.text.set_editable(False)
        
        #self.textbuffer = self.text.get_buffer()
        txt = open('example.py', 'r').read()
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
        
        self.rightbox.pack_start(self.vpaned, True, True, 0)
        self.vpaned.pack1(self.sw, resize=True, shrink=True)
        self.vpaned.pack2(self.output, resize=False, shrink=False)
        #self.rightbox.pack_start(self.sw, True, True, 0)
        # self.rightbox.pack_start(self.buttonbox, False, False, 0)
        #self.rightbox.pack_start(self.output, False, False, 0)
        
        self.toplevelhbox.pack_start(self.treeview, False, False, 0)
        self.toplevelhbox.pack_start(self.rightbox, True, True, 0)
        
        self.toolbar = Toolbar(self)
        
        
        menubar = gtk.MenuBar()
        agr = gtk.AccelGroup()
        self.toplevelbox.pack_start(menubar, False, False, 0)
        menubar.show()
        
        filemenuitem = gtk.MenuItem("_File", agr)
        
        filemenuitem.show()
        menubar.append(filemenuitem)
        filemenu = gtk.Menu()
        
        newitem = gtk.MenuItem("_New", agr)
        quititem = gtk.MenuItem("_Quit", agr)
        quititem.connect('activate', self.destroy)
        sep = gtk.SeparatorMenuItem()
        filemenu.append(newitem)
        filemenu.append(sep)
        filemenu.append(quititem)
        filemenuitem.set_submenu(filemenu)
        filemenu.show()
        quititem.show()
        newitem.show()
        sep.show()
        
        self.window.add_accel_group(agr)
        key, mod = gtk.accelerator_parse("N")
        newitem.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)
        key, mod = gtk.accelerator_parse("Q")
        quititem.add_accelerator("activate", agr, key, mod, gtk.ACCEL_VISIBLE)



        self.toplevelbox.pack_start(self.toolbar, False, False, 0)
        self.toplevelbox.pack_start(self.toplevelhbox, True, True, 0)
        #self.window.add(self.text)
        
        

        #self.window.add(self.toolbar)
        self.window.add(self.toplevelbox)
        self.window.show()
        self.rightbox.show()
        self.text.show()
        self.output.show()
        self.treeview.show()
        self.toplevelhbox.show()
        self.sw.show()
        self.vpaned.show()
        self.toplevelbox.show()
        
        self.handle_debuggee_output()
        
        iter1 = self.textbuffer.get_iter_at_line(3)
        iter2 = self.textbuffer.get_iter_at_line(4)
        mark = self.textbuffer.create_mark("mark1", iter1, left_gravity=False)

        #self.textbuffer.create_tag("highlighted",  background = "red")
        #self.textbuffer.apply_tag_by_name("highlighted", iter1, iter2)

        #print self.text.get_visible_rect()
    def main(self):
        # All PyGTK applications must have a gtk.main(). Control ends here
        # and waits for an event to occur (like a key press or mouse event).
        gtk.main()

if __name__ == "__main__":
    guipdb = GuiPdb()
    guipdb.main()