"Communication with the debugger process"
from twisted.internet import protocol
from twisted.protocols import basic
import re
import subprocess as sp

class NullGuiAction:
    def getattr(self):
        pass

class DbgComProtocol(basic.LineReceiver):
    "Communication with epdb over Unix Domain Sockets"
    def connectionMade(self):
        self.guiactions = self.factory.guiactions
        self.guiactions.activate()
        self.guiactions.window.debuggercom.set_active_dbgcom(self)
    
    def sendLine(self, line):
        #print "sendLine", line
        basic.LineReceiver.sendLine(self, line)
    
    def lineReceived(self, line):
        cmd, _, args = line.partition("#")
        if cmd == 'lineinfo':
            linematch = re.match('([<>/a-zA-Z0-9_\.\-]+)\(([0-9]+)\).*', args)
            if linematch:
                if linematch.group(1) == '<string>':
                    pass
                else:
                    lineno = int(linematch.group(2))
                    self.guiactions.show_line(linematch.group(1), lineno)
            else:
                print 'ERROR in lineinfo:', args
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
            sid, _, sic = args.partition('#')
            self.guiactions.add_snapshot(sid, sic)
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
        elif cmd == "switched to timeline":
            bpid = args
            self.guiactions.new_active_timeline(args)
        elif cmd == "debugmessage":
            print "debugmessage", args
            message = args
            self.guiactions.append_debug(message.rstrip()+"\n")
        elif cmd == "stopped":
            self.guiactions.stopped()
        else:
            print "other cmd: ", repr(cmd), repr(args)
    
    def connectionLost(self, reason):
        pass
        #print "connection Lost", reason
    
    def quit(self):
        self.sendLine('quit')
    
class DbgComFactory(protocol.Factory):
    "Factory to create a connection with a debuggee"
    protocol = DbgComProtocol
    
    def __init__(self, guiactions):
        self.guiactions = guiactions
    
class DbgProcessProtocol(protocol.ProcessProtocol):
    """Communication with the process over stdin/stdout/stderr"""
    def __init__(self, guiactions):
        self.guiactions = guiactions
    
    def connectionMade(self):
        pass
        
    def outReceived(self, data):
        self.guiactions.append_output(data)
    
    def processEnded(self, reason):
        pass
    
class DbgComChooser:
    """Chooser which chooses between debuggees"""
    def __init__(self):
        self.p = None
        self._dbgcom = None
        
    def set_active_dbgcom(self, dbgcom):
        self._dbgcom = dbgcom
    
    def is_active(self):
        if not self._dbgcom:
            return False
        return True

    def quit(self):
        if not self._dbgcom:
            return
        return self._dbgcom.quit()
    
    def __getattr__(self, name):
        return getattr(self._dbgcom, name)