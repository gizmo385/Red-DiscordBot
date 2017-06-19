import discord
from discord.ext import commands
from .utils.chat_formatting import *
from .utils.dataIO import fileIO
from .utils import checks
from __main__ import user_allowed, send_cmd_help
from random import choice
import os
import requests
import logging
import json

log = logging.getLogger('red.gizmo385')

class Gizmo385:
    def __init__(self, bot):
        self.fuckoffs = fileIO("data/gizmo385/fuckoff.json","load")
        self.bot = bot

    @commands.command(name="fortune", pass_context=True, no_pm=True)
    async def __new_fortune(self, ctx):
        """Gives you a fortune"""
        fortune_output = os.popen("fortune").read()
        await self.bot.say(box(fortune_output))
        return

    @commands.command(name="cowfortune", pass_context=True, no_pm=True)
    async def __cowfortune(self, ctx):
        """Makes the cow say a fortune"""
        fortune_output = os.popen("fortune").read()
        cosway_output = os.popen("cowsay " + fortune_output).read()
        await self.bot.say(box(cosway_output))
        return

    @commands.command(pass_context=True, no_pm=True)
    async def fuckoff(self, ctx, user : discord.Member=None):
        author = ctx.message.author
        base_url = 'https://foaas.com'
        endpoint = choice(self.fuckoffs)

        insult = requests.get(
            base_url + endpoint, headers={'Accept' : 'text/plain'}
        )

        if insult.status_code == 200:
            user = user.mention if user else 'everyone @here'

            message = insult.content.decode('UTF-8')
            replacements = {
                'name' : user,
                'from' : author.mention,
                'language' : 'English',
                'do' : 'Fuck',
                'something' : 'fuckers',
                'reference' : '¯\_(ツ)_/¯'
            }

            if ':name' not in message:
                message = ':name, ' + message

            for key, replacement in replacements.items():
                message = message.replace(':' + key, replacement)

            await self.bot.say(message)
        else:
            await self.bot.say("Error communicating with FOaaS API")


def check_folders():
    folders = ("data", "data/gizmo385/")
    for folder in folders:
        if not os.path.exists(folder):
            print("Creating " + folder + " folder...")
            os.makedirs(folder)

def setup(bot):
    check_folders()
    n = Gizmo385(bot)
    bot.add_cog(n)
