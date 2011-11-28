import pygtk
pygtk.require('2.0')
import gtk

class ResourceBox(gtk.VBox):
    def __init__(self, dbgcom):
        gtk.VBox.__init__(self)
        self.dbgcom = dbgcom

        self.treestore = gtk.TreeStore(str, str)
        self.var_renderer = gtk.CellRendererText()
        #self.lbl = gtk.Label('Resources')
        #self.lbl.show()
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_headers_visible(False)
        
        self.scrolledwindow = gtk.ScrolledWindow()
        self.scrolledwindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolledwindow.show()
        
        self.treeview.show()
        self.treedict = {}
        self.tvcolumn1 = gtk.TreeViewColumn('Column 0', self.var_renderer, text=0)
        self.tvcolumn2 = gtk.TreeViewColumn('Column 1', self.var_renderer, text=1)
        
        self.treeview.append_column(self.tvcolumn1)
        self.treeview.append_column(self.tvcolumn2)
        
        #self.pack_start(self.lbl, False, False, 0)
        self.pack_start(self.scrolledwindow, True, True, 0)
        self.scrolledwindow.add(self.treeview)
        self.iter_dict = {}
        self.rows = 0
        self.show()

    def update_resources(self):
        "Send to the debuggee the request to update the resources"
        self.dbgcom.sendLine('resources')
    
    def add_resource(self, rtype, location):
        "Add a resource to the store"
        treeiter = self.treestore.append(None, (rtype, location))
        self.iter_dict[(rtype, location)] = treeiter
        self.rows += 1
        
    def add_resource_entry(self, rtype, location, ric, rid):
        "Add resource data to the resource"
        self.treestore.append(self.iter_dict[(rtype, location)], (ric, rid))
        for i in range(self.rows):
            self.treeview.expand_row(str(i), True)
    
    def clear_resources(self):
        "Clears all resources from the window"
        self.rows = 0
        self.iter_dict = {}
        self.treestore.clear()
        
    def modify_font(self, font_desc):
        self.treeview.modify_font(font_desc)
