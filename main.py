import discord
import random
from random import randint
import os
import json
import re
import datetime
from discord import app_commands
from discord.ext import tasks
from PIL import Image, ImageDraw
import aiohttp
import io
#git has been added finally

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is missing")
PURGE_CHANNEL_ID = 1346807075153645681
ORDER_CHANNEL_ID = 1430331529099215031
DATA_FILE = "dm_blocked.json"
STONE_FILE = "stone_leaderboard.json"
HUG_BACKGROUND_URL = (
    "https://media.discordapp.net/attachments/1462490936490856582/"
    "1462490937073729780/Mandra_Hug2.jpeg"
)

MAKURA_ID = 400140550503923713
NUKE_TARGET_ID = 644586863881093120
SAY_CHANNEL_ID = 1205588718774263860

intents = discord.Intents.default()
intents.message_content = True

INSULTS = [
    "stinky",
    "cringe",
    "lame",
    "embarrassing",
    "unwashed",
    "terminally online",
]
GOON_MESSAGES = [
    "good idea baws",
    "aye boss",
    "sounds right, baws",
    "whatever you say, baws",
    "you got it, boss",
    "yeah yeah, makes sense baws",
]

last_random_send = None
last_order_message_id = None

ALLOWED_ROLE_IDS = {
    1315105809658544209,
    1395006533347180624,
    1315090029982384169,
    1345758044499476501,
    1385296517975375993,
    1315091467127230534,
    1315102680775135324,
    1238573370220740729,
    1346800838491897891,
    1315094176072732723,
}

ROLE_CHANNEL_MAP = {
    1346808567130230804: 1315105809658544209,
    1395007020163268669: 1395006533347180624,
    1346809772070141952: 1315090029982384169,
    1346806389359775846: 1345758044499476501,
    1346807075153645681: 1385296517975375993,
    1346806767228555345: 1315091467127230534,
    1346806929065771072: 1315102680775135324,
    1368902634437738617: 1238573370220740729,
}


def load_blocked_users():
    if not os.path.exists(DATA_FILE):
        return set()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()

def save_blocked_users(blocked_users):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(blocked_users), f)

