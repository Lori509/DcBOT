import discord
from discord.ext import commands
import os
import datetime

# Stelle sicher, dass du diesen Token ersetzt oder als Umgebungsvariable setzt
TOKEN = os.getenv("DISCORD_BOT_TOKEN") or "DEIN_BOT_TOKEN"

# Intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

# Bot initialisieren
bot = commands.Bot(command_prefix="!", intents=intents)

# Aufnahme-Speicher
recording_sessions = {}

@bot.event
async def on_ready():
    print(f"✅ Bot ist online: {bot.user}")

@bot.command()
@commands.has_permissions(administrator=True)
async def join(ctx, *, channel_name: str):
    """Tritt einem Voice-Channel bei und startet die Aufnahme."""
    if ctx.guild.id in recording_sessions:
        await ctx.send("⚠️ Aufnahme läuft bereits.")
        return

    channel = discord.utils.get(ctx.guild.voice_channels, name=channel_name)
    if not channel:
        await ctx.send("❌ Channel nicht gefunden!")
        return

    try:
        vc = await channel.connect()
        await ctx.send(f"🎙️ Beigetreten zu `{channel.name}` und starte Aufnahme...")

        # Audio sink vorbereiten
        sink = discord.sinks.WaveSink()

        async def after_recording(sink, ctx):
            for user, audio in sink.audio_data.items():
                filename = f"aufnahme_{user.name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                audio.file.seek(0)
                with open(filename, "wb") as f:
                    f.write(audio.file.read())
                await ctx.send(f"✅ Aufnahme gespeichert: `{filename}`")

        vc.start_recording(sink, after_recording, ctx)
        recording_sessions[ctx.guild.id] = (vc, sink)

    except Exception as e:
        await ctx.send(f"❌ Fehler beim Beitreten: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def leave(ctx):
    """Beendet die Aufnahme und verlässt den Voice-Channel."""
    session = recording_sessions.get(ctx.guild.id)
    if session:
        vc, sink = session
        if vc.is_connected():
            vc.stop_recording()
            await vc.disconnect()
            await ctx.send("🛑 Aufnahme gestoppt & Voice-Channel verlassen.")
        else:
            await ctx.send("⚠️ Bot ist nicht verbunden.")
        del recording_sessions[ctx.guild.id]
    else:
        await ctx.send("❌ Bot nimmt gerade nichts auf.")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("🚫 Du brauchst Administratorrechte für diesen Befehl.")
    else:
        await ctx.send(f"❌ Fehler: {str(error)}")
        raise error  # Für Logs in der Konsole

# Bot starten


bot.run(os.getenv("DISCORD_BOT_TOKEN"))
