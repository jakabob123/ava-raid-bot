import discord
from discord.ext import commands
from discord import app_commands
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)

raid_data = {}

EMOJI_ROLES = {
    "🛡️": "Tank",
    "💉": "Heal",
    "🔮": "One Hand Arcane",
    "✨": "Great Arcane",
    "😈": "Incubus",
    "🧪": "Debuff",
    "⚔️": "DPS",
    "🔁": "Queue",
    "❌": "Cancel"
}

ROLE_LIMITS = {
    "Tank": 1,
    "Heal": 1,
    "One Hand Arcane": 1,
    "Great Arcane": 1,
    "Incubus": 1,
    "Debuff": 1,
    "DPS": 3,
    "Queue": 99,
    "Cancel": 99
}


class AvaRaid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ava", description="Buat event Ava Raid")
    async def ava(self, interaction: discord.Interaction, title: str, date: str, time: str):
        await interaction.response.defer(thinking=False)

        event_id = f"{interaction.channel.id}-{interaction.id}"
        raid_data[event_id] = {
            "title": title,
            "date": date,
            "time": time,
            "message_id": None,
            "roles": {role: [] for role in ROLE_LIMITS}
        }

        embed = self.generate_embed(raid_data[event_id])
        message = await interaction.channel.send(embed=embed)
        raid_data[event_id]["message_id"] = message.id

        for emoji in EMOJI_ROLES:
            await message.add_reaction(emoji)

        await interaction.followup.send(f"✅ Raid event **{title}** dibuat!", ephemeral=True)

    def generate_embed(self, event):
        embed = discord.Embed(title=event["title"], color=0x5865F2)
        embed.add_field(name="📅 Event Info:", value=f'**{event["date"]}** ⏰ **{event["time"]}**', inline=False)

        for role in ROLE_LIMITS:
            names = event["roles"].get(role, [])
            limit = ROLE_LIMITS[role]
            display = "\n".join([f"{i+1}. {name}" for i, name in enumerate(names)]) if names else "-"
            embed.add_field(name=f"{role} ({len(names)}/{limit})", value=display, inline=True)

        return embed


@bot.event
async def on_ready():
    print(f"🤖 Bot aktif sebagai {bot.user}")
    await bot.tree.sync()


@bot.event
async def on_raw_reaction_add(payload):
    if payload.member is None or payload.member.bot:
        return

    matched_event = None
    for event_id, data in raid_data.items():
        if data["message_id"] == payload.message_id:
            matched_event = event_id
            break

    if not matched_event:
        return

    emoji = str(payload.emoji)
    role = EMOJI_ROLES.get(emoji)
    if not role:
        return

    event = raid_data[matched_event]
    name = payload.member.display_name

    # Hapus dari semua role terlebih dahulu
    for r in event["roles"]:
        if name in event["roles"][r]:
            event["roles"][r].remove(name)

    # Toggle masuk kalau sebelumnya belum di role ini
    if role != "Cancel":
        if name not in event["roles"][role] and len(event["roles"][role]) < ROLE_LIMITS[role]:
            event["roles"][role].append(name)
        elif len(event["roles"][role]) >= ROLE_LIMITS[role]:
            event["roles"]["Queue"].append(name)
    else:
        event["roles"]["Cancel"].append(name)

    # Update embed
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    embed = AvaRaid(bot).generate_embed(event)
    await message.edit(embed=embed)

    # Hapus reaksi user agar bisa klik ulang
    await message.remove_reaction(payload.emoji, payload.member)


bot.tree.add_command(AvaRaid(bot).ava)
bot.run("MTM4NjU3NTU4NTU1OTU3NjY5Nw.G56kS1.aT0OssAGfI_Fq_khRD_nPLws1OyR4nSK5zzHpQ")
