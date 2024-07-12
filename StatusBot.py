import discord
from discord.ext import tasks
import requests
from bs4 import BeautifulSoup

# Your Discord Bot Token
TOKEN = ''

VOICE_CHANNEL_ID = 1234  # the voice channel where you want the status to show.
OFFLINE_ALERT_CHANNEL_ID = 1234  # the announcements channel where you want automated alerts to be sent of downtime.

intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)
previous_status = None

# Setup for https://betterstack.com, Don't change this unless Betterstack does.
def check_status(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    status_div = soup.find("div",class_="section-status-badge p-1 pr-2 rounded-full bg-statuspage-neutral-60 dark:bg-statuspage-neutral-600 font-medium text-statuspage-neutral-800 dark:text-white transition whitespace-nowrap")
    if status_div:
        status_text = status_div.get_text(strip=True)
        return status_text.strip()
    else:
        return "Fatal Error"

# Checks every 3 minutes, anything shorter and Discord will time you out.
@tasks.loop(minutes=3)
async def periodic_status_check():
    global previous_status
    # Website you want to check here
    status = check_status("https://YourWebsite")
    if status != previous_status:
        await update_voice_channel_name(status)
        previous_status = status


@periodic_status_check.before_loop
async def before_periodic_status_check():
    await client.wait_until_ready()


async def update_voice_channel_name(status):
    voice_channel = client.get_channel(VOICE_CHANNEL_ID)
    alert_channel = client.get_channel(OFFLINE_ALERT_CHANNEL_ID)

    if voice_channel is not None:
        if status == "Operational":
            channel_name = "Online"
            if previous_status == "Downtime" and alert_channel is not None:
                await alert_channel.send("All services are online. Thank you for your patience. If you encounter any issues, please create a ticket.")
        elif status == "Downtime":
            channel_name = "Offline"
            if previous_status == "Operational" and alert_channel is not None:
                await alert_channel.send("Some services are offline. We're working on it and will update you soon. Thank you for your patience.")

        await voice_channel.edit(name=channel_name)
        print(f"Voice channel name updated to: {channel_name}")
    else:
        print("Voice channel not found.")


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    # Read https://stackoverflow.com/questions/59126137/how-to-change-activity-of-a-discord-py-bot
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=""))
    periodic_status_check.start()


client.run(TOKEN)
