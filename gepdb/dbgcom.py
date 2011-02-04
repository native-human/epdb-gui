import pexpect
from twisted.internet import interfaces, reactor, protocol, error, address, defer, utils
from twisted.protocols import basic
import socket
import re

class DbgComProtocol(basic.LineReceiver):
    def connectionMade(self):
        print "connection made"
        self.guiactions = self.factory.guiactions
        self.guiactions.activate()
        self.guiactions.window.debuggercom.set_active_dbgcom(self)
    
    def sendLine(self, line):
        print "sendLine", line
        basic.LineReceiver.sendLine(self, line)
    
    def lineReceived(self, line):
        cmd,_,args = line.partition("#")
        if cmd == 'lineinfo':
            print 'lineinfo:', args
            m = re.match('([<>/a-zA-Z0-9_\.]+)\(([0-9]+)\).*', args)
            if m:
                if m.group(1) == '<string>':
                    print 'String'
                else:
                    lineno = int(m.group(2))
                    print 'showline', m.group(1), lineno
                    self.guiactions.show_line(m.group(1), lineno)
                    #self.sendLine("step")
            else:
                print 'ERROR in lineinfo'
        elif cmd == "ic":
            self.guiactions.set_ic(args)
        elif cmd == "mode":
            self.guiactions.set_mode(args)
        elif cmd == "time":
            self.guiactions.set_time(args)
        elif cmd == "clear_stdout":
            self.guiactions.set_output_text('')
        elif cmd == "add_stdout_line":
            self.guiactions.append_output(args)
        elif cmd == "newtimeline successful":
            self.guiactions.add_timeline(args)
        elif cmd == "list_timeline_snapshots":
            self.guiactions.clear_snapshots()
        elif cmd == "tsnapshot":
            id, _, ic = args.partition('#')
            self.guiactions.add_snapshot(id, ic)
        elif cmd == "list resources":
            self.guiactions.clear_resources()
        elif cmd == "resource":
            rtype, _, rloc = args.partition("#")
            self.guiactions.add_resource(rtype, rloc)
        elif cmd == "resource_entry":
            rtype, rloc, rid, ric = args.split('#')
            self.guiactions.add_resource_entry(rtype, rloc, rid, ric)
        elif cmd == "var":
            var, value = args.split("#")
            self.guiactions.update_variable(var, value)
        elif cmd == "varerror":
            self.guiactions.update_variable_error(args)
        elif cmd == "break success":
            bpid, filename, lineno = args.split("#")
            self.guiactions.add_breakpoint(bpid, filename, lineno)
        elif cmd == "clear success":
            bpid = args
            self.guiactions.clear_breakpoint(bpid)
        else:
            print "other cmd: ", cmd, args
    def connectionLost(self, reason):
        print "connection Lost", reason
    
    def quit(self):
        self.sendLine('quit')
    
class DbgComFactory(protocol.Factory):
    protocol = DbgComProtocol
    
    def __init__(self, guiactions):
        self.guiactions = guiactions
    
class DbgComChooser:
    def __init__(self):
        pass
    
    def set_active_dbgcom(self, dbgcom):
        self._dbgcom = dbgcom
    
    def __getattr__(self, name):
        return getattr(self._dbgcom, name)
    
