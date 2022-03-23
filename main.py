import asyncio
import datetime
import random

import requests
import discord
from discord.ext import tasks

# Init objects and variables for discord notification bot
client = discord.Client()

# Make sure to have your ids and token accessible in those txt files!
channel_id_for_appointment_notification = int(open('channel_id_for_appointment_notification.txt','r').read()) # Closely watch this channel for results!
channel_id_for_scan_executed_msg = int(open('channel_id_for_scan_executed_msg.txt','r').read()) # This channel should be muted tbh
discord_bot_token = open('discord_bot_token.txt','r').read() # This is your bot token

async def request_all_locations():
    try:
        # Create a new session, because the session cookie will expire after 30 minutes
        session = requests.Session()
        # We have to trigger some things in their backend. Not sure what they are exactly, so just pretend we are a user navigating through frontend
        session.get('https://terminvergabe-ema-zulassung.kiel.de/tevisema/select1?md=4')  # Request "Startseite"
        session.get(
            'https://terminvergabe-ema-zulassung.kiel.de/tevisema/select2?md=4')  # Request "Einwohner-Angelegenheiten"
        session.get(
            "https://terminvergabe-ema-zulassung.kiel.de/tevisema/calendar?mdt=54&cnc-122=1")  # Request "Rathaus - Einwohnerangelegenheiten für eine Person"
        # Those requests should trigger everything needed in backend. So now we can just request through their REST API

        for calendar_week in calc_calendar_weeks_to_request():
            for office_id in office_id_mapping.keys():
                # Building our target URL for the REST API
                target_url = "https://terminvergabe-ema-zulassung.kiel.de/tevisema/caldiv?cal={}&cnc=0&cncdata=&week={}&json=1&offset=1".format(
                    office_id, calendar_week)

                # Get response from the API request
                api_response = session.get(target_url)

                # In valid json array all appointments are stored. Check this for available appointments
                day_counter = 0
                for day in api_response.json()["valid"]:
                    # If the entry is a valid dict there is at least one appointment inside
                    if day and type(day) == dict:
                        # Each timespace is stored as a key-value-pair in the day dict
                        for time in dict(day).keys():
                            # If the value of the key (time) is 1, the appointment is available
                            if dict(day).get(time) == 1:
                                # Build a message and send it through discord bot
                                await send_success_msg(weekday_mapping[day_counter] + ", den " + convert_date_int_to_string(api_response.json()["days"][day_counter]) + " um " + convert_minutes_to_time_string(time) + " Uhr", office_id_mapping[office_id])
                    day_counter += 1
    except Exception as e:
        # This is just triggered if server is not reachable or we are dumb, stuipd or dumb huh
        await send_error_msg()
        print(e)

def calc_calendar_weeks_to_request():
    # We are building a list of the next few calendar week we want to request
    calendar_weeks_list = []

    for x in range(0, 9):
        today = datetime.date.today()
        next_week = today + datetime.timedelta(days=7 * x)

        calendar_year = str(next_week.isocalendar()[0])
        calendar_week = str(next_week.isocalendar()[1])

        # Stupid workaround to use leading zeros
        if len(calendar_week) == 1:
            calendar_week = str(0) + calendar_week

        calendar_weeks_list.append(calendar_year + calendar_week)
    return calendar_weeks_list

def convert_minutes_to_time_string(time):
    # Api will send time as a int in minutes. E.g. 600 = 10am. Whatever... We convert it to a readable time string
    hours = str(int(time) // 60)
    minutes = str(int(time) % 60)
    if len(hours) == 1:
        hours = "0" + hours
    if len(minutes) == 1:
        minutes = "0" + minutes
    time_string = "{}:{}".format(hours, minutes)
    return time_string

def convert_date_int_to_string(date):
    # We just get the day as an int from API.. So lets convert that to a readable date string
    year = str(date)[0:4]
    month = str(date)[4:6]
    day = str(date)[6:8]
    date_string = "{}.{}.{}".format(day, month, year)
    return date_string

async def send_success_msg(date, place):
    # Send a discord message if we found an appointment
    if client.is_ready():
        msg = date + "\nhttps://www.kiel.de/de/politik_verwaltung/service/termine.php#kalender"
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        embed = discord.Embed(title="[{0}] Termin gefunden".format(current_time), color=0x008800)
        embed.add_field(name="Termin gefunden für: " + place, value=msg)
        await client.get_channel(channel_id_for_appointment_notification).send(embed=embed)

async def send_error_msg():
    # Send a discord message if any error occurred while requesting API
    if client.is_ready():
        msg = "Fehler beim Request an die API!"
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        embed = discord.Embed(title="[{0}] Fehler".format(current_time), color=0x7B1818)
        embed.add_field(name="Ein Fehler ist aufgetreten", value=msg)
        await client.get_channel(channel_id_for_appointment_notification).send(embed=embed)


async def send_done_msg():
    # Let user now in a muted other discord channel that the bot is still active
    if client.is_ready():
        msg = "Wenn kein Termin ausgegeben wurde, ist keiner verfügbar."
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        embed = discord.Embed(title="[{0}] Durchgeführt".format(current_time), color=0xFFFF00)
        embed.add_field(name="Eine Suche nach Terminen wurde durchgeführt", value=msg)
        await client.get_channel(channel_id_for_scan_executed_msg).send(embed=embed)


office_id_mapping = {
    97: "Rathaus",
    94: "Hassee",
    96: "Friedrichsort",
    92: "Dietrichsorf",
    93: "Elmschenhagen",
    95: "Mettenhof",
    98: "Suchsdorf"
}

weekday_mapping = {
    0: "Montag",
    1: "Dienstag",
    2: "Mittwoch",
    3: "Donnerstag",
    4: "Freitag",
    5: "Samstag",
    6: "Sonntag"
}

# Start this lovely thing for lazy people as soon as the discord bot is up and connected
print("Waiting for discord client to come up...")
@tasks.loop(count=1)
async def wait_until_ready():
    await client.wait_until_ready()
    print("Discord client ist ready, starting bot! Happy days!")
    while True:
        await request_all_locations()
        await send_done_msg()
        # Just a random intervall between API scans. Pretty unnecessary, because I dont think there is much bot protection neither anyone will care
        await asyncio.sleep(random.randint(15, 60))

wait_until_ready.start()
client.run(discord_bot_token)
