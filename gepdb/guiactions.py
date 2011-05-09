import tempfile
import config

from dbgcom import DbgComFactory, DbgProcessProtocol

class GuiActions:
    def __init__(self, window):
        self.window = window

    def update(self):
        self.window.varbox.update_all_variables()
        self.window.resourcebox.update_resources()
        self.window.snapshotbox.update_snapshots()
        
    def append_debug(self, line):
        """Append to the debug window"""
        self.window.outputbox.append_debug(line)
        
    def show_line(self, filename, lineno):
        """Show a line of a file in the edit window"""
        self.window.edit_window.show_line(filename, lineno)
        self.update()
        
    def expect_input(self):
        """TODO i think this will not be needed anymore"""
        self.window.outputbox.input_entry.set_sensitive(True)
        self.window.outputbox.input_entry.grab_focus()
        self.window.varbox.deactivate()
        self.window.timelinebox.deactivate()
        self.window.toolbar.deactivate()
        self.window.statusbar.set_mode('INPUT')
        
    def clear_resources(self):
        """Clear all resources"""
        self.window.resourcebox.clear_resources()
        
    def clear_snapshots(self):
        """Clear all snapshots"""
        self.window.snapshotbox.clear_snapshots()
        
    def add_resource(self, rtype, location):
        """Adds an resource to the resource box"""
        self.window.resourcebox.add_resource(rtype, location)
    
    def add_resource_entry(self, rtype, location, ric, rid):
        """Adds a resource entry to the resource box"""
        self.window.resourcebox.add_resource_entry(rtype, location, ric, rid)
     
    def add_snapshot(self, sid, sic):
        """Adds a new snapshot to the Snapshot Box"""
        self.window.snapshotbox.add_snapshot(sid, sic)
        
    def set_output_text(self, text):
        """Set the Output Window text"""
        self.window.outputbox.outputbuffer.set_text(text)        
    
    def append_output(self, text):
        """Append some text to the output window"""
        self.window.outputbox.append_output(text)

    def set_mode(self, mode):
        """Set the current mode"""
        self.window.statusbar.set_mode(mode)

    def set_ic(self, ic):
        """Set the instruction count"""
        self.window.statusbar.set_ic(ic)

    def set_time(self, time):
        """Set the time needed for an instruction"""
        self.window.statusbar.set_time(time)

    def update_variable(self, var, value):
        """Update the value of an variable"""
        self.window.varbox.update_variable(var, value)

    def update_variable_error(self, var):
        """Add a variable with error message to the variable box"""
        self.window.varbox.update_variable_error(var)
        
    def show_syntax_error(self, filename, lineno):
        """Show a message with a syntax error and go to the position in the
        program"""
        self.window.messagebox.show_message("Syntax Error\n")
        self.show_line(filename, lineno)
        self.window.toolbar.deactivate()

    def reset(self):
        "Resets every thing. Usually called before starting another debuggee"
        self.window.outputbox.outputbuffer.set_text('')
        self.window.outputbox.debugbuffer.set_text('')
        self.window.timelinebox.reset()
        self.window.edit_window.restart()
        
        self.window.snapshotbox.clear_snapshots()
        self.window.resourcebox.clear_resources()
        self.window.timelinebox.reset()
        self.window.varbox.reset()

    def update_snapshots(self):
        "Updates the snapshot box."
        self.window.snapshotbox.clear_snapshots()
        self.window.snapshotbox.update_snapshots()
        
    def activate(self):
        "Activates the toolbar"
        self.window.varbox.activate()
        self.window.timelinebox.activate()
        self.window.toolbar.activate()
    
    def statusbar_message(self, message):
        "Sends a message to the statusbar"
        self.window.statusbar.message(message)

    def add_timeline(self, name):
        "Adds a new timeline to the gui"
        self.window.timelinebox.add_timeline(name)
        #self.update_snapshots()
        self.update()
        
    def add_breakpoint(self, bpid, filename, lineno):
        "Adds a breakpoint in the edit window"
        self.window.edit_window.set_breakpoint(bpid, filename, lineno)
    
    def clear_breakpoint(self, bpid):
        "Clears a breakpoint in the edit_window"
        self.window.edit_window.clear_breakpoint(bpid)
    
    def new_active_timeline(self, timelinename):
        "Sets a new active timeline in the timelinebox by highlighting it."
        self.window.timelinebox.new_active_timeline(timelinename)
        
    def new_program(self, filename, parameters=[]):
        "Starts a new program for debugging"
        # TODO ask if the user wants to close the running debugging session.
        self.window.outputbox.outputbuffer.set_text('')
        self.window.outputbox.debugbuffer.set_text('')
        self.window.edit_window.restart()
        self.window.timelinebox.reset()
        self.window.snapshotbox.clear_snapshots()
        self.window.resourcebox.clear_resources()
        self.window.timelinebox.reset()
        self.window.varbox.reset()
        self.window.parameters = parameters
        self.window.filename = filename
        
        self.window.debuggercom.quit()
        self.window.dbgprocess = DbgProcessProtocol(self)
        self.window.tempfilename = tempfile.mktemp(dir=self.window.tempdir)
        factory = DbgComFactory(self)
        if self.window.listen:
            self.window.listen.stopListening()
        self.window.listen = self.window.reactor.listenUNIX(
                self.window.tempfilename, factory)
        
        abs_epdb_path = self.window.find_executable('epdb')
        self.window.reactor.spawnProcess(self.window.dbgprocess, abs_epdb_path,
            ["epdb", "--uds", self.window.tempfilename, filename] + parameters,
            usePTY=True)
        config.save_program_access(filename)
        self.window.toolbar.activate()
        self.window.edit_window.startpage.update_programs()
        
    def open_file(self, filename):
        "Open a new file without executing it"
        self.window.edit_window.open_page(filename)
        
    def start_page(self):
        "View a start page in the main notebook"
        self.window.edit_window.start_page()