import discord
from discord.ext import commands
import asyncio
import datetime

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

recording_tasks = {}

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def join(ctx, *, channel_name: str):
    """[ADMIN] Tritt dem angegebenen Voice-Channel bei und startet die Aufnahme"""
    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name)
    if not channel:
        await ctx.send("❌ Channel nicht gefunden!")
        return

    vc = await channel.connect()
    await ctx.send(f"🎙️ Beigetreten zu `{channel.name}` und starte endlose Aufnahme...")

    async def after_recording(sink, ctx):
        for user, audio in sink.audio_data.items():
            filename = f"aufnahme_{user.name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            with open(filename, "wb") as f:
                f.write(audio.file.read())
            await ctx.send(f"✅ Aufnahme gespeichert für `{user.name}` als `{filename}`")

    sink = discord.sinks.WaveSink()
    vc.start_recording(sink, after_recording, ctx)
    recording_tasks[ctx.guild.id] = (vc, sink)

@bot.command()
@commands.has_permissions(administrator=True)
async def leave(ctx):
    """[ADMIN] Beendet die Aufnahme und verlässt den Voice-Channel"""
    if ctx.guild.id in recording_tasks:
        vc, sink = recording_tasks[ctx.guild.id]
        vc.stop_recording()
        await vc.disconnect()
        await ctx.send("🛑 Aufnahme beendet & Voice-Channel verlassen.")
        del recording_tasks[ctx.guild.id]
    else:
        await ctx.send("❌ Bot nimmt gerade nichts auf.")

@join.error
@leave.error
async def permissions_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Nur Administratoren dürfen diesen Befehl verwenden.")

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
