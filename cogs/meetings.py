import asyncio
import json
import logging
import os
import time

from datetime import datetime

import discord

from dateutil import parser
from discord.ext import commands

from .utils.dataIO import fileIO

MEETING_TIME_FORMAT = "%m/%d/%Y at %-I:%M:%S%p %Z"

class Meeting:
    """Never forget anything anymore."""

    def __init__(self, bot):
        self.bot = bot
        self.meetings = fileIO("data/meetings/meetings.json", "load")


    @commands.group(name='meetings', pass_context=True)
    async def _meetings(self, ctx):
        """Meeting operations"""
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    def _create_new_meeting(self, creator, time, title, users):
        meeting = {
            'creator' : creator.id,
            'time' : int(time.strftime('%s')),
            'title' : title,
            'users' : [u.id for u in users]
        }

        self.meetings.append(meeting)
        fileIO("data/meetings/meetings.json", "save", self.meetings)

        return meeting

    def _meetings_created_by(self, creator_to_find):
        created_meetings = []

        for meeting in self.meetings:
            creator = meeting['creator']
            if creator == creator_to_find.id:
                created_meetings.append(meeting)

        return created_meetings

    @_meetings.command(pass_context=True, no_pm=True)
    async def create(self, ctx, date, time, title, *users):
        # Parse out the users
        try:
            users = [discord.User(id=u[2:-1]) for u in users]
        except ValueError as ve:
            await self.bot.say("Error - Invalid user: {}".format(user))

        # Parse out the time and date
        combined_date_and_time = date + ' ' + time
        try:
            parsed_meeting_time = parser.parse(combined_date_and_time)
        except ValueError as ve:
            print(ve)
            await self.bot.say("Error: Could not parse your time and date!")
            return

        author = ctx.message.author
        meeting = self._create_new_meeting(
            author, parsed_meeting_time, title, users
        )

        await self.bot.say('Scheduled meeting "{title}" on {time}'.format(
            title=title,
            time=parsed_meeting_time.strftime(MEETING_TIME_FORMAT)
        ))

    @_meetings.command(name='removeall', pass_context=True, no_pm=True)
    async def remove_all(self, ctx):
        author = ctx.message.author
        to_remove = self._meetings_created_by(author)
        self.meetings = [m for m in self.meetings if m not in to_remove]
        fileIO("data/meetings/meetings.json", "save", self.meetings)

        await self.bot.say("Removed all of your meetings.")

    @_meetings.command(pass_context=True, no_pm=True)
    async def list(self, ctx):
        author = ctx.message.author
        meetings_to_show = self._meetings_created_by(author)

        message = ""
        if not meetings_to_show:
            await self.bot.say("You do not have any scheduled meetings")
            return

        message += "Your meetings:\n"
        for meeting in meetings_to_show:
            meeting_time = datetime.utcfromtimestamp(int(meeting['time']))
            message += "▸ {}: {}\n".format(
                meeting['title'], meeting_time.strftime(MEETING_TIME_FORMAT)
            )

        em = discord.Embed(description=message, colour=author.colour)
        await self.bot.say(embed=em)

    # async def check_meetings(self):
        # while self is self.bot.get_cog("Meetings"):
            # pass

def check_folders():
    if not os.path.exists("data/meetings"):
        print("Creating data/meetings folder...")
        os.makedirs("data/meetings")

def check_files():
    files =  [
        "data/meetings/meetings.json",
        "data/meetings/meetings.log"
    ]

    for f in files:
        if not fileIO(f, "check"):
            print("Creating: {}".format(f))
            fileIO(f, "save", [])

def setup(bot):
    global logger
    check_folders()
    check_files()
    logger = logging.getLogger("meetings")
    if logger.level == 0: # Prevents the logger from being loaded again in case of module reload
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(filename='data/meetings/meetings.log', encoding='utf-8', mode='a')
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s', datefmt="[%d/%m/%Y %H:%M]"))
        logger.addHandler(handler)
    n = Meeting(bot)
    loop = asyncio.get_event_loop()
    bot.add_cog(n)
