#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import gtksourceview2
import sys
import os
import difflib

class Filewatcher:
    def delete_event(self, widget, data=None):
        gtk.main_quit()
        
    def timeout(self):
        #print 'Timeout'
        try:
            _, _, _, _, _, _, _, _, _, st_ctime = os.stat(self.filename)
        except OSError:
            print 'OSError'
            source_id = gobject.timeout_add(100, self.timeout)
            return
        
        if st_ctime != self.ctime:
            print 'File has changed'
            self.ctime = st_ctime
            with open(self.filename, 'r') as f:
                newtext = f.read()
            self.textbuffer.set_text(newtext)
            print 'New text set'
            print newtext
            print '----'
            # TODO do some diff highlighting
            newlines = newtext.splitlines()
            oldlines = self.text.splitlines()
            
            sm = difflib.SequenceMatcher(a=newlines, b=oldlines)
            
            lastc = 0
            self.highlighted_lines = []
            for element in sm.get_matching_blocks():
                if element[0] != lastc:
                    print 'Not same:', lastc, element[0]
                    self.highlighted_lines.extend(list(range(lastc, element[0])))
                
                print 'Same: ', element[0], '-', element[0]+element[2]
                lastc = element[0] + element[2]
            
            
            self.text = newtext
            print 'highlighted lines', self.highlighted_lines
        
        source_id = gobject.timeout_add(100, self.timeout)
        
    def __init__(self, filename):
        self.filename = filename
        st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime = os.stat(self.filename)
        self.ctime = st_ctime
        with open(filename, 'r') as f:
            self.text = f.read()
        
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_default_size(640,480)
        self.window.connect("delete_event", self.delete_event)
        self.textbuffer = gtksourceview2.Buffer()
        #self.textbuffer = gtk.TextBuffer()
        #self.textview = gtk.TextView(self.textbuffer)
        self.textview = gtksourceview2.View(self.textbuffer)
        self.textview.set_editable(False)
        self.textview.set_show_line_numbers(True)
        self.textbuffer.set_text(self.text)
        
        self.sw = gtk.ScrolledWindow()
        self.sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.sw.add(self.textview)
        
        self.window.add(self.sw)
        source_id = gobject.timeout_add(1, self.timeout)

        self.sw.show()
        self.textview.show()
        self.window.show()
        
        self.highlighted_lines = []
        self.textview.connect("expose-event", self.highlight_line)
        self.odd = 1
        
    
    def highlight_line(self, widget, event): #expose event
        #print 'Event', event.window == widget.get_window(gtk.TEXT_WINDOW_TEXT), \
        #    event.window == widget.get_window(gtk.TEXT_WINDOW_LEFT)
    
        if event.window == widget.get_window(gtk.TEXT_WINDOW_TEXT):
            for linenumber in self.highlighted_lines:
                it = widget.get_buffer().get_iter_at_line(linenumber)
                y1,y2 = widget.get_line_yrange(it)
                width, height = widget.allocation.width, widget.allocation.height
                context = event.window.cairo_create()
                context.rectangle(0, 0, width, height)
                context.clip()
                context.set_line_width(1.0)
                context.set_source_rgba(0.5,1,0.5,1)
                context.rectangle(0,y1, width, y2)
                context.fill()
        
    def main(self):
        gtk.main()

def usage():
    print 'filewatcher.py filename'

if __name__ == "__main__":
    if len(sys.argv) != 2:
        usage()
        
    filename = sys.argv[1]
    #print st_ctime
    #print filename
    #sys.exit(0)
    filewatcher = Filewatcher(filename)
    filewatcher.main()