def load_stone_data():
    if not os.path.exists(STONE_FILE):
        return {}
    try:
        with open(STONE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_stone_data(data):
    with open(STONE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

def contains_goon(text: str) -> bool:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    if "goon" in text:
        return True
    words = text.split()
    for i in range(len(words) - 1):
        if words[i] == "go" and words[i + 1] == "on":
            return True
    return False


class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.dm_blocked_users = load_blocked_users()
        self.stone_data = load_stone_data()

    async def setup_hook(self):
        await self.tree.sync()

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        print(f"Loaded {len(self.dm_blocked_users)} blocked users")
        if not weekly_purge.is_running():
            weekly_purge.start()


client = MyClient()

ROLE_TO_CHANNEL = {role: channel for channel, role in ROLE_CHANNEL_MAP.items()}


# /stone
@client.tree.command(name="stone", description="Attempt to stone another user")
@app_commands.describe(user="User to stone")
async def stone(interaction: discord.Interaction, user: discord.User):
    brick_gif = "https://tenor.com/view/cat-throwing-brick-brick-cat-gif-9142560192559212520"
    parry_gif = "https://tenor.com/view/ultrakill-funny-cat-cat-parry-explode-gif-12515622299668151985"
    nuke_gif = "https://tenor.com/mB9C7DzBBge.gif"
    immunity_gif = "https://tenor.com/b1SeM.gif"

    stoner_id = str(interaction.user.id)
    target_id = str(user.id)

    if user.id == MAKURA_ID:
        await interaction.response.send_message(
            f"makura has been granted stone immunity by the great mandra\n{immunity_gif}",
            allowed_mentions=discord.AllowedMentions.none()
        )
        return

    if user.id == NUKE_TARGET_ID:
        client.stone_data[target_id] = client.stone_data.get(target_id, 0) + 1
        save_stone_data(client.stone_data)
        await interaction.response.send_message(
            f"{interaction.user.name} stones {user.name}\n{nuke_gif}",
            allowed_mentions=discord.AllowedMentions.none()
        )
        return

    if random.choice([True, False]):
        client.stone_data[target_id] = client.stone_data.get(target_id, 0) + 1
        save_stone_data(client.stone_data)
        await interaction.response.send_message(
            f"{interaction.user.name} stones {user.name}\n{brick_gif}",
            allowed_mentions=discord.AllowedMentions.none()
        )
    else:
        client.stone_data[stoner_id] = client.stone_data.get(stoner_id, 0) + 1
        save_stone_data(client.stone_data)
        await interaction.response.send_message(
            f"{interaction.user.mention} you got parried!\n{parry_gif}"
        )


# /hug
@client.tree.command(name="hug", description="Hug another user")
@app_commands.describe(user="User to hug")
async def hug(interaction: discord.Interaction, user: discord.User):
    await interaction.response.defer()

    background_path = os.path.join(os.path.dirname(__file__), "Mandra_Hug2.jpeg")

    if not os.path.exists(background_path):
        await interaction.followup.send("Hug image missing on server.")
        return

    avatar_url = user.display_avatar.replace(size=256, format="png").url

    headers = {"User-Agent": "DiscordBot (Mandrabot)"}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(avatar_url) as av_resp:
            if av_resp.status != 200:
                await interaction.followup.send("Failed to load avatar.")
                return
            avatar_bytes = await av_resp.read()

    background = Image.open(background_path).convert("RGBA")
    avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

    avatar_size = 210
    outline_size = 6
    avatar = avatar.resize((avatar_size, avatar_size))

    total_size = avatar_size + outline_size * 2
    outline = Image.new("RGBA", (total_size, total_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(outline)
    draw.ellipse((0, 0, total_size, total_size), fill=(0, 0, 0, 255))

    mask = Image.new("L", (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
    avatar.putalpha(mask)

    outline.paste(avatar, (outline_size, outline_size), avatar)

    bg_w, bg_h = background.size
    position = (
        (bg_w - total_size) // 2 - 15,
        (bg_h - total_size) // 2 + 145,
    )

    background.paste(outline, position, outline)

    buffer = io.BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)

    await interaction.followup.send(file=discord.File(buffer, filename="hug.png"))


# /stoneboard
@client.tree.command(name="stoneboard", description="View the stoning leaderboard")
async def stoneboard(interaction: discord.Interaction):
    if not client.stone_data:
        await interaction.response.send_message("No one has been stoned yet.", ephemeral=True)
        return

    sorted_board = sorted(client.stone_data.items(), key=lambda x: x[1], reverse=True)

    lines = []
    for i, (user_id, points) in enumerate(sorted_board[:10], start=1):
        try:
            user = await client.fetch_user(int(user_id))
            name = user.name
        except Exception:
            name = f"Unknown User ({user_id})"
        lines.append(f"**{i}.** {name} — **{points}**")

    await interaction.response.send_message("🪨 **STONING LEADERBOARD** 🪨\n" + "\n".join(lines))


# /insult
@client.tree.command(name="insult", description="Insult another role in their channel")
@app_commands.describe(role="Role to insult")
async def insult(interaction: discord.Interaction, role: discord.Role):
    member = interaction.user

    caller_role = None
    for r in member.roles:
        if r.id in ROLE_TO_CHANNEL:
            caller_role = r
            break

    insult_word = random.choice(INSULTS)

    if caller_role is None:
        await interaction.response.send_message("You don't have permission to insult anyone.", ephemeral=True)
        return

    if role.id not in ROLE_TO_CHANNEL:
        await interaction.response.send_message("That role cannot be insulted.", ephemeral=True)
        return

    target_channel_id = ROLE_TO_CHANNEL[role.id]
    target_channel = interaction.guild.get_channel(target_channel_id)

    if target_channel is None:
        await interaction.response.send_message("Target channel not found.", ephemeral=True)
        return

    if role.id == caller_role.id:
        await target_channel.send(f"{interaction.user.name}, you called your own role **{insult_word}**. Embarrassing.")
        await interaction.response.send_message(f"Insult delivered to {target_channel.mention}.", ephemeral=True)
        return

    await target_channel.send(f"{role.name}, {caller_role.name} called you **{insult_word}**.")
    await interaction.response.send_message(f"Insult delivered to {target_channel.mention}.", ephemeral=True)


# /mandrapet
@client.tree.command(name="mandrapet", description="mandra pet")
async def mandrapet(interaction: discord.Interaction):
    await interaction.response.send_message(
        "https://media.discordapp.net/attachments/1462490936490856582/1462491111921549573/MANDY_SMILE_TRANS.gif"
    )


# /pillar
@client.tree.command(name="pillar", description="pillar")
async def pillar(interaction: discord.Interaction):
    await interaction.response.send_message(
        "https://media.discordapp.net/attachments/586588921614303233/1446964632970596372/10N04_Mandragora.gif"
    )


# /feedmandra
@client.tree.command(name="feedmandra", description="Feed the Mandra bot some rock candy!")
async def feedmandra(interaction: discord.Interaction):
    if random.randint(1, 10) == 1:
        await interaction.response.send_message(
            "you fed it a rock. <:KILL:1471974665252507814>"
        )
    else:
        await interaction.response.send_message(
            "you fed mandrabot candy! <:mandralove:1474115259659714816>"
        )


# /say
@client.tree.command(name="say", description="Internal use only")
@app_commands.describe(message="Message to send")
async def ventriloquist(interaction: discord.Interaction, message: str):
    if interaction.user.id != MAKURA_ID:
        await interaction.response.send_message("Mandrabot resists your attempt at mind control.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    target_channel = client.get_channel(SAY_CHANNEL_ID)
    if target_channel is None:
        await interaction.followup.send("Target channel not found.", ephemeral=True)
        return

    await target_channel.send(message, allowed_mentions=discord.AllowedMentions.none())
    await interaction.followup.send("Message sent.", ephemeral=True)


# Single on_message handler
@client.event
async def on_message(message):
    global last_random_send, last_order_message_id

    if message.author == client.user:
        return

    if (
        message.channel.id == ORDER_CHANNEL_ID
        and message.reference is not None
        and message.reference.message_id == last_order_message_id
        and last_order_message_id is not None
    ):
        await message.reply("on it baws")

    if client.user.mentioned_in(message):
        sticker = await client.fetch_sticker(1274672953803669585)
        await message.channel.send(stickers=[sticker])

    if message.author.id == 644586863881093120:
        if random.randint(1, 100) == 1:
            await message.channel.send("go white boy go")

    if contains_goon(message.content):
        await message.channel.send(random.choice(GOON_MESSAGES))

    user_message = message.content.lower()

    if user_message == 'victorian cuisine':
        await message.channel.send(
            "https://images-ext-1.discordapp.net/external/cgUQPEYpzmj7jm5D1R1lwVw_OHlHeaVU4XdY1W8E8T8/https/i.imgur.com/exNU6Rf.mp4"
        )

    if random.randint(1, 999) == 2:
        now = datetime.datetime.utcnow()
        if (
            last_random_send is None
            or now - last_random_send >= datetime.timedelta(days=7)
        ):
            await message.channel.send(
                "BORN TO CAST VICTORIA IS A FUCK 鬼神 Kill Em All 1091 "
                "I am rock cat410,757,864,530 DEAD VICTORIANS"
            )
            last_random_send = now

    if random.randint(1, 1000) == 1:
        await message.channel.send(
            "<@644586863881093120>\n"
            "https://media.discordapp.net/attachments/1346809772070141952/1354376217410670698/"
            "SPOILER_picmix.com_12527279.gif?ex=696defa5&is=696c9e25&hm="
            "3ab21403e0ea38f6f5bd1227a646a312b8da8968a7e929f3f0aa8dad20705668&=&width=620&height=620"
        )

    if user_message == "hatto":
        await message.channel.send(
            "https://media.discordapp.net/attachments/1432125742396735532/1453363990511091762/hatto.jpg"
        )


@tasks.loop(hours=168)
async def weekly_purge():
    global last_order_message_id

    order_channel = client.get_channel(ORDER_CHANNEL_ID)
    if order_channel is not None and (randint(1, 5) == 4):
        try:
            sent = await order_channel.send("any new orders baws ?")
            last_order_message_id = sent.id
        except Exception as e:
            print(f"Failed to send order message: {e}")

    channel = client.get_channel(PURGE_CHANNEL_ID)

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
async def before_weekly_purge():
    await client.wait_until_ready()


client.run(TOKEN)
