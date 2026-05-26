import random
import datetime
from random import randint

import discord
from discord.ext import commands, tasks
from storage import add_honor, remove_honor

from config import (
    ORDER_CHANNEL_ID, PURGE_CHANNEL_ID,
    NUKE_TARGET_ID, MANDRA_STICKER_ID,
    GOON_MESSAGES, VICTORIAN_URL, HATTO_URL,
    RANDOM_MSG_URL, BORN_TO_CAST_MSG,
)


def contains_goon(text: str) -> bool:
    import re
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    if "goon" in text:
        return True
    words = text.split()
    for i in range(len(words) - 1):
        if words[i] == "go" and words[i + 1] == "on":
            return True
    return False


class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_random_send = None
        self.last_order_message_id = None
        self.weekly_purge.start()

    def cog_unload(self):
        self.weekly_purge.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        # Reply to order replies
        if (
            message.channel.id == ORDER_CHANNEL_ID
            and message.reference is not None
            and message.reference.message_id == self.last_order_message_id
            and self.last_order_message_id is not None
        ):
            await message.reply("on it baws")

        # Sticker when mentioned
        if self.bot.user.mentioned_in(message):
            sticker = await self.bot.fetch_sticker(MANDRA_STICKER_ID)
            await message.channel.send(stickers=[sticker])

        # Random "go white boy go"
        if message.author.id == NUKE_TARGET_ID and random.randint(1, 100) == 1:
            await message.channel.send("go white boy go")

        # Goon trigger
        if contains_goon(message.content):
            await message.channel.send(random.choice(GOON_MESSAGES))

        user_message = message.content.lower()

        # Victorian cuisine
        if user_message == "victorian cuisine":
            await message.channel.send(VICTORIAN_URL)

        # Weekly rare message
        if random.randint(1, 999) == 2:
            now = datetime.datetime.utcnow()
            if (
                self.last_random_send is None
                or now - self.last_random_send >= datetime.timedelta(days=7)
            ):
                await message.channel.send(BORN_TO_CAST_MSG)
                self.last_random_send = now

        # Random ping
        if random.randint(1, 1000) == 1:
            await message.channel.send(f"<@{NUKE_TARGET_ID}>\n{RANDOM_MSG_URL}")
        # +rep / -rep
        if user_message.startswith("+rep") or user_message.startswith("-rep"):
            if message.mentions:
                target = message.mentions[0]
                if user_message.startswith("+rep"):
                    success, msg = add_honor(target.id, message.author.id)
                else:
                    success, msg = remove_honor(target.id, message.author.id)
                await message.channel.send(msg)
            else:
                await message.channel.send("Mention a user to rep.")
        # Hatto
        if user_message == "hatto":
            await message.channel.send(HATTO_URL)

    @tasks.loop(hours=168)
    async def weekly_purge(self):
        order_channel = self.bot.get_channel(ORDER_CHANNEL_ID)
        if order_channel is not None and randint(1, 5) == 4:
            try:
                sent = await order_channel.send("any new orders baws ?")
                self.last_order_message_id = sent.id
            except Exception as e:
                print(f"Failed to send order message: {e}")

        channel = self.bot.get_channel(PURGE_CHANNEL_ID)
        if channel is None:
            print("failed at censoring the bl*es")
            return

        deleted = 0
        async for msg in channel.history(limit=None, oldest_first=True):
            try:
                await msg.delete()
                deleted += 1
            except discord.Forbidden:
                print("the bl*es won.")
                return
            except discord.HTTPException:
                pass

        print(f"blues: deleted {deleted} messages")

    @weekly_purge.before_loop
    async def before_weekly_purge(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
