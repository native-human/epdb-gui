import pygtk

pygtk.require('2.0')
import gtk
import gtksourceview2
import pkgutil
import time

import os.path
import config

class Breakpoint:
    def __init__(self, filename, lineno, bpid):
        self.filename = filename
        self.lineno = lineno
        self.id = bpid

class BreakpointCollection:
    def __init__(self):
        self.breakpoint_loc_dict = {}
        self.breakpoint_id_dict = {}
        self.breakpoint_dict = {}
    
    def add(self, bp):
        self.breakpoint_loc_dict[(bp.filename, bp.lineno)] = bp
        self.breakpoint_id_dict[bp.id] = bp
        self.breakpoint_dict[bp] = True
    
    def remove(self, bp):
        del self.breakpoint_loc_dict[(bp.filename, bp.lineno)]
        del self.breakpoint_id_dict[bp.id]
        del self.breakpoint_dict[bp]

    def clear(self):
        self.breakpoint_loc_dict.clear()
        self.breakpoint_dict.clear()
        self.breakpoint_id_dict.clear()
        
    def get_by_loc(self, filename, lineno):
        return self.breakpoint_loc_dict[(filename, lineno)]
        
    def get_by_id(self, bpid):
        return self.breakpoint_id_dict[bpid]
        
    def has_loc(self, filename, lineno):
        return (filename, lineno) in self.breakpoint_loc_dict
    
    def has_id(self, bpid):
        return bpid in self.breakpoint_id_dict

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
        #self.text.set_highlight_current_line(True)
        self.text.scroll_mark_onscreen(self.textbuffer.get_insert())
        self.text.show()
        
        self.text.set_editable(False)
        self.add(self.text)
        self.show()
    
class StartPage(gtk.HBox):
    def __init__(self, guiactions, dbgcom):
        gtk.HBox.__init__(self)
        self.dbgcom = dbgcom
        self.guiactions = guiactions
        self.treestore = gtk.TreeStore(str, str)
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.connect("row-activated", self.on_treeview_activated)
        self.recently_used_programs = self.treestore.append(None, ["Recently used programs", None])
        for filename, date in config.get_latest_programs():
            self.treestore.append(self.recently_used_programs, [filename, date])
        self.recently_used_files = self.treestore.append(None, ["Recently used files", None])
        for filename, date in config.get_latest_files():
            self.treestore.append(self.recently_used_files, [filename, date])
        
        self.treeview.show()
        self.column1 = gtk.TreeViewColumn('Column 1')
        self.treeview.append_column(self.column1)
        self.cellrenderer = gtk.CellRendererText()
        self.column1.pack_start(self.cellrenderer, True)
        self.column1.add_attribute(self.cellrenderer, 'text', 0)


        self.treeview.set_headers_visible(False)
        self.pack_start(self.treeview, True, True)
        self.show()
    
    def on_treeview_activated(self, treeview, row, col):
        model = treeview.get_model()
        print "treeview activated", row, col
        #model[row][col]
        if len(row) == 2 and model[row[0]][0] == 'Recently used programs':
            print "Activate", model[row][0]
            self.guiactions.new_program(model[row][0])
        if len(row) == 2 and model[row[0]][0] == 'Recently used files':
            self.guiactions.open_file(model[row][0])
            
    def update_programs(self):
        # count number of children
        count = 0
        iter = self.treestore.iter_children(self.recently_used_programs)
        while iter:
            count += 1
            iter = self.treestore.iter_next(iter)
        
        # Get all the filenames and insert into the treestore
        for filename, date in config.get_latest_programs():
            self.treestore.append(self.recently_used_programs, [filename, date])
        
        # Remove old entries
        iter = self.treestore.iter_children(self.recently_used_programs)
        while self.treestore.iter_is_valid(iter) and count > 0:
            count -= 1
            self.treestore.remove(iter)
            
        #And now the same with recently_used_files

    def update_files(self):
        # count number of children
        count = 0
        iter = self.treestore.iter_children(self.recently_used_files)
        while iter:
            count += 1
            iter = self.treestore.iter_next(iter)
        
        # Get all the filenames and insert into the treestore
        for filename, date in config.get_latest_files():
            self.treestore.append(self.recently_used_files, [filename, date])
        
        # Remove old entries
        iter = self.treestore.iter_children(self.recently_used_files)
        while iter and self.treestore.iter_is_valid(iter) and count > 0:
            count -= 1
            self.treestore.remove(iter)
    
    def reset(self):
        """This is needed for the other pages. The Start Page doesn't change
        because of an reset"""


