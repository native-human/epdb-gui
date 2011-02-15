import pygtk
pygtk.require('2.0')
import gtk

class MessageBox(gtk.EventBox):
    def __init__(self):
        gtk.EventBox.__init__(self)
        self.hbox = gtk.HBox()
        self.add(self.hbox)
        self.messagelbl = gtk.Label("")
        self.buttonbox = gtk.VBox()
        self.buttonbox.show()
        self.cancelbutton = gtk.Button("X")
        self.cancelbutton.show()
        self.cancelbutton.connect('clicked', self.on_cancel_clicked)
        self.buttonbox.pack_start(self.cancelbutton, False, False, 0)
        self.hbox.pack_start(self.messagelbl, True, True, 0)
        self.hbox.pack_start(self.buttonbox, False, False, 0)
        self.messagelbl.show()
        self.modify_bg(gtk.STATE_NORMAL, self.get_colormap().alloc_color("red"))
        self.hbox.show()
        #self.show()
    
    def on_cancel_clicked(self, widget, data=None):
        self.hide()
        
    def show_message(self, message):
        self.messagelbl.set_text(message)
        self.show()