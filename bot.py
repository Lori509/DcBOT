import discord
from discord.ext import commands
import datetime
import os

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Speichert VoiceClient + Sink pro Guild, wenn Aufnahme aktiv ist
recording_tasks = {}

@bot.event
async def on_ready():
    print(f"✅ Bot ist online als {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def join(ctx, *, channel_name: str):
    """Tritt Voice-Channel bei und startet Aufnahme."""
    if ctx.guild.id in recording_tasks:
        await ctx.send("❌ Bot nimmt bereits in diesem Server auf.")
        return

    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name)
    if not channel:
        await ctx.send("❌ Voice-Channel nicht gefunden!")
        return

    try:
        vc = await channel.connect()
    except discord.ClientException:
        await ctx.send("❌ Bot ist bereits in einem Voice-Channel!")
        return

    await ctx.send(f"🎙️ Beigetreten zu `{channel.name}` und starte Aufnahme...")

    async def after_recording(sink, ctx):
        for user, audio in sink.audio_data.items():
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"aufnahme_{user.name}_{timestamp}.wav"
            with open(filename, "wb") as f:
                f.write(audio.file.read())
            await ctx.send(f"✅ Aufnahme gespeichert: `{filename}` für `{user.name}`")

    sink = discord.sinks.WaveSink()
    vc.start_recording(sink, after_recording, ctx)
    recording_tasks[ctx.guild.id] = (vc, sink)
    print(f"Recording gestartet für Guild {ctx.guild.id}")

@bot.command()
@commands.has_permissions(administrator=True)
async def leave(ctx):
    """Beendet Aufnahme und verlässt Voice-Channel."""
    if ctx.guild.id not in recording_tasks:
        await ctx.send("❌ Bot nimmt gerade nichts auf.")
        return

    vc, sink = recording_tasks[ctx.guild.id]
    vc.stop_recording()
    await vc.disconnect()
    del recording_tasks[ctx.guild.id]
    await ctx.send("🛑 Aufnahme beendet & Voice-Channel verlassen.")
    print(f"Recording gestoppt für Guild {ctx.guild.id}")

@join.error
@leave.error
async def permissions_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Nur Administratoren dürfen diesen Befehl verwenden.")

bot.run(os.getenv("DISCORD_BOT_TOKEN"))
