import tempfile
import config

from dbgcom import DbgComChooser, DbgComFactory, DbgComProtocol, DebuggerCom, DbgProcessProtocol

class GuiActions:
    def __init__(self, window):
        self.window = window

    def update(self):
        self.window.varbox.update_all_variables()
        self.window.resourcebox.update_resources()
        self.window.snapshotbox.update_snapshots()
        
    def append_debugbuffer(self, line):
        # TODO call outputbox directly
        self.window.append_debugbuffer(line)
        
    def show_line(self, filename, lineno):
        self.window.edit_window.show_line(filename, lineno)
        self.update()
        
    def expect_input(self):
        self.window.outputbox.input_entry.set_sensitive(True)
        self.window.outputbox.input_entry.grab_focus()
        self.window.varbox.deactivate()
        self.window.timelinebox.deactivate()
        self.window.toolbar.deactivate()
        self.window.statusbar.set_mode('INPUT')
        
    def clear_resources(self):
        self.window.resourcebox.clear_resources()
        
    def clear_snapshots(self):
        self.window.snapshotbox.clear_snapshots()
        
    def add_resource(self, type, location):
        self.window.resourcebox.add_resource(type, location)
    
    def add_resource_entry(self, type, location, ic, id):
        self.window.resourcebox.add_resource_entry(type, location, ic, id)
     
    def add_snapshot(self, id, ic):   
        self.window.snapshotbox.add_snapshot(id, ic)
        
    def set_output_text(self, text):
        self.window.outputbox.outputbuffer.set_text(text)        
    
    def append_output(self, text):
        self.window.outputbox.append_output(text)
        #self.window.append_output(text)

    def set_mode(self, mode):
        self.window.statusbar.set_mode(mode)

    def set_ic(self, ic):
        self.window.statusbar.set_ic(ic)

    def set_time(self, time):
        self.window.statusbar.set_time(time)

    def update_variable(self, var, value):
        self.window.varbox.update_variable(var, value)

    def update_variable_error(self, var):
        self.window.varbox.update_variable_error(var)
        
    def show_syntax_error(self, file, lineno):
        self.window.messagebox.show_message("Syntax Error\n")
        self.show_line(file, lineno)
        #self.lineiter = self.textbuffer.get_iter_at_line(lineno-1)
        #self.textbuffer.place_cursor(self.lineiter)
        self.window.toolbar.deactivate()

    def reset(self):
        print("Reset")
        self.window.outputbox.outputbuffer.set_text('')
        self.window.outputbox.debugbuffer.set_text('')
        self.window.timelinebox.reset()
        self.window.edit_window.restart()
        
        self.window.snapshotbox.clear_snapshots()
        self.window.resourcebox.clear_resources()
        self.window.timelinebox.reset()
        self.window.varbox.reset()

    def update_snapshots(self):
        self.window.snapshotbox.clear_snapshots()
        self.window.snapshotbox.update_snapshots()
        
    def activate(self):
        self.window.varbox.activate()
        self.window.timelinebox.activate()
        self.window.toolbar.activate()
    
    def statusbar_message(self, message):
        self.window.statusbar.message(message)

    def add_timeline(self, name):
        self.window.timelinebox.add_timeline(name)
        #self.update_snapshots()
        self.update()
        
    def add_breakpoint(self, bpid, filename, lineno):
        self.window.edit_window.set_breakpoint(bpid, filename, lineno)
    
    def clear_breakpoint(self, bpid):
        self.window.edit_window.clear_breakpoint(bpid)
    
    def new_active_timeline(self, timelinename):
        self.window.timelinebox.new_active_timeline(timelinename)
        
    def new_program(self, filename, parameters=[]):
        # TODO ask if the user wants to close the running debugging session.
        self.window.outputbox.outputbuffer.set_text('')
        self.window.outputbox.debugbuffer.set_text('')
        self.window.timelinebox.reset()
        self.window.snapshotbox.clear_snapshots()
        self.window.resourcebox.clear_resources()
        self.window.timelinebox.reset()
        self.window.varbox.reset()
        self.window.parameters = parameters
        
        self.window.debuggercom.quit()
        self.window.dbgprocess = DbgProcessProtocol(self)
        self.window.tempfilename = tempfile.mktemp(dir=self.window.tempdir)
        factory = DbgComFactory(self)
        if self.window.listen:
            self.window.listen.stopListening()
        self.window.listen = self.window.reactor.listenUNIX(self.window.tempfilename, factory)
        r = self.window.reactor.spawnProcess(self.window.dbgprocess, 'epdb', ["epdb", "--uds", self.window.tempfilename, filename]+parameters, usePTY=True)
        config.save_program_access(filename)
        self.window.toolbar.activate()
        self.window.edit_window.startpage.update_programs()
        
    def open_file(self, filename):
        "Open a new file without executing it"
        self.window.edit_window.open_page(filename)
        
    def start_page(self):
        "View a start page in the main notebook"
        self.window.edit_window.start_page()