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
        self.input_from_user = True
        self.dbgcom = dbgcom
        self.guiactions = guiactions
        self.debugbuffer = gtk.TextBuffer()
        self.debug = gtk.TextView(self.debugbuffer)
        self.debug.set_editable(False)
        
        self.debug_sw = gtk.ScrolledWindow()
        self.debug_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.debug_sw.add(self.debug)
        
        self.texttagtable = gtk.TextTagTable()
        self.texttag_editable = gtk.TextTag("editable")	
        self.texttag_editable.set_property("editable", False)
        self.texttag_editable.set_property("editable-set", True)     
        self.texttagtable.add(self.texttag_editable)

        self.outputbox = gtk.VBox()
        self.outputbuffer = gtk.TextBuffer(self.texttagtable)
        self.outputbuffer.connect("mark-set", self.on_output_mark_set)
        self.outputbuffer.connect_after("insert-text", self.on_output_insert_text)
        self.output = gtk.TextView(self.outputbuffer)
        self.output.set_editable(True)
        self.input_mark_left = self.outputbuffer.create_mark("input_mark_left", self.outputbuffer.get_end_iter(), left_gravity=True)
        self.input_mark_right = self.outputbuffer.create_mark("input_mark_right", self.outputbuffer.get_end_iter(), left_gravity=False)
    
        self.output_sw = gtk.ScrolledWindow()
        self.output_sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.output_sw.add(self.output)
        
        self.outputbox.pack_start(self.output_sw, True, True, 0)
        self.outputbox.show()
        
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
        
    def on_output_mark_set(self, textbuffer, iter, textmark):
        if textmark.get_name() == 'insert' and iter.has_tag(self.texttag_editable):
            suc = True
            while suc:
                if iter.has_tag(self.texttag_editable):
                    suc = iter.forward_char()
                else:
                    break
            if suc == False:
                iter = self.outputbuffer.get_end_iter()
            self.outputbuffer.move_mark(textmark, iter)
            self.outputbuffer.move_mark(self.outputbuffer.get_selection_bound(), iter)
        else:
            pass
            #print "mark set", textbuffer, iter.get_line(), iter.get_tags(), textmark.get_name()
            
    def on_output_insert_text(self, textview, iter, text, length):
        i = iter.copy()
        if self.input_from_user == False:
            self.input_from_user = True
            return
        self.outputbuffer.move_mark(self.input_mark_right, self.outputbuffer.get_iter_at_mark(self.input_mark_left))
        if text == '\n':
            start = iter.copy()
            start.backward_char()
            self.outputbuffer.delete(start, iter)
            start = self.outputbuffer.get_iter_at_mark(self.input_mark_left)
            end = self.outputbuffer.get_end_iter()
            line = self.outputbuffer.get_slice(start, end)
            self.outputbuffer.delete(start, end)
            enditer = self.outputbuffer.get_end_iter()
            cursor = self.outputbuffer.get_mark('insert')
            self.outputbuffer.move_mark(cursor, enditer)
            self.outputbuffer.move_mark(self.input_mark_left, enditer)
            self.outputbuffer.move_mark(self.input_mark_right, enditer)
            #print "line: ", repr(line), repr(text)
            self.guiactions.window.dbgprocess.transport.write(line+'\n')
        
    def modify_font(self, font_desc):
        self.debug.modify_font(font_desc)
        self.output.modify_font(font_desc)
        self.debug_tab_lbl.modify_font(font_desc)
        self.output_tab_lbl.modify_font(font_desc)
        
    def append_output(self, text):
        #print "append output", repr(text), len(text)
        self.input_from_user = False
        iter = self.outputbuffer.get_iter_at_mark(self.input_mark_left)
        self.outputbuffer.insert_with_tags(iter, text, self.texttag_editable)
        #right gravity needed: move left gravity mark to the position of the right gravity mark
        self.outputbuffer.move_mark(self.input_mark_left, self.outputbuffer.get_iter_at_mark(self.input_mark_right))
        self.output.scroll_mark_onscreen(self.outputbuffer.get_insert())