class DebugPage(gtk.HBox):
    def __init__(self, dbgcom, filename, bp_collection):
        gtk.HBox.__init__(self)
        self.dbgcom = dbgcom
        self.filename = filename
        with open(filename, 'r') as f:
            text = f.read()
        #print "Save file access", filename
        config.save_file_access(filename)
        self.sourceview = ScrolledSourceView()
        self.textbuffer = self.sourceview.textbuffer
        self.text = self.sourceview.text
        self.pack_start(self.sourceview, True, True, 0)
        self.show()
        
        self.active = False
        
        ui = '''<ui>
        <popup name="BreakpointMenu">
            <menuitem action="Breakpoint"/>
        </popup>
        </ui>
        '''
        
        uimanager = self.uimanager = gtk.UIManager()
        #accelgroup = uimanager.get_accel_group()
        #self.window.add_accel_group(accelgroup)
        self.actiongroup = actiongroup = gtk.ActionGroup('UIManagerExample')
        actiongroup.add_actions([
                ('Breakpoint', None, '_Breakpoint', None, "Toggle Breakpoint", self.toggle_breakpoint)
            ])
        uimanager.insert_action_group(actiongroup, 0)
        uimanager.add_ui_from_string(ui)
        self.breakpointmenu = uimanager.get_widget('/BreakpointMenu')
        #print self.breakpointmenu
        self.bp_collection = bp_collection
        
        #self.lineiter = self.textbuffer.get_iter_at_line(0)
        pixbuf_loader = gtk.gdk.PixbufLoader("png")
        pixbuf_loader.write(pkgutil.get_data("gepdb", "breakpoint.png"))
        #TODO don't sleep, but connect with the area-prepared signal and do the
        #     image stuff
        time.sleep(0.1)
        pixbuf = pixbuf_loader.get_pixbuf()
        pixbuf_loader.close()
        #pixbuf = gtk.gdk.pixbuf_new_from_data(pkgutil.get_data("gepdb", "breakpoint.png"))
        self.text.set_mark_category_icon_from_pixbuf("breakpoint", pixbuf)
        self.text.connect('button-release-event', self.button_release_sv)
        self.text.connect("expose-event", self.textview_expose)
        self.text.connect("move-cursor", self.cursor_moved)
        self.text.connect("button-release-event", self.text_clicked)
        
        if text:
            self.set_text(text)
    
    def unhighlight(self):
        #print "unhighlight", self.filename
        self.text.set_highlight_current_line(False)
        self.active = False
    
    def highlight(self):
        #print "highlight", self.filename
        self.active = True
        self.text.set_highlight_current_line(True)
    
    def set_text(self, text):
        self.textbuffer.set_text(text)
        self.lineiter = self.textbuffer.get_iter_at_line(0)
        self.textbuffer.place_cursor(self.lineiter)

    def show_line(self, lineno):
        self.lineiter = self.textbuffer.get_iter_at_line(int(lineno)-1)
        self.textbuffer.place_cursor(self.lineiter)
        self.text.scroll_mark_onscreen(self.textbuffer.get_insert())
        #self.text.set_highlight_current_line(False)

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

        if self.active:
            visible_rect = widget.get_visible_rect()
            it = self.lineiter
            y1, y2 = widget.get_line_yrange(it)
            #curline = widget.get_buffer().get_iter_at_mark(widget.get_buffer().get_insert() ).get_line()
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

    def set_breakpoint(self, bp):
        self.textbuffer.create_source_mark(None, "breakpoint",
                    self.textbuffer.get_iter_at_line(bp.lineno-1))
        self.bp_collection.add(bp)
        #self.breakpointdict[(self.filename, lineno)] = bpid
        
    def clear_breakpoint(self, bpid):
        bp = self.bp_collection.get_by_id(bpid)
        start = self.textbuffer.get_iter_at_line(bp.lineno-1)
        end = self.textbuffer.get_iter_at_line(bp.lineno-1)
        self.textbuffer.remove_source_marks(start, end, category=None)
        self.bp_collection.remove(bp)
        #del self.breakpointdict[self.breakpointlineno]
        
    def toggle_breakpoint(self, widget, data=None):
        #print "toggle breakpoint", self.breakpointlineno
        if not self.bp_collection.has_loc(self.filename, self.breakpointlineno):
            self.dbgcom.sendLine('break {0}:{1}'.format(self.filename, self.breakpointlineno))
        else:
            bp = self.bp_collection.get_by_loc(self.filename, self.breakpointlineno)
            if not bp:
                print "TODO put error in status line"
                return
            
            print "Clear Breakpoint {0}".format(bp.id)
            self.dbgcom.sendLine('clear {0}\n'.format(bp.id))
    
    def reset(self):
        "Resets all breakpoints"
        #self.breakpointdict = {}
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        self.textbuffer.remove_source_marks(start, end, category=None)
        

