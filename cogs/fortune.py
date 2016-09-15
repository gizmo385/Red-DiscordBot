from discord.ext import commands
from .utils.chat_formatting import *
from .utils.dataIO import fileIO
from .utils import checks
from __main__ import user_allowed, send_cmd_help
import os
import requests

class Fortune:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="fortune", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_server=True)
    async def __new_fortune(self, ctx):
        fortune_output = os.popen("fortune").read()
        await self.bot.say(box(fortune_output))
        return

    @commands.command(name="cowsay", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_server=True)
    async def __cowsay(self, ctx, *text):
        if not text:
            await self.bot.say(box("You must include text"))
            return
        else:
            cosway_output = os.popen("cowsay " + " ".join(text)).read()
            await self.bot.say(box(cosway_output))
        return

    @commands.command(name="cowfortune", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_server=True)
    async def __cowfortune(self, ctx):
        fortune_output = os.popen("fortune").read()
        cosway_output = os.popen("cowsay " + fortune_output).read()
        await self.bot.say(box(cosway_output))
        return

    @commands.command(name="baconipsum", pass_context=True, no_pm=True)
    @checks.mod_or_permissions(manage_server=True)
    async def __bacon_ipsum(self, ctx, paras):
        try:
            paras = int(paras)
            paras = max(1, min(paras, 5))
            url = "https://baconipsum.com/api/?type=meat-and-filler&paras={paras}&format=text".format(paras=paras)
            result = requests.get(url)
            await self.bot.say(box(result.text))
        except ValueError:
            await self.bot.say("The argument must be a number")
        return


def setup(bot):
    n = Fortune(bot)
    bot.add_cog(n)

