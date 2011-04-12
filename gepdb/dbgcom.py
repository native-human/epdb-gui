"Communication with the debugger process"
from twisted.internet import protocol
from twisted.protocols import basic
import re
import subprocess as sp

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
            message = args
            self.guiactions.append_debug(message.rstrip()+"\n")
        else:
            print "other cmd: ", cmd, args
    
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
    
    def new_debuggee(self, filename, parameters):
        
        if self.p:
            self.quit()
        # TODO split parameters
        # TODO change the communication channel
        self.p = sp.Popen(["python3",
                           "/usr/lib/python3.1/dist-packages/epdb.py", "--uds",
                           '/tmp/dbgcom', filename, parameters], stdout=sp.PIPE)
    
    def __getattr__(self, name):
        return getattr(self._dbgcom, name)
    
#class DebuggerCom:
#    def __init__(self, guiactions):
#        self.guiactions = guiactions
#        self.debuggee = None
#        self.params = ""
#        self.filename = None
#        
#    def new_debuggee(self, filename, params=""):
#        self.filename = filename
#        self.params = ""
#        if self.debuggee:
#            self.sendLine("quit")
#        self.debuggee = pexpect.spawn("python3 -m epdb {0} {1}".format(self.filename, self.params), timeout=None)
#        self.sendLine()
#        
#    def is_active(self):
#        return not self.debuggee is None
#        
#    def quit(self):
#        if self.is_active():
#            self.sendLine("quit")
#        
#    def sendLine(self, line=None, update=True):
#        if line:
#            if not line.endswith('\n'):
#                line += '\n'
#            ignorelines = 1
#            self.debuggee.send(line)
#        else:
#            ignorelines = 0
#        returnmode = self.handle_debuggee_output(ignorelines=ignorelines)
#        if returnmode == 'normal':
#            if update:
#                self.guiactions.update()
#        elif returnmode == 'intermediate':
#            pass
#        else:
#            print "Unknown return mode"
#    
#    def handle_debuggee_output(self, ignorelines=1):
#        returnmode = 'normal'
#        try:
#            while True:
#                line = self.debuggee.readline()
#                if line == '':
#                    break
#                if ignorelines > 0:
#                    ignorelines -= 1
#                    continue
#                m = re.match('> ([<>/a-zA-Z0-9_\.]+)\(([0-9]+)\).*', line)
#                if m:
#                    if m.group(1) == '<string>':
#                        continue
#                    lineno = int(m.group(2))
#                    self.guiactions.show_line(m.group(1), lineno)
#                elif line.startswith('-> '):
#                    pass
#                elif line.startswith('(Pdb)') or line.startswith('(Epdb)'):
#                    #print 'Normal break'
#                    returnmode = 'normal'
#                    break
#                elif line.startswith("***"):
#                    print line
#                    self.guiactions.append_debugbuffer(line)
#                elif line.startswith('#'):
#                    bpsuc = re.match('#Breakpoint ([0-9]+) at ([<>/a-zA-Z0-9_\.]+):([0-9]+)', line)
#                    clbpsuc = re.match("#Deleted breakpoint ([0-9]+)", line)
#                    icm = re.match("#ic: (\d+) mode: (\w+)", line)
#                    timem = re.match("#time: ([\d.]*)", line)
#                    #print "interesting line '{0}'".format(line.replace(" ", '_'))
#                    prm = re.match("#var#([<>/a-zA-Z0-9_\. \+\-]+)#([<>/a-zA-Z0-9_\.'\" ]*)#\r\n", line)
#                    perrm = re.match("#varerror# ([<>/a-zA-Z0-9_\. \+\-]+)\r\n", line)
#                    resm = re.match("#resource#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
#                    resem = re.match("#resource_entry#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
#                    tsnapm = re.match("#tsnapshot#([<>/a-zA-Z0-9_\. \+\-]*)#([<>/a-zA-Z0-9_\. \+\-]*)#\r\n", line)
#                    synterr = re.match("#syntax_error#([<>/a-zA-Z0-9_\. \+\-]*)#([0-9]+)#\r\n", line)
#                    if line.startswith('#*** Blank or comment'):
#                        self.breakpointsuccess = False
#                    elif line.startswith("#expect input#"):
#                        self.guiactions.expect_input()
#                        returnmode = 'intermediate'
#                        break
#                    elif line.startswith("#show resources#"):
#                        self.guiactions.clear_resources()
#                    elif line.startswith("#timeline_snapshots#"):
#                        self.guiactions.clear_snapshots()
#                    elif resm:
#                        self.guiactions.add_resource(resm.group(1), resm.group(2))
#                    elif resem:
#                        self.guiactions.add_resource_entry(resem.group(1), resem.group(2), resem.group(3), resem.group(4))
#                    elif tsnapm:
#                        self.guiactions.add_snapshot(tsnapm.group(1), tsnapm.group(2))
#                    elif line.startswith('#-->'):
#                        self.guiactions.set_output_text('')
#                        print "Clear output box1"
#                    elif line.startswith('#->'):
#                        self.guiactions.append_output(line[3:])
#                    elif bpsuc:
#                        self.guiactions.append_debugbuffer(line)
#                        self.breakpointno = bpsuc.group(1)
#                        self.breakpointsuccess = True
#                    elif clbpsuc:
#                        self.clearbpsuccess = True
#                    elif line.startswith("#newtimeline successful"):
#                        self.newtimelinesuc = True
#                    elif line.startswith("#Switched to timeline"):
#                        self.timelineswitchsuc = True
#                    elif icm:
#                        ic = icm.group(1)
#                        mode = icm.group(2)
#                        self.guiactions.set_mode(mode)
#                        self.guiactions.set_ic(ic)
#                    elif timem:
#                        t = timem.group(1)
#                        self.guiactions.set_time(t)
#                    elif prm:
#                        print 'Got prm update', line
#                        var = prm.group(1)
#                        value = prm.group(2)
#                        self.guiactions.update_variable(var, value)
#                    elif perrm:
#                        var = perrm.group(1)
#                        self.guiactions.update_variable_error(var)
#                    elif synterr:
#                        print "Syntax Error"
#                        file = synterr.group(1)
#                        lineno = int(synterr.group(2))
#                        
#                        self.guiactions.show_syntax_error(file, lineno)
#                    else:
#                        'print "OTHER LINE", line'
#                        self.guiactions.append_debugbuffer(line[1:])
#                elif line.startswith('--Return--'):
#                    print 'Return'
#                    self.guiactions.append_output(line)
#                else:
#                    self.guiactions.append_output(line)
#        except pexpect.TIMEOUT:
#            print "TIMEOUT"
#        return returnmode
#