class TabHeader(gtk.HBox):
    def __init__(self, name, closefunc=None):
        gtk.HBox.__init__(self)
        self.closefunc = closefunc
        self.show()
        label = gtk.Label(os.path.basename(name))
        label.set_tooltip_text(name)
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
    def __init__(self, guiactions, dbgcom, *filenames):
        gtk.Notebook.__init__(self)
        self.bp_collection = BreakpointCollection()
        self.dbgcom = dbgcom
        self.guiactions = guiactions
        self.set_tab_pos(gtk.POS_TOP)
        #self.set_tab_pos(gtk.POS_LEFT)
        self.content_dict = {}
        self.label_dict = {}
        # Show Start Page
        self.startpage = StartPage(self.guiactions, self.dbgcom)
        self.start_page()
        
        # Show all filenames in EditWindow
        for fn in filenames:
            absfn = os.path.abspath(fn)
            page = self.content_dict[absfn] = DebugPage(self.dbgcom, absfn, self.bp_collection)
            closefunc = self.gen_callback_delete_page(absfn)
            labelbox = TabHeader(absfn, closefunc)
            self.label_dict[absfn] = labelbox
            #self.label_dict[absfn] = label = gtk.Label(os.path.basename(fn))
            self.append_page(page, labelbox)
            self.set_tab_reorderable(page, True)
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
        self.activepage = None

    def start_page(self):
        """Add a start page to the notebook, if it doesn't already exists"""
        if 'Start Page' in self.content_dict:
            return
        self.content_dict['Start Page'] = self.startpage
        closefunc = self.gen_callback_delete_page('Start Page')
        labelbox = TabHeader('Start Page', closefunc)
        self.label_dict['Start Page'] = labelbox
        self.append_page(self.startpage, labelbox)
        self.set_tab_reorderable(self.startpage, True)

    def gen_callback_delete_page(self, absfilename):
        def retfunc():
            page = self.content_dict[absfilename]
            page_num = self.page_num(page)
            self.remove_page(page_num)
            del self.content_dict[absfilename]
            del self.label_dict[absfilename]
            #self.label_dict.remove
        return retfunc

    def open_page(self, absfn):
        page = self.content_dict[absfn] = DebugPage(self.dbgcom, absfn, self.bp_collection)
        self.startpage.update_files()
        labelbox = TabHeader(absfn, closefunc = self.gen_callback_delete_page(absfn))
        self.label_dict[absfn] = labelbox
        self.append_page(self.content_dict[absfn], labelbox)
        self.set_tab_reorderable(self.content_dict[absfn], True)
        page_num = self.page_num(page)
        self.set_current_page(page_num)
        return page
    
    def show_line(self, filename, lineno):
        try:
            page = self.content_dict[filename]
            page.show_line(lineno)
            current_page_num = self.get_current_page()
            page_num = self.page_num(page)
            if current_page_num != page_num:
                self.set_current_page(page_num)
            active_page_num = self.page_num(self.activepage)
            if page_num != active_page_num:
                self.activepage.unhighlight()
                self.activepage = page
                self.activepage.highlight()
        except KeyError:
            # Create new page
            absfn = os.path.abspath(filename)
            page = self.open_page(absfn)

            if self.activepage:
                self.activepage.unhighlight()
            page.show_line(lineno)
            self.activepage = page
            self.activepage.highlight()

    def restart(self):
        "clear all breakpoints in all files for this debuggee"
        self.bp_collection.clear()
        for page in self.content_dict.values():
            page.reset()
            
    def set_breakpoint(self, bpid, filename, lineno):
        absfilename = os.path.abspath(filename)
        bp = Breakpoint(filename, int(lineno), int(bpid))
        page = self.content_dict[absfilename]
        page.set_breakpoint(bp)

    def clear_breakpoint(self, bpid):
        bp = self.bp_collection.get_by_id(int(bpid))
        page = self.content_dict[bp.filename]
        page.clear_breakpoint(int(bpid))
