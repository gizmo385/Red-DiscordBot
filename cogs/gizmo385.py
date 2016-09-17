from discord.ext import commands
from .utils.chat_formatting import *
from .utils.dataIO import fileIO
from .utils import checks
from __main__ import user_allowed, send_cmd_help
import os
import requests
import json

class Gizmo385:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="fortune", pass_context=True, no_pm=True)
    async def __new_fortune(self, ctx):
        """Gives you a fortune"""
        fortune_output = os.popen("fortune").read()
        await self.bot.say(box(fortune_output))
        return

    @commands.command(name="cowsay", pass_context=True, no_pm=True)
    async def __cowsay(self, ctx, *text):
        """Makes the cow say something"""
        if not text:
            await self.bot.say(box("You must include text"))
            return
        else:
            cosway_output = os.popen("cowsay " + " ".join(text)).read()
            await self.bot.say(box(cosway_output))
        return

    @commands.command(name="cowfortune", pass_context=True, no_pm=True)
    async def __cowfortune(self, ctx):
        """Makes the cow say a fortune"""
        fortune_output = os.popen("fortune").read()
        cosway_output = os.popen("cowsay " + fortune_output).read()
        await self.bot.say(box(cosway_output))
        return

    @commands.command(name="baconipsum", pass_context=True, no_pm=True)
    async def __bacon_ipsum(self, ctx, paras):
        """For when you need filler text involving bacon"""
        try:
            paras = int(paras)
            paras = max(1, min(paras, 5))
            url = "https://baconipsum.com/api/?type=meat-and-filler&paras={paras}&format=text".format(paras=paras)
            result = requests.get(url)
            await self.bot.say(box(result.text))
        except ValueError:
            await self.bot.say("The argument must be a number")
        return

    @commands.command(name="swapi", pass_context=True, no_pm=False)
    async def __swapi(self, ctx, endpoint, *params):
        """Searches the star wars API"""
        endpoints = ["people", "planets", "films", "starships", "vehicles",
                     "species"]
        if endpoint not in endpoints:
            await self.bot.say("Valid search types: " + ", ".join(endpoints))
            return

        api_url = "https://swapi.co/api/{type}/?search={params}"
        api_url = api_url.format(params=" ".join(params), type=endpoint)
        try:
            result = requests.get(api_url)
            await self.bot.whisper(box(json.dumps(result.json(), indent=4)))
        except:
            await self.bot.say("Error while searching :(")

def setup(bot):
    n = Gizmo385(bot)
    bot.add_cog(n)

