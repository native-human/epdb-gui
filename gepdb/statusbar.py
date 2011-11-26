import pygtk
pygtk.require('2.0')
import gtk

class Statusbar(gtk.Statusbar):
    def __init__(self, prnt):
        gtk.Statusbar.__init__(self)
        self.prnt = prnt
        
        self.messagelbl = self.get_children()[0].get_child().get_children()[0]
        
        self.context_id = self.get_context_id("gepdb")
        self.modelbl = gtk.Label("Mode label")
        self.modelbl.set_markup('Mode: <span color="red">normal</span>')
        self.modelbl.show()
        
        self.iclbl = gtk.Label("Ic label")
        self.iclbl.set_markup('Ic: 0')
        self.iclbl.show()
        
        self.timelbl = gtk.Label("Time Label")
        self.timelbl.set_markup('Time: 0s')
        self.timelbl.show()
        
        self.pack_start(self.timelbl, False, False, 0)
        self.pack_start(self.iclbl, False, False, 20)
        self.pack_start(self.modelbl, False, False, 20)
        self.show()
        
    def set_mode(self, mode):
        self.modelbl.set_markup(
                        'Mode: <span color="red">{0}</span>'.format(mode))
    
    def set_ic(self, ic):
        self.iclbl.set_markup('Ic: {0}'.format(ic))
    
    def set_time(self, time):
        
        if str(time).strip() == "":
            self.timelbl.set_markup('')
        else:
            time = float(time)
            unit = 's'
            if time < 1:
                time = time * 1000
                unit = 'ms'
                if time < 1:
                    time = time * 1000
                    unit = 'us'
            self.timelbl.set_markup('Time: {0:0.1f} {1}'.format(time, unit))
        
    def message(self, message):
        self.push(self.context_id, message)
        
    def modify_font(self, font_desc):
        #gtk.Statusbar.child.modify_font(self, font_desc)
        self.messagelbl.modify_font(font_desc)
        self.iclbl.modify_font(font_desc)
        self.modelbl.modify_font(font_desc)
        self.timelbl.modify_font(font_desc)
