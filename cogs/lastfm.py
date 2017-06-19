import os
import urllib
import discord
import aiohttp
import datetime
from .utils import checks
from discord.ext import commands
from __main__ import send_cmd_help
from cogs.utils.dataIO import dataIO


class Lastfm:
    """Le Last.fm cog"""
    def __init__(self, bot):
        self.bot = bot
        self.settings_file = 'data/lastfm/lastfm.json'
        settings = dataIO.load_json(self.settings_file)
        self.api_key = settings['LASTFM_API_KEY']

        self.payload = {}
        self.payload['api_key'] = self.api_key
        self.payload['format'] = 'json'

    async def _url_decode(self, url):
        # Fuck non-ascii URLs!!!@##$@
        url = urllib.parse.urlparse(url)
        url = '{0.scheme}://{0.netloc}{1}'.format(url, urllib.parse.quote(url.path))
        return url

    async def _api_request(self, payload):
        url = 'http://ws.audioscrobbler.com/2.0/'
        headers = {'user-agent': 'Red-cog/1.0'}
        conn = aiohttp.TCPConnector()
        session = aiohttp.ClientSession(connector=conn)
        async with session.get(url, params=payload, headers=headers) as r:
            data = await r.json()
        session.close()
        return data

    @commands.group(pass_context=True, name='lastfm', aliases=['lf'])
    async def _lastfm(self, context):
        """Get Last.fm statistics of a user.

Will remember your username after setting one. [p]lastfm last @username will become [p]lastfm last."""
        if context.invoked_subcommand is None:
            await send_cmd_help(context)

    @_lastfm.command(pass_context=True, name='set')
    async def _set(self, context, username: str):
        """Set a username"""

        try:
            payload = self.payload
            payload['method'] = 'user.getInfo'
            payload['username'] = username
            data = await self._api_request(payload)
        except Exception as e:
            message = 'Something went terribly wrong! [{}]'.format(e)
        if 'error' in data:
            message = '{}'.format(data['message'])
        else:
            settings = dataIO.load_json(self.settings_file)
            settings['USERS'][context.message.author.id] = username
            username = username
            dataIO.save_json(self.settings_file, settings)
            message = 'Username set'
        await self.bot.say(message)

    @_lastfm.command(pass_context=True, name='info')
    async def _info(self, context, *username: str):
        """Retrieve general information"""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['method'] = 'user.getInfo'
                payload['username'] = username
                data = await self._api_request(payload)
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = '{}'.format(data['message'])
                await self.bot.say(message)
            else:
                user = data['user']['name']
                playcount = data['user']['playcount']
                registered = datetime.datetime.fromtimestamp(data['user']['registered']['#text']).strftime('%Y-%m-%d')
                image = data['user']['image'][1]['#text']
                author = context.message.author
                em = discord.Embed(url='http://www.last.fm/user/{}'.format(user), description='\a\n')
                avatar = author.avatar_url if author.avatar else author.default_avatar_url
                em.set_author(name='Last.fm profile of {} ({})'.format(user, author.name), icon_url=avatar)
                if 'realname' in data['user']:
                    realname = data['user']['realname']
                    em.add_field(name='Name', value=realname)
                if 'country' in data['user']:
                    if data['user']['country']:
                        em.add_field(name='Country', value=data['user']['country'])
                em.add_field(name='Scrobbles', value=playcount)
                em.add_field(name='Registered', value=registered)
                em.set_thumbnail(url=image)
                await self.bot.say(embed=em)
        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
            await self.bot.say(message)

    @_lastfm.command(pass_context=True, name='now')
    async def _now(self, context, *username: str):
        """Shows the current played song"""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['method'] = 'user.getRecentTracks'
                payload['username'] = username
                payload['limit'] = 1
                data = await self._api_request(payload)
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = '{}'.format(data['message'])
                await self.bot.say(message)
            else:
                user = data['recenttracks']['@attr']['user']
                track = data['recenttracks']['track'][0]
                try:
                    if track['@attr']['nowplaying'] == 'true':
                        artist = track['artist']['#text']
                        song = track['name']
                        url = await self._url_decode(track['url'])
                        image = track['image'][-1]['#text']
                        author = context.message.author
                        em = discord.Embed(url=url)
                        avatar = author.avatar_url if author.avatar else author.default_avatar_url
                        em.set_author(name='{} - {}'.format(artist, song), icon_url=avatar)
                        if not self.bot.get_cog('YouTube'):
                            em.set_image(url=image)
                        await self.bot.say(embed=em)
                        if self.bot.get_cog('YouTube'):
                            await context.invoke(self.bot.get_cog('YouTube')._youtube, query='{} - {}'.format(artist, song))
                except KeyError:
                    await self.bot.say('{} is not playing any song right now'.format(user))
        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
            await self.bot.say(message)

    @_lastfm.command(pass_context=True, name='recent', aliases=['lp', 'last'])
    async def _recent(self, context, *username: str):
        """Shows recent tracks"""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['limit'] = '11'
                payload['method'] = 'user.getRecentTracks'
                payload['username'] = username
                data = await self._api_request(payload)
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = data['message']
                await self.bot.say(message)
            else:
                user = data['recenttracks']['@attr']['user']
                author = context.message.author
                l = ''
                for i, track in enumerate(data['recenttracks']['track'], 1):
                    artist = track['artist']['#text']
                    song = track['name']
                    url = await self._url_decode(track['url'])
                    if i < 10:
                        l += '`{}`\t  **[{}]({})** by **{}**\n'.format(str(i), song, url, artist)
                    elif i > 10:
                        break
                    else:
                        l += '`{}`\t**[{}]({})** by **{}**\n'.format(str(i), song, url, artist)
                em = discord.Embed(description=l, url='http://www.last.fm/user/{}/library'.format(user))
                avatar = author.avatar_url if author.avatar else author.default_avatar_url
                em.set_author(name='{}\'s Recent Tracks'.format(user), icon_url=avatar)
                await self.bot.say(embed=em)
        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
            await self.bot.say(message)

    @_lastfm.command(pass_context=True, name='toptracks', aliases=['tracks', 'ttr'])
    async def _toptracks(self, context, *username: str):
        """Shows most played tracks"""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['limit'] = '11'
                payload['method'] = 'user.getTopTracks'
                payload['username'] = username
                data = await self._api_request(payload)
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = data['message']
                await self.bot.say(message)
            else:
                user = data['toptracks']['@attr']['user']
                author = context.message.author
                l = ''
                for i, track in enumerate(data['toptracks']['track'], 1):
                    artist = track['artist']['name']
                    song = track['name']
                    url = await self._url_decode(track['url'])
                    plays = track['playcount']
                    if i < 10:
                        l += '`{}`\t  **[{}]({})** by **{}** ({} plays)\n'.format(str(i), song, url, artist, plays)
                    elif i > 10:
                        break
                    else:
                        l += '`{}`\t**[{}]({})** by **{}** ({} plays)\n'.format(str(i), song, url, artist, plays)
                em = discord.Embed(description=l, url='http://www.last.fm/user/{}/library/tracks'.format(user))
                avatar = author.avatar_url if author.avatar else author.default_avatar_url
                em.set_author(name='{}\'s Top Tracks'.format(user), icon_url=avatar)
                await self.bot.say(embed=em)
        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
            await self.bot.say(message)

    @_lastfm.command(pass_context=True, name='topartists', aliases=['artists', 'tar'])
    async def _topartists(self, context, *username: str):
        """Shows most played artists"""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['limit'] = '11'
                payload['method'] = 'user.getTopArtists'
                payload['username'] = username
                data = await self._api_request(payload)
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)
            if 'error' in data:
                message = data['message']
                await self.bot.say(message)
            else:
                user = data['topartists']['@attr']['user']
                author = context.message.author
                l = ''
                for i, artist in enumerate(data['topartists']['artist'], 1):
                    artist_a = artist['name']
                    url = await self._url_decode(artist['url'])
                    plays = artist['playcount']
                    if i < 10:
                        l += '`{}`\t  **[{}]({})** ({} plays)\n'.format(str(i), artist_a, url, plays)
                    elif i > 10:
                        break
                    else:
                        l += '`{}`\t**[{}]({})** ({} plays)\n'.format(str(i), artist_a, url, plays)
                em = discord.Embed(description=l, url='http://www.last.fm/user/{}/library/artists'.format(user))
                avatar = author.avatar_url if author.avatar else author.default_avatar_url
                em.set_author(name='{}\'s Top Artists'.format(user), icon_url=avatar)
                await self.bot.say(embed=em)
        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
            await self.bot.say(message)

    @_lastfm.command(pass_context=True, name='topalbums', aliases=['albums', 'tab'])
    async def _topalbums(self, context, *username: str):
        """Shows most played albums"""
        if self.api_key != '':
            if not username:
                settings = dataIO.load_json(self.settings_file)
                if context.message.author.id in settings['USERS']:
                    username = settings['USERS'][context.message.author.id]
            else:
                user_patch = username[0].replace('!', '')
                settings = dataIO.load_json(self.settings_file)
                if user_patch[2:-1] in settings['USERS']:
                    username = settings['USERS'][user_patch[2:-1]]
                else:
                    username = user_patch
            try:
                payload = self.payload
                payload['limit'] = '11'
                payload['method'] = 'user.getTopAlbums'
                payload['username'] = username
                data = await self._api_request(payload)
            except Exception as e:
                message = 'Something went terribly wrong! [{}]'.format(e)

            if 'error' in data:
                message = data['message']
                await self.bot.say(message)
            else:
                user = data['topalbums']['@attr']['user']
                author = context.message.author
                l = ''
                for i, album in enumerate(data['topalbums']['album'], 1):
                    albums = album['name']
                    artist = album['artist']['name']
                    url = await self._url_decode(album['url'])
                    plays = album['playcount']
                    if i < 10:
                        l += '`{}`\t  **[{}]({})** by **({})** ({} plays)\n'.format(str(i), albums, url, artist, plays)
                    elif i > 10:
                        break
                    else:
                        l += '`{}`\t**[{}]({})** by **({})** ({} plays)\n'.format(str(i), albums, url, artist, plays)
                em = discord.Embed(description=l, url='http://www.last.fm/user/{}/library/albums'.format(user))
                avatar = author.avatar_url if author.avatar else author.default_avatar_url
                em.set_author(name='Top Albums by {}'.format(user), icon_url=avatar)
                await self.bot.say(embed=em)
        else:
            message = 'No API key set for Last.fm. Get one at http://www.last.fm/api'
            await self.bot.say(message)

    @_lastfm.command(pass_context=True, name='apikey')
    @checks.is_owner()
    async def _apikey(self, context, *key: str):
        """Sets the Last.fm API key - for bot owner only."""
        settings = dataIO.load_json(self.settings_file)
        if key:
            settings['LASTFM_API_KEY'] = key[0]
            self.api_key = key[0]
            dataIO.save_json(self.settings_file, settings)
            await self.bot.say('**Done**')
        else:
            await self.bot.say('**I need more than that!**')


def check_folder():
    if not os.path.exists("data/lastfm"):
        print("Creating data/lastfm folder...")
        os.makedirs("data/lastfm")


def check_file():
    data = {}
    data['LASTFM_API_KEY'] = ''
    data['USERS'] = {}
    f = "data/lastfm/lastfm.json"
    if not dataIO.is_valid_json(f):
        print("Creating default lastfm.json...")
        dataIO.save_json(f, data)


def setup(bot):
    check_folder()
    check_file()
    n = Lastfm(bot)
    bot.add_cog(n)
