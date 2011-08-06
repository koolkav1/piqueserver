from twisted.internet import reactor
from twisted.internet.task import LoopingCall

import commands

@commands.admin
@commands.name('timer')
def start_timer(connection, end):
    connection.protocol.start_timer(int(end) * 60)

commands.add(start_timer)

def apply_script(protocol, connection, config):
    class MatchConnection(connection):
        def on_flag_take(self):
            self.add_message("%s took %s's flag!" %
                (self.printable_name, self.team.other.name.lower()))
            return connection.on_flag_take(self)
        
        def on_flag_drop(self):
            self.add_message("%s dropped %s's flag!" %
                (self.printable_name, self.team.other.name.lower()))
            return connection.on_flag_drop(self)
                
        def on_flag_capture(self):
            self.add_message("%s captured %s's flag!" %
                (self.printable_name, self.team.other.name.lower()))
            return connection.on_flag_capture(self)
        
        def on_kill(self, killer):
            if killer is None:
                killer = self
            self.add_message("%s was killed by %s!" %
                (self.printable_name, killer.printable_name))
            return connection.on_kill(self, killer)
        
        def add_message(self, value):
            self.protocol.messages.append(value)
    
    class MatchProtocol(protocol):
        def __init__(self, *arg, **kw):
            protocol.__init__(self, *arg, **kw)
            self.messages = []
            self.send_message_loop = LoopingCall(self.display_messages)
            self.send_message_loop.start(2)
            
        def start_timer(self, end):
            self.timer_end = reactor.seconds() + end
            self.send_chat('Timer started, ending in %s minutes' % (end / 60),
                irc = True)
            self.display_timer(True)
        
        def display_timer(self, silent = False):
            time_left = self.timer_end - reactor.seconds()
            minutes_left = int(time_left / 60.0)
            next_call = 60
            if not silent:
                if time_left <= 0:
                    self.send_chat('Timer ended!', irc = True)
                    return
                elif minutes_left <= 1:
                    self.send_chat('%s seconds left' % int(time_left), 
                        irc = True)
                    next_call = max(1, int(time_left / 2.0))
                else:
                    self.send_chat('%s minutes left' % int(minutes_left), 
                        irc = True)
            reactor.callLater(next_call, self.display_timer)
        
        def display_messages(self):
            if not self.messages:
                return
            message = self.messages.pop(0)
            self.irc_say(message)
        
    return MatchProtocol, MatchConnection