class DebuggerCom:
    def __init__(self, guiactions):
        self.guiactions = guiactions
        self.debuggee = None
        self.params = ""
        
    def new_debuggee(self, filename, params=""):
        self.filename = filename
        self.params = ""
        if self.debuggee:
            self.sendLine("quit")
        self.debuggee = pexpect.spawn("python3 -m epdb {0} {1}".format(self.filename, self.params), timeout=None)
        self.sendLine()
        
    def is_active(self):
        return not self.debuggee is None
        
    def quit(self):
        if self.is_active():
            self.sendLine("quit")
        
    def sendLine(self, line=None, update=True):
        if line:
            if not line.endswith('\n'):
                line += '\n'
            ignorelines = 1
            #print "SEND LINE TO DEBUGGEE: ", line
            self.debuggee.send(line)
        else:
            ignorelines = 0
        returnmode = self.handle_debuggee_output(ignorelines=ignorelines)
        if returnmode == 'normal':
            if update:
                self.guiactions.update()
        elif returnmode == 'intermediate':
            pass
        else:
            print "Unknown return mode"
    
    def handle_debuggee_output(self, ignorelines=1):
        returnmode = 'normal'
        try:
            while True:
                line = self.debuggee.readline()
                if line == '':
                    break
                if ignorelines > 0:
                    #print "line ignored:", line
                    ignorelines -= 1
                    continue
                #print(line)
                m = re.match('> ([<>/a-zA-Z0-9_\.]+)\(([0-9]+)\).*', line)
                if m:
                    #self.append_debugbuffer(line)
                    #self.guiactions.append_debugbuffer(line)
                    if m.group(1) == '<string>':
                        continue
                    lineno = int(m.group(2))
                    self.guiactions.show_line(m.group(1), lineno)
                    #self.edit_window.show_line(m.group(1), lineno)
                    
                elif line.startswith('-> '):
                    pass
                    #print 'At line: ', line[3:]
                    #break
                    
                elif line.startswith('(Pdb)') or line.startswith('(Epdb)'):
                    #print 'Normal break'
                    returnmode = 'normal'
                    break
                elif line.startswith("***"):
                    print line
                    self.guiactions.append_debugbuffer(line)
                elif line.startswith('#'):
                    bpsuc = re.match('#Breakpoint ([0-9]+) at ([<>/a-zA-Z0-9_\.]+):([0-9]+)', line)
                    clbpsuc = re.match("#Deleted breakpoint ([0-9]+)", line)
                    icm = re.match("#ic: (\d+) mode: (\w+)", line)
                    timem = re.match("#time: ([\d.]*)", line)
                    #print "interesting line '{0}'".format(line.replace(" ", '_'))
                    prm = re.match("#var#([<>/a-zA-Z0-9_\. \+\-]+)#([<>/a-zA-Z0-9_\.'\" ]*)#\r\n", line)
                    perrm = re.match("#varerror# ([<>/a-zA-Z0-9_\. \+\-]+)\r\n", line)
                    resm = re.match("#resource#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
                    resem = re.match("#resource_entry#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
                    tsnapm = re.match("#tsnapshot#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
                    synterr = re.match("#syntax_error#([<>/a-zA-Z0-9_\. \+\-]*)#([0-9]+)#\r\n", line)
                    if line.startswith('#*** Blank or comment'):
                        self.breakpointsuccess = False
                    elif line.startswith("#expect input#"):
                        self.guiactions.expect_input()
                        #self.outputbox.input_entry.set_sensitive(True)
                        #self.outputbox.input_entry.grab_focus()
                        #self.varbox.deactivate()
                        #self.timelinebox.deactivate()
                        #self.toolbar.deactivate()
                        #self.statusbar.set_mode('INPUT')
                        returnmode = 'intermediate'
                        break
                    elif line.startswith("#show resources#"):
                        self.guiactions.clear_resources()
                        #self.resourcebox.clear_resources()
                    elif line.startswith("#timeline_snapshots#"):
                        self.guiactions.clear_snapshots()
                        #self.snapshotbox.clear_snapshots()
                    elif resm:
                        #print "resm", resm.group(1), resm.group(2)
                        self.guiactions.add_resource(resm.group(1), resm.group(2))
                        #self.resourcebox.add_resource(resm.group(1), resm.group(2))
                    elif resem:
                        self.guiactions.add_resource_entry(resem.group(1), resem.group(2), resem.group(3), resem.group(4))
                        #self.resourcebox.add_resource_entry(resem.group(1), resem.group(2), resem.group(3), resem.group(4))
                    elif tsnapm:
                        #print tsnapm, tsnapm.group(1), tsnapm.group(2)
                        #self.snapshotbox.add_snapshot(tsnapm.group(1), tsnapm.group(2))
                        self.guiactions.add_snapshot(tsnapm.group(1), tsnapm.group(2))
                    elif line.startswith('#-->'):
                        #self.outputbox.outputbuffer.set_text('')
                        self.guiactions.set_output_text('')
                    elif line.startswith('#->'):
                        self.guiactions.append_output(line[3:])
                        #self.append_output(line[3:])
                    elif bpsuc:
                        #self.append_debugbuffer(line)
                        self.guiactions.append_debugbuffer(line)
                        self.breakpointno = bpsuc.group(1)
                        self.breakpointsuccess = True
                    elif clbpsuc:
                        self.clearbpsuccess = True
                    elif line.startswith("#newtimeline successful"):
                        self.newtimelinesuc = True
                    elif line.startswith("#Switched to timeline"):
                        self.timelineswitchsuc = True
                    elif icm:
                        ic = icm.group(1)
                        mode = icm.group(2)
                        self.guiactions.set_mode(mode)
                        self.guiactions.set_ic(ic)
                        #self.statusbar.set_mode(mode)
                        #self.statusbar.set_ic(ic)
                    elif timem:
                        t = timem.group(1)
                        self.guiactions.set_time(t)
                        #self.statusbar.set_time(t)
                    elif prm:
                        print 'Got prm update', line
                        var = prm.group(1)
                        value = prm.group(2)
                        self.guiactions.update_variable(var, value)
                    elif perrm:
                        #print 'Got var err update'
                        var = perrm.group(1)
                        #print var
                        #self.varbox.update_variable_error(var)
                        self.guiactions.update_variable_error(var)
                    elif synterr:
                        print "Syntax Error"
                        file = synterr.group(1)
                        lineno = int(synterr.group(2))
                        
                        self.guiactions.show_syntax_error(file, lineno)
                        #self.messagebox.show_message("Syntax Error\n")
                        #self.lineiter = self.textbuffer.get_iter_at_line(lineno-1)
                        #self.textbuffer.place_cursor(self.lineiter)
                        #self.toolbar.deactivate()
                        
                        #self.text.scroll_mark_onscreen(self.textbuffer.get_insert())
                    else:
                        'print "OTHER LINE", line'
                        self.guiactions.append_debugbuffer(line[1:])
                elif line.startswith('--Return--'):
                    print 'Return'
                    self.guiactions.append_output(line)
                    #dialog = RestartDlg(self)
                    #dialog.run()
                #elif line.startswith('The program finished and will be restarted'):
                #    print 'Finished: ', line
                #    dlg = MessageDlg(title='Restart', message='The program has finished and will be restarted now', action=self.restart)
                #    dlg.run()
                #    #break
                else:
                    #print line
                    self.guiactions.append_output(line)
                    #self.guiactions.append_output(line)
        except pexpect.TIMEOUT:
            print "TIMEOUT"
            #gtk.main_quit()
        #self.text.scroll_mark_onscreen(self.textbuffer.get_insert())
        return returnmode

