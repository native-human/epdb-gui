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

IMAGEDIR = "/usr/share/gepdb"

class ScrolledSourceView(gtk.ScrolledWindow):
    def __init__(self):
        gtk.ScrolledWindow.__init__(self)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.textbuffer = gtksourceview2.Buffer()    
        self.text = gtksourceview2.View(self.textbuffer)
        self.languagemanager = gtksourceview2.LanguageManager()
        
        l = self.languagemanager.get_language("python")
        self.textbuffer.set_language(l)
        self.text.set_show_line_marks(True)
        self.text.set_show_line_numbers(True)
        self.text.set_highlight_current_line(True)
        self.text.scroll_mark_onscreen(self.textbuffer.get_insert())
        self.text.show()
        
        #self.lineiter = self.textbuffer.get_iter_at_line(0)
        
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(os.path.join(IMAGEDIR,"breakpoint.png"), 64, 64)
        self.text.set_mark_category_icon_from_pixbuf("breakpoint", pixbuf)
        self.text.connect('button-release-event', self.button_release_sv)
        self.text.connect("expose-event", self.textview_expose)
        self.text.connect("move-cursor", self.cursor_moved)
        self.text.connect("button-release-event", self.text_clicked)
        self.text.set_editable(False)
        self.add(self.text)
        self.show()
    
    def button_release_sv(self, view, event):
        if event.window == view.get_window(gtk.TEXT_WINDOW_LEFT):
            #print "gutter clicked LEFT"
            if event.button == 3: 
                x_buf, y_buf = view.window_to_buffer_coords(gtk.TEXT_WINDOW_LEFT,
                                                    int(event.x), int(event.y))
                linenoiter, linenocoord = view.get_line_at_y(y_buf)
                self.breakpointlineno = linenoiter.get_line() + 1
                self.breakpointmenu.popup( None, None, None, event.button, event.get_time())
    
    def textview_expose(self, widget, event):
        if event.window != widget.get_window(gtk.TEXT_WINDOW_TEXT):     
            return

        visible_rect = widget.get_visible_rect()
        it = self.lineiter
        y1,y2 = widget.get_line_yrange(it)
        curline = widget.get_buffer().get_iter_at_mark(widget.get_buffer().get_insert() ).get_line()
        width, height = widget.allocation.width, widget.allocation.height
        context = event.window.cairo_create()
        context.rectangle(0, 0, width, height)
        context.clip()
        context.set_line_width(1.0)
        context.set_source_rgba(1,1,0,.25)
        context.rectangle(0,y1-visible_rect.y, width, y2)
        context.fill()

    def cursor_moved(self, widget,  step_size, count, extend_selection):
        self.textbuffer.place_cursor(self.lineiter)
        
    def text_clicked(self, widget, event):
        self.textbuffer.place_cursor(self.lineiter)


class DebugPage(gtk.HBox):
    def __init__(self, text):
        gtk.HBox.__init__(self)
        self.sourceview = ScrolledSourceView() 
        self.textbuffer = self.sourceview.textbuffer
        self.text = self.sourceview.text
        self.pack_start(self.sourceview, True, True, 0)
        self.show()
        if text:
            self.set_text(text)
    
    def set_text(self, text):
        self.textbuffer.set_text(text)
        self.sourceview.lineiter = self.textbuffer.get_iter_at_line(0)
        self.textbuffer.place_cursor(self.sourceview.lineiter)

    def show_line(self, lineno):
        self.sourceview.lineiter = self.textbuffer.get_iter_at_line(int(lineno)-1)
        self.textbuffer.place_cursor(self.sourceview.lineiter)

class TabHeader(gtk.HBox):
    def __init__(self, name, closefunc=None):
        gtk.HBox.__init__(self)
        self.closefunc = closefunc
        self.show()
        label = gtk.Label(name)
        label.show()
        labelbutton = gtk.Button()
        labelbutton.connect('clicked', self.on_close_click)
        labelbutton.set_relief(gtk.RELIEF_NONE)
        #vs = gtk.icon_size_register("very small", 12, 12)
        img = gtk.image_new_from_stock(gtk.STOCK_CLOSE,  gtk.ICON_SIZE_MENU)
        labelbutton.set_name("my-close-button")
        #labelbutton.set_alignment(0,0)
        img.show()
        labelbutton.set_image(img)
        labelbutton.show()
        self.pack_start(label, False, False, 0)
        self.pack_start(labelbutton, False, False, 0)
    
    def on_close_click(self, widget, data=None):
        print "Close clicked"
        if self.closefunc:
            self.closefunc()
            
class EditWindow(gtk.Notebook):
    def __init__(self, *filenames):
        gtk.Notebook.__init__(self)
        self.set_tab_pos(gtk.POS_TOP)
        self.content_dict = {}
        self.label_dict = {}
        for fn in filenames:
            with open(fn, 'r') as f:
                txt = f.read()
            absfn = os.path.abspath(fn)
            page = self.content_dict[absfn] = DebugPage(txt)
            closefunc = self.gen_callback_delete_page(absfn)
            labelbox = TabHeader(os.path.basename(fn), closefunc)
            self.label_dict[absfn] = labelbox
            #self.label_dict[absfn] = label = gtk.Label(os.path.basename(fn))
            self.append_page(page, labelbox)
        self.show()
        rcstyle = """style "my-button-style"
            {
              GtkWidget::focus-padding = 0
              GtkWidget::focus-line-width = 0
              xthickness = 0
              ythickness = 0
            }
            widget "*.my-close-button\" style "my-button-style" """ 
        gtk.rc_parse_string(rcstyle)

    def gen_callback_delete_page(self, absfilename):
        def retfunc():
            page = self.content_dict[absfilename]
            page_num = self.page_num(page)
            self.remove_page(page_num)
            del self.content_dict[absfilename]
            del self.label_dict[absfilename]
            #self.label_dict.remove
        return retfunc

    def show_line(self, filename, lineno):
        try:
            page = self.content_dict[filename]
            page.show_line(lineno)
            current_page_num = self.get_current_page()
            page_num = self.page_num(page)
            if current_page_num != page_num:
                self.set_current_page(page_num)
        except KeyError:
            print "Could not find filename", filename
            with open(filename, 'r') as f:
                txt = f.read()
            absfn = os.path.abspath(filename)
            page = self.content_dict[absfn] = DebugPage(txt)
            labelbox = TabHeader(os.path.basename(filename), closefunc = self.gen_callback_delete_page(absfn))
            self.label_dict[absfn] = labelbox
            self.append_page(self.content_dict[absfn], labelbox)
            page_num = self.page_num(page)
            self.set_current_page(page_num)
            page.show_line(lineno)
