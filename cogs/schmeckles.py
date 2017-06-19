import re


class Schmeckles:
    def __init__(self, bot):
        self.bot = bot
        self.p = re.compile('([^\n\.\,\r\d-]{0,30})(-?[\d|,]{0,300}\.{0,1}\d{1,300} schmeckle[\w]{0,80})([^\n\.\,\r\d-]{0,30})', re.IGNORECASE)

    async def schmeckle2usd(self, schmeckle):
        """1 Schmeckle = $148 USD
        https://www.reddit.com/r/IAmA/comments/202owt/we_are_dan_harmon_and_justin_roiland_creators_of/cfzfv79"""
        return schmeckle * 148.0

    async def schmeckle2eur(self, schmeckle):
        return schmeckle * 139.25   # latest USDEUR value

    async def schmeckle2yen(self, schmeckle):
        return schmeckle * 139.25   # latest USDYEN value

    async def schmeckle2rub(self, schmeckle):
        return schmeckle * 139.25   # latest USDRUB value

    async def searchForSchmeckles(self, content):
        if any([x in content.lower() for x in ['?', 'how much', 'what is', 'how many', 'euro', 'usd', 'dollars', 'dollar', 'euros']]):
            return self.p.search(content)
        return None

    async def getSchmeckles(self, content):
        get_schmeckles = await self.searchForSchmeckles(content)
        if get_schmeckles:
            match = get_schmeckles.groups()
            euro = any([x in match[-1].lower() for x in ['eur', 'euro', 'euros']])
            dollar = any([x in match[-1].lower() for x in ['usd', 'dollar', 'dollars']])
            if euro and not dollar:
                value = await self.schmeckle2eur(float(match[1].split()[0])), 'EUR', match[1].split()[0]
            elif dollar and not euro:
                value = await self.schmeckle2usd(float(match[1].split()[0])), 'USD', match[1].split()[0]
            elif not dollar and not euro:
                value = await self.schmeckle2usd(float(match[1].split()[0])), 'USD', match[1].split()[0]
            return value
        return None

    async def _on_message(self, message):
        content = message.content
        author = message.author
        channel = message.channel
        if author.id != self.bot.user.id:
            schmeckles = await self.getSchmeckles(content)
            if schmeckles:
                await self.bot.send_message(channel, '{0[2]} SHM is about {0[0]:.2f} {0[1]}'.format(schmeckles))


def setup(bot):
    cog = Schmeckles(bot)
    bot.add_listener(cog._on_message, "on_message")
    bot.add_cog(cog)
