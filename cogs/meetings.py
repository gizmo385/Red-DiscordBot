import asyncio
import json
import logging
import os
import time

from datetime import datetime
from functools import lru_cache

import discord

from dateutil import parser
from discord.ext import commands
from __main__ import send_cmd_help

from .utils.dataIO import fileIO

MEETING_TIME_FORMAT = '%x at %X %p %Z'

class Meetings:
    """
    Schedule meetings with other discord users and generate reminders for
    all attendees.
    """

    def __init__(self, bot):
        self.bot = bot
        self.meetings = fileIO("data/meetings/meetings.json", "load")
        self.user_cache = {}


    @commands.group(name='meetings', aliases=['meeting', 'meet'],
                    pass_context=True)
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

        logger.info("Created new meeting: {}".format(meeting))
        return meeting

    def _meetings_created_by_user(self, user):
        return [m for m in self.meetings if user.id == m['creator']]

    def _meetings_including_user(self, user, ignore_mine=True):
        uid = user.id
        if ignore_mine:
            return [m for m in self.meetings
                    if uid in m['users'] and m['creator'] != uid]
        else:
            return [m for m in self.meetings if uid in m['users']]

    @_meetings.command(pass_context=True, no_pm=False)
    async def info(self, ctx, *, meeting_name):
        """ Retrieves information about a meeting by name """
        author = ctx.message.author
        invited_meetings = self._meetings_including_user(author, ignore_mine=False)

        found = False
        for meeting in invited_meetings:
            if meeting['title'].lower() != meeting_name.lower():
                continue
            found = True

            # Pull creator information
            if meeting['creator'] in self.user_cache:
                creator = self.user_cache[meeting['creator']]
            else:
                creator = await self.bot.get_user_info(meeting['creator'])
                self.user_cache[meeting['creator']] = creator

            users = meeting['users']
            title = meeting['title']
            time = datetime.utcfromtimestamp(meeting['time'])

            # Build the message
            message = title + '\n'
            message += "-" * len(title) + '\n'
            message += "Created by: {}\n".format(creator.name)
            message += "Scheduled: {}\n\n".format(
                time.strftime(MEETING_TIME_FORMAT)
            )

            # Get usernames
            usernames = []
            for user_id in users:
                if user_id in self.user_cache:
                    user = self.user_cache[user_id]
                else:
                    user = await self.bot.get_user_info(user_id)
                    self.user_cache[user_id] = user
                usernames.append(user.name)

            message += "Attendees: {}\n".format(', '.join(usernames))

            em = discord.Embed(description=message)
            if hasattr(author, 'color'):
                em.color = author.color
            await self.bot.say(embed=em)

        if not found:
            await self.bot.say("Could not find a meeting by that name.")
        logger.info("Cache: {}".format(self.user_cache))

    @_meetings.command(pass_context=True, no_pm=True)
    async def create(self, ctx, date, time, title, *users):
        """ Creates a new meeting on the calendar """
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
            logger.error(ve)
            await self.bot.say("Error: Could not parse your time and date!")
        else:
            author = ctx.message.author
            meeting = self._create_new_meeting(
                author, parsed_meeting_time, title, users
            )

            await self.bot.say('Scheduled meeting "{title}" on {time}'.format(
                title=title,
                time=parsed_meeting_time.strftime(MEETING_TIME_FORMAT)
            ))

    @_meetings.command(pass_context=True)
    async def reject(self, ctx, *, meeting_name):
        """ Remove yourself from the attending list for a meeting """
        author = ctx.message.author
        meetings = self._meetings_including_user(author, ignore_mine=False)

        meetings_rejected = 0
        for meeting in meetings:
            users = meeting['users']
            creator = meeting['creator']

            if meeting['title'] == meeting_name:
                meetings_rejected += 1
                users.remove(author.id)
                meeting['users'] = users

        if meetings_rejected:
            logger.info("{} meetings rejected by {}".format(
                meetings_rejected, author
            ))
            fileIO("data/meetings/meetings.json", "save", self.meetings)
            await self.bot.say("Meetings rejected.")
        else:
            await self.bot.say("No meeting on your calendar with that name.")

    @_meetings.command(pass_context=True)
    async def cancel(self, ctx, *, meeting_name):
        """ Cancels a meeting by name """
        author = ctx.message.author
        meetings = self._meetings_created_by_user(author)
        to_cancel = [m for m in meetings if m['title'].lower() == meeting_name.lower()]

        if to_cancel:
            self.meetings = [m for m in self.meetings if m not in to_cancel]
            fileIO("data/meetings/meetings.json", "save", self.meetings)
            logger.info("Meetings to delete: " + str(to_cancel))

            if len(to_cancel) == 1:
                await self.bot.say("Cancelled 1 meeting.")
            else:
                await self.bot.say("Cancelled {} meetings.".format(len(to_cancel)))
        else:
            await self.bot.say("Could not find a meeting with that name!")

    @_meetings.command(name='cancelall', pass_context=True, no_pm=True)
    async def cancel_all(self, ctx):
        """ Cancels all meetings you have scheduled """
        author = ctx.message.author
        to_remove = self._meetings_created_by_user(author)
        self.meetings = [m for m in self.meetings if m not in to_remove]
        fileIO("data/meetings/meetings.json", "save", self.meetings)

        await self.bot.say("Removed all of your meetings.")

    @_meetings.command(pass_context=True)
    async def list(self, ctx):
        """ Lists all meetings you're a part of (created or invited) """
        author = ctx.message.author
        your_meetings = self._meetings_created_by_user(author)
        invited_meetings = self._meetings_including_user(author)

        message = ""
        if not (your_meetings or invited_meetings):
            await self.bot.say("You have no meetings on your calendar.")
            return

        # Check the meetings that you have created
        if your_meetings:
            message += "Your meetings:\n"
            for meeting in your_meetings:
                meeting_time = datetime.utcfromtimestamp(int(meeting['time']))
                message += "▸ {}: {}\n".format(
                    meeting['title'],
                    meeting_time.strftime(MEETING_TIME_FORMAT)
                )

            # Add some spacing
            if invited_meetings:
                message += "\n"

        # Check the meetings others have created that you're invited to
        if invited_meetings:
            message += "Meetings you're invited to:\n"
            for meeting in invited_meetings:
                meeting_time = datetime.utcfromtimestamp(int(meeting['time']))
                message += "▸ {}: {}\n".format(
                    meeting['title'],
                    meeting_time.strftime(MEETING_TIME_FORMAT)
                )

        # Send a message detailing all the meetings you're a part of
        em = discord.Embed(description=message)
        if hasattr(author, 'color'):
            em.color = author.color
        await self.bot.say(embed=em)

    @_meetings.command(pass_context=True, no_pm=False)
    async def next(self, ctx):
        """ Lists the next meeting on your calendar """
        author = ctx.message.author
        invited_meetings = self._meetings_including_user(
            author, ignore_mine=False
        )

        # Determine the earliest meeting on your calendar
        if not invited_meetings:
            await self.bot.say("You have no upcoming meetings.")
            return

        earliest_meeting = invited_meetings[0]
        for meeting in invited_meetings:
            if meeting['time'] < earliest_meeting['time']:
                earliest_meeting = meeting

        # Send out the earliest meeting information
        if not earliest_meeting:
            await self.bot.say("Could not find your next earliest meeting.")
        else:
            meeting_time = datetime.utcfromtimestamp(earliest_meeting['time'])
            await self.bot.say('Your next meeting is "{title}" on {time}'.format(
                title=earliest_meeting['title'],
                time=meeting_time.strftime(MEETING_TIME_FORMAT)
            ))

    async def check_meetings(self):
        check_time = datetime.now()
        while self is self.bot.get_cog("Meetings"):
            to_remove = []

            for meeting in self.meetings:
                meeting_time = datetime.utcfromtimestamp(meeting['time'])
                msg = '{time} - Meeting about to start: {title}'.format(
                    time=meeting_time.strftime(MEETING_TIME_FORMAT),
                    title=meeting['title']
                )

                # Check if the meeting start time has passed
                if meeting_time <= check_time:
                    logger.info("Sending reminders for {meeting}...".format(
                        meeting=meeting
                    ))
                    to_remove.append(meeting)

                    # PM each user with a reminder about the meeting
                    for user in meeting['users']:
                        try:
                            discord_user = discord.User(id=user)
                        except ValueError as ve:
                            continue

                        await self.bot.send_message(discord_user, msg)

            # Remove any meetings where reminders were sent
            if to_remove:
                self.meetings = [m for m in self.meetings if m not in to_remove]
                fileIO("data/meetings/meetings.json", "save", self.meetings)

            await asyncio.sleep(10)


def check_folders():
    if not os.path.exists("data/meetings"):
        print("Creating data/meetings folder...")
        os.makedirs("data/meetings")

def check_files():
    files =  [
        "data/meetings/meetings.json",
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
    meeting_bot = Meetings(bot)
    loop = asyncio.get_event_loop()
    loop.create_task(meeting_bot.check_meetings())
    bot.add_cog(meeting_bot)
