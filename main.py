import random  
import os                           
import discord                      
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv      
import yt_dlp                       
from collections import deque       
import asyncio                      
import logging

logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w') 

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

SONG_QUEUES = {}        
LOOP_FLAGS = {}  

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()           
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)

@bot.event
async def on_ready():
    await bot.tree.sync()


@bot.tree.command(name="loop", description="Toggles looping of the current queue.")
async def loop(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)

    current_state = LOOP_FLAGS.get(guild_id, False)
    LOOP_FLAGS[guild_id] = not current_state

    if LOOP_FLAGS[guild_id]:
        await interaction.response.send_message("🔁 Loop is now **enabled**.")
    else:
        await interaction.response.send_message("⏹️ Loop is now **disabled**.")


@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")

    else:
        await interaction.response.send_message("Not playing anything to skip.")


@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is currently playing.")
    
    voice_client.pause()
    await interaction.response.send_message("Playback paused!")


@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    
    voice_client = interaction.guild.voice_client

    
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    
    if not voice_client.is_paused():
        return await interaction.response.send_message("I’m not paused right now.")
    
    
    voice_client.resume()
    await interaction.response.send_message("Playback resumed!")



@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    
    voice_client = interaction.guild.voice_client

    
    if not voice_client or not voice_client.is_connected():
        return await interaction.response.send_message("I'm not connected to any voice channel.")

    
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    
    await voice_client.disconnect()

    await interaction.response.send_message("Stopped playback and disconnected!")


@bot.tree.command(name="queue", description="Shows the current song queue.")
async def show_queue(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    queue = SONG_QUEUES.get(guild_id)

    if not queue or len(queue) == 0:
        await interaction.response.send_message("The queue is currently empty.")
        return

    queue_list = [f"{i+1}. {title}" for i, (_, title) in enumerate(queue)]
    queue_text = "\n".join(queue_list)

    if len(queue_text) > 1900:
        queue_text = queue_text[:1900] + "\n...and more."

    await interaction.response.send_message(f"🎶 **Current Queue:**\n{queue_text}")


@bot.tree.command(name="shuffle", description="Shuffles the current queue.")
async def shuffle_queue(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    queue = SONG_QUEUES.get(guild_id)

    if not queue or len(queue) < 2:
        await interaction.response.send_message("Not enough songs to shuffle the queue.")
        return

    queue_list = list(queue)
    random.shuffle(queue_list)
    SONG_QUEUES[guild_id] = deque(queue_list)

    await interaction.response.send_message("🔀 Queue shuffled!")


@bot.tree.command(name="play",description="Play a song or add it to the queue")
@app_commands.describe(song_query="Search query")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()      
    voice_channel = interaction.user.voice.channel

    if voice_channel is None:
        await interaction.followup.send("You must be in a voice channel.")
        return
    
    voice_client = interaction.guild.voice_client

    if voice_client is None:
        voice_client = await voice_channel.connect()
    elif voice_channel != voice_client.channel:
        await voice_client.move_to(voice_channel)

    ydl_options = {
        "format": "bestaudio[abr<=256]/bestaudio",
        "noplaylist": False,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }

    if song_query.startswith("http"):
        query = song_query
    else:
        query = "ytsearch1:" + song_query

    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [results])

    if tracks is None:
        await interaction.followup.send("No results found.")
        return
    
    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    for i, track in enumerate(tracks):
        audio_url = track["url"]
        title = track.get("title", "Untitled")
        SONG_QUEUES[guild_id].append((audio_url, title))

    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(f"Added **{len(tracks)}** song(s) to queue.")
    else:
        await interaction.followup.send(f"Now playing: **{tracks[0]['title']}**")
        await play_next_song(voice_client, guild_id, interaction.channel)
    
    
async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        
        audio_url, title = SONG_QUEUES[guild_id].popleft()
        
        if LOOP_FLAGS.get(guild_id, False):
            SONG_QUEUES[guild_id].append((audio_url, title))

        ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                "options": "-vn -c:a libopus -b:a 96k",  
        }

        source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable = "D:\\coding\\Experiments\\MusicBot\\bin\\ffmpeg\\ffmpeg.exe")
        def after_play(error):
            if error:
                print(f"[ERROR in after_play]: {error}")

            future = asyncio.run_coroutine_threadsafe(
                play_next_song(voice_client, guild_id, channel),
                bot.loop
            )
            
            try:
                future.result()
            except Exception as e:
                print(f"[ERROR while playing next song]: {e}")

        voice_client.play(source, after=after_play)
        
        asyncio.create_task(channel.send(f"Now playing: **{title}**"))
    
    else:
        await voice_client.disconnect()
        SONG_QUEUES[guild_id] = deque()

bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)

