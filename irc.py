# minqlbot - A Quake Live server administrator bot.
# Copyright (C) Mino <mino@minomino.org>

# This file is part of minqlbot.

# minqlbot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# minqlbot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with minqlbot. If not, see <http://www.gnu.org/licenses/>.

import socket
import asynchat
import asyncore
import re
import minqlbot
import traceback

from threading import Thread

class IrcAdminChannel(minqlbot.AbstractChannel):
    """A channel, in the bot's context, for IRC.

    """
    def __init__(self, irc_plugin):
        super().__init__("irc")
        self.irc_plugin = irc_plugin

    def reply(self, msg):
        msg = self.irc_plugin.translate_colors(msg)
        for s in self.split_long_msg(msg, limit=450):
            self.irc_plugin.privmsg_admin(s)

# Quake will consume any character succeeding a '^' except for that same character,
# and then convert it into a color. There are 8 different colors, so Quake will
# simply do ord(character_succeeding_^) % 8 and use that as an index. We do the
# same and match it with similar colors based on the "standard" color pallet
# used by several IRC clients out there, AKA the mIRC protocol.
COLORS = ("\x0301", "\x0304", "\x0303", "\x0308", "\x0302", "\x0311", "\x0306", "\x0300")

class irc(minqlbot.Plugin):
    def __init__(self):
        super().__init__()
        self.add_hook("unload", self.handle_unload)
        self.add_hook("chat", self.handle_game_chat)
        self.add_hook("player_connect", self.handle_player_connect)
        self.add_hook("player_disconnect", self.handle_player_disconnect)
        self.add_command("say_irc", self.say_irc)
        self.add_command("topic", self.topic)
        self.add_command("lastgame", self.lastgame)
        self.add_command("players", self.lastgame_players)
        self.add_command("caps", self.lastgame_caps)
        self.add_command("add", self.qladd)
        self.add_command("remove", self.qlremove)
        self.add_command("auth", self.anna_auth)

        # Static instance so we don't waste resources making a new one every time.
        self.irc_bot_channel = IrcAdminChannel(self)
        
        self.config = minqlbot.get_config()
        self.server = self.config["IRC"].get("Server", fallback="irc.quakenet.org")
        self.channel = self.config["IRC"]["Channel"]
        self.admin_channel = self.config["IRC"]["AdminChannel"]
        self.admin_channel_pass = self.config["IRC"]["AdminChannelPassword"]
        self.color_translation = self.config["IRC"].getboolean("TranslateColors", fallback=False)
        self.irc_name = "QL" + minqlbot.NAME
        #minqlbot.debug(self.channel)
        self.irc = SimpleIrc(self.irc_name, self.server, 6667, self.channel,
                             self.admin_channel, self.admin_channel_pass, self)
        self.irc_thread = Thread(target=self.irc.run)
        self.irc_thread.start()
        self.caps = "No caps data! Try to refresh with !lastgame"
        self.players = "No player data! Try to refresh with !lastgame"
    
    def handle_unload(self):
        self.irc.quit("Plugin unloaded!")
        self.irc.close()
    
    def say_irc(self, player, msg, channel):
        #channel.reply("^7output to IRC:.")
        num = msg.__len__()
        if num == 0:
            return
        con_msg = ""
        for x in range(1, num):
            con_msg =  con_msg + " " + self.translate_colors(msg[x])
        self.privmsg(self.channel, "<{}> {}\r\n"
            .format(self.translate_colors(player.name), self.translate_colors(con_msg)))
            
    def topic(self, player, msg, channel):
        #self.irc.join("JOIN #irc.haj \r\n")
        #self.privmsg(self.channel, "<{}> {}\r\n"
        #    .format(self.translate_colors(player.name), self.translate_colors(con_msg)))
            
        #minqlbot.debug(self.channel)
        self.irc.out("TOPIC {}\r\n".format(self.channel))
        
        #self.irc.out("PRIVMSG {} :{}\r\n".format(channel, msg))
        
    def lastgame(self, player, msg, channel):
        #self.irc.join("JOIN #irc.haj \r\n")
        #self.privmsg(self.channel, "<{}> {}\r\n"
        #    .format(self.translate_colors(player.name), self.translate_colors(con_msg))
        #minqlbot.debug(self.channel)
        self.privmsg(self.channel, "!lastgame \r\n")
        #self.irc.out("TOPIC {}\r\n".format(self.channel))
        
        #self.irc.out("PRIVMSG {} :{}\r\n".format(channel, msg))
    
    def lastgame_players(self, player, msg, channel):
        self.msg("^6<^7PLAYERS^6> ^5{}".format(self.players))
    
    def lastgame_caps(self, player, msg, channel):
        self.msg("^6<^7CAPS^6> ^5{}".format(self.caps))
    
    def qladd(self, player, msg, channel):
        #channel.reply("^7output to IRC:.")
        num = msg.__len__()
        if num == 0:
            return
        con_msg = ""
        for x in range(1, num):
            con_msg =  con_msg + " " + self.translate_colors(msg[x])
        self.privmsg(self.channel, "!qladd {}\r\n"
            .format(self.translate_colors(player.name)))
    
    def qlremove(self, player, msg, channel):
        #channel.reply("^7output to IRC:.")
        num = msg.__len__()
        if num == 0:
            return
        con_msg = ""
        for x in range(1, num):
            con_msg =  con_msg + " " + self.translate_colors(msg[x])
        self.privmsg(self.channel, "!qlremove {}\r\n"
            .format(self.translate_colors(player.name)))
    
    def anna_auth(self, player, msg, channel):
        #channel.reply("^7output to IRC:.")
        num = msg.__len__()
        if num == 0:
            return
        con_msg = ""
        for x in range(1, num):
            con_msg =  con_msg + " " + self.translate_colors(msg[x])
        self.privmsg(self.channel, "!auth")
    
    def privmsg(self, channel, msg):
        self.irc.out("PRIVMSG {} :{}\r\n".format(channel, msg))
    
    def privmsg_admin(self, msg):
        self.privmsg(self.admin_channel, "{}\r\n".format(msg))
    
    def handle_game_chat(self, player, msg, channel):
        if player.clean_name.lower() == minqlbot.NAME.lower() and msg.startswith("^6<^7"):
            # TODO: More elegant solution to msg.startswith("^6<^7")
            return
        elif channel == "chat":
            return
            #self.privmsg(self.channel, "<{}> {}\r\n"
            #    .format(self.translate_colors(player.name), self.translate_colors(msg[1])))
        elif channel == "team_chat":
            return
            #self.privmsg(self.channel, "(Team) <{}> {}\r\n"
            #   .format(self.translate_colors(player.name), self.translate_colors(msg)))
        elif channel == "tell":
            return
            self.privmsg_admin("[{}] {}\r\n"
                .format(self.translate_colors(player.name), self.translate_colors(msg)))
    
    def handle_332(self, msg):
        #minqlbot.debug(msg)
        #self.privmsg(channel,msg)
        r = re.match(r":([^ ]+).+ 332 ([^ ]+) ([^ ]+) :(.+)", msg)
        if not r:
            return
        topic = r.group(4)
        self.msg("^6<^7TOPIC^6> ^5{}".format(topic))
    
    def handle_topic(self, msg):
        r = re.match(r":([^ ]+)!.+ TOPIC ([^ ]+) :(.+)", msg)
        if not r:
            return
        user = r.group(1)
        channel = r.group(2)
        topic = r.group(3)
        # Topic contained in msg_text. Send topic to ql.
        self.msg("^6<^7TOPIC^6> ^5{}".format(topic))
    
    #used to get !lastgame players + caps data to struct
    def handle_notice(self, msg):
        r = re.match(r":([^ ]+)!.+ Players:(.+).+Captains:(.+)", msg)
        if not r:
            return
        user = r.group(1)
        if not user == "anna^":
            return
        self.players=r.group(2)
        self.caps=r.group(3) 
        minqlbot.debug(self.players)
        minqlbot.debug(self.caps)
        self.msg("^6<^7PLAYERS^6> ^5{}".format(self.players))
        self.msg("^6<^7CAPS^6> ^5{}".format(self.caps))
            
    def handle_incoming(self, msg):
        r = re.match(r":([^ ]+)!.+ PRIVMSG ([^ ]+) :(.+)", msg)
        if not r:
            return
        user = r.group(1)
        channel = r.group(2)
        msg_text = r.group(3)
        split_msg = msg_text.split()
        # COMMANDS
        # .team - Send to team chat instead.
        if split_msg[0] == ".team" and channel.lower() == self.channel.lower():
            self.msg("^6<^7{}^6> ^5{}".format(user, " ".join(split_msg[1:])), "team_chat")
        # .players - List players currently on the server.
        elif split_msg[0] == ".players":
                teams = self.teams()
                game = self.game()
                # Make a list of players.
                plist = ""
                slist = ""
                for t in teams:
                    for player in teams[t]:
                        if t == "spectator":
                            slist += player.clean_name + " (s), "
                        else:
                            plist += player.clean_name + ", "

                pslist = plist + slist.rstrip(", ")
                # Message the info to the channel.
                self.privmsg(channel, "{}'s server currently has \x02{}\x02 player(s) and \x02{}\x02 spectator(s) on \x02{}\x02:\r\n"
                    .format(minqlbot.NAME, len(teams["red"] + teams["blue"] + teams["default"]), len(teams["spectator"]), game.map))
                self.privmsg(channel, "{}\r\n".format(pslist))
        # .score/.map - Return the score of the current game.
        elif split_msg[0] == ".score" or split_msg[0] == ".map" or split_msg[0] == ".info":
            game = self.game()
            state = game.state
            if state == "in_progress":
                self.privmsg(channel, "{} on \x02{}\x02: \x034RED:\x03 {} - \x032BLUE:\x03 {}\r\n"
                    .format(game.type, game.map, game.red_score, game.blue_score))
            if state == "warmup" or state == "warmup":
                self.privmsg(channel, "The game of {} is currently in warm-up on \x02{}\x02.\r\n"
                    .format(game.type, game.map))
        # .cmd Send command to bot as admin.
        elif split_msg[0].startswith(minqlbot.COMMAND_PREFIX) and channel.lower() == self.admin_channel.lower() and len(split_msg):
            minqlbot.COMMANDS.handle_input(minqlbot.DummyPlayer(minqlbot.NAME), msg_text, self.irc_bot_channel)
        elif split_msg[0] == ".say":
            num = split_msg.__len__()
            if num == 0:
                return
            con_msg = ""
            for x in range(1, num):
                con_msg =  con_msg + " " + self.translate_colors(split_msg[x])
            self.msg("^6<^7{}^6> ^2{}".format(user, con_msg))
        # Anything else is sent as a message to the server.
        elif channel.lower() == self.channel.lower():
            return
            #self.msg("^6<^7{}^6> ^2{}".format(user, msg_text))
    
    def handle_player_connect(self, player):
        name = player.clean_name
        #minqlbot.debug(name + "connected")
        #self.privmsg(self.channel, "{} connected.\r\n".format(self.translate_colors(player.name)))
    
    def handle_player_disconnect(self, player, reason):
        name = player.clean_name
        if reason == "disconnect" or reason == "unknown":
            #self.privmsg(self.channel, "{} disconnected.\r\n".format(self.translate_colors(player.name)))
            return
        elif reason == "kick":
            #self.privmsg(self.channel, "{} was kicked.\r\n".format(self.translate_colors(player.name)))
            return
        elif reason == "timeout":
            #self.privmsg(self.channel, "{} timed out.\r\n".format(self.translate_colors(player.name)))
            return
        elif reason == "ragequit":
            #self.privmsg(self.channel, "{} \x02ragequits\x02!\r\n".format(self.translate_colors(player.name)))
            return

    def translate_colors(self, text):
        if not self.color_translation:
            return self.clean_text(text)

        text = str(text)
        res = ""
        skip = False
        for i in range(len(text)):
            if skip:
                skip = False
                continue

            if text[i] == '^' and i + 1 < len(text) and text[i+1] != '^':
                res += COLORS[ord(text[i+1]) % 8]
                skip = True
            else:
                res += text[i]
                
    def strip_irc_colors(self, text):
        if not self.color_translation:
            return self.clean_text(text)

        text = str(text)
        res = ""
        skip = False
        for i in range(len(text)):
            if skip:
                skip = False
                continue

            if text[i] == '^' and i + 1 < len(text) and text[i+1] != '^':
                res += COLORS[ord(text[i+1]) % 8]
                skip = True
            else:
                res += text[i]

        return res


