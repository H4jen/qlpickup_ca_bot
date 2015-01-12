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

import minqlbot

class anna(minqlbot.Plugin):
    def __init__(self):
        self.add_command("settopic", self.set_ch_topic)
        self.add_command("cookies", self.cmd_cookies)
        self.add_command("<3", self.cmd_heart, channels=("chat", "team_chat", "tell"))
        
    def set_ch_topic(self, player, msg, channel):
        num = msg.__len__()
        if num == 0:
            return
        con_msg = ""
        for x in range(1, num):
            con_msg =  con_msg + " " + self.translate_colors(msg[x])
        self.privmsg(self.channel, "<{}> {}\r\n"
            .format(self.translate_colors(player.name), self.translate_colors(con_msg)))
        #channel.reply("^7For me? Thank you, {}!".format(player))
        
    def cmd_cookies(self, player, msg, channel):
        channel.reply("^7For me? Thank you, {}!".format(player))

    def cmd_heart(self, player, msg, channel):
        s = ("^1\r oo   oo"
             "\no  o o  o"
             "\no   o   o"
             "\n o     o"
             "\n  o   o"
             "\n   o o"
             "\n    o")
        channel.reply(s.replace("o", "\x08"))