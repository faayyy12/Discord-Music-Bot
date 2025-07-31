## 🎵 Discord Music Bot

A Python-based Discord music bot that supports YouTube streaming, queues, looping, shuffling, and more — all via slash commands.

### 🚀 Features

* 🎶 `/play [query/url]`: Play or queue songs from YouTube
* ⏭️ `/skip`: Skip the current song
* ⏸️ `/pause`: Pause the current song
* ▶️ `/resume`: Resume the current song 
* 🔁 `/loop`: Toggle looping of the queue
* 📃 `/queue`: Show current queue
* 🔀 `/shuffle`: Shuffle the queue
* ⏹️ `/stop`: Clear queue and disconnect

---

### 📦 Technologies Used

* `discord.py` with `app_commands` (slash commands)
* `yt_dlp` for YouTube streaming
* `FFmpeg` for audio handling
* `.env` file for token management
* `asyncio` for async playback

---

### 🛠️ Setup Instructions

#### 1. Clone the repo:

```bash
git clone https://github.com/faayyy12/discord-music-bot.git
cd discord-music-bot
```

#### 2. Install dependencies:

```bash
pip install -r requirements.txt
```

#### 3. Set up `.env`:

Rename the .env.example to `.env` in the root folder and add your bot token:

```
DISCORD_TOKEN=your_actual_discord_token_here
```


#### 4. Add FFmpeg:

* Download FFmpeg and place it in the `bin/ffmpeg` folder
* Update the path in `main.py`:

```python
executable= "path/to/your/ffmpeg/executable"
```

#### 5. Run the bot:

```bash
python main.py
```

---

### 💡 Notes

* This bot uses **slash commands**, so it must sync to the Discord server the first time it's run.
* Make sure to **enable `MESSAGE CONTENT INTENT`** in your bot settings at [Discord Developer Portal](https://discord.com/developers/applications).

---

### 📁 Project Structure

```
.
├── bin/
│   └── ffmpeg/
├── main.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```