class SimpleIrc(asynchat.async_chat):
    def __init__(self, nick, host, port, channel, admin_channel, password, handler):
        asynchat.async_chat.__init__(self)
        self.nick = nick
        self.host = host
        self.port = int(port)
        self.channel = channel
        self.admin_channel = admin_channel
        self.password = password
        self.handler = handler
        
        self.ibuf = ""
        self.set_terminator(b"\r\n")
        
        self.serveroptions = {}


    def out(self, out):
        #minqlbot.debug(out)
        self.push(out.encode())

    def run(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.host, self.port))
        asyncore.loop()

    def handle_error(self):
        self.ibuf = ""
        e = traceback.format_exc().rstrip("\n")
        minqlbot.debug("========== ERROR: SimpleIrc ==========")
        for line in e.split("\n"):
            minqlbot.debug(line)

    def handle_connect(self):
        obuf = ("NICK {0}\r\n" + "USER {0} 0 * :{0}\r\n").format(self.nick)
        self.out(obuf)

    def handle_close(self):
        self.close()

    def collect_incoming_data(self, data):
        #minqlbot.debug(data)
        self.ibuf += data.decode("utf8", "ignore")

    def found_terminator(self):
        #Uncomment to get output on irc buffer inpcoming
        minqlbot.debug(self.ibuf)
        split_msg = self.ibuf.split()
        if len(split_msg) > 1 and split_msg[0].lower() == "ping":
            self.pong(split_msg[1].lstrip(":"))
        elif len(split_msg) > 3 and split_msg[1].lower() == "privmsg":
            self.handler.handle_incoming(self.ibuf)
        elif len(split_msg) > 3 and split_msg[1].lower() == "topic":
            self.handler.handle_topic(self.ibuf)
        elif len(split_msg) > 3 and split_msg[1].lower() == "notice":
            self.handler.handle_notice(self.ibuf)
        #Stuff to do after topic query
        elif split_msg[1] == "332":
            self.handler.handle_332(self.ibuf)
        # Save all the server's options and shit.
        elif split_msg[1] == "005":
            for option in split_msg[3:-1]:
                opt_pair = option.split("=", 1)
                if len(opt_pair) == 1:
                    self.serveroptions[opt_pair[0]] = str()
                else:
                    self.serveroptions[opt_pair[0]] = opt_pair[1]
        # Stuff to do after we get the MOTD.
        elif re.match(r":[^ ]+ (376|422) .+", self.ibuf):
            #minqlbot.debug("========== ERROR: SimpleIrc ==========")
                       # Auth with Q if we have a user/pass pair in config and we're connected to Qnet.
            if ("QUsername" in self.handler.config["IRC"] and
                 "QPassword" in self.handler.config["IRC"] and 
                 "NETWORK" in self.serveroptions and 
                 self.serveroptions["NETWORK"] == "QuakeNet" ):
                #minqlbot.debug("HERE")
                username = self.handler.config["IRC"]["QUsername"]
                password = self.handler.config["IRC"]["QPassword"]
                self.msg("Q@CServe.quakenet.org", "AUTH {0} {1}".format(username, password))
                minqlbot.debug("AUTH IRC: " + "AUTH {0} {1}".format(username, password))
                if "QHidden" in self.handler.config["IRC"] and self.handler.config["IRC"].getboolean("QHidden"):
                    self.mode(self.nick, "+x")
            self.out("JOIN {0},{1} {2},{2}\r\n".format(self.channel, self.admin_channel, self.password))
        self.ibuf = ""

    def msg(self, recipient, msg):
        self.out("PRIVMSG {0} :{1}\r\n".format(recipient, msg))

    def change_nick(self, nick):
        self.out("NICK {0}\r\n".format(nick))

    def join(self, channels):
        self.out("JOIN {0}\r\n".format(channels))

    def part(self, channels):
        self.out("PART {0}\r\n".format(channels))

    def mode(self, what, mode):
        self.out("MODE {0} {1}\r\n".format(what, mode))

    def kick(self, channel, nick, reason):
        self.out("KICK {0} {1}:{2}\r\n".format(channel, nick, reason))

    def quit(self, reason):
        self.out("QUIT :{0}\r\n".format(reason))

    def pong(self, id):
        self.out("PONG :{0}\r\n".format(id))