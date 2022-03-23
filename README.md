# ema_checker
Checks for appointments at the Kieler Einwohnermeldeamt.

Its just a small script for those who are too lazy to check for appointments themselfes. (Spoiler: Like me)
This script only makes sense, because all appointments are always booked out.

In general it checks the API of the online booking tool and sends a notification for available appointments through a discord bot, so you are able to book them before anyone else!

Make sure you have those to requirements met (use pip):
  - requests
  - discord

The channel ids and bot token are stored in individual .txt files, because you should not share them. So make sure you create those yourself.

Good luck!

PS: Its developed quick and dirty while watching netflix. Should work smooth nevertheless.

Found appointment will look like this:

<img width="563" alt="grafik" src="https://user-images.githubusercontent.com/99338575/159779691-a68a5a93-72bf-4ed3-acbe-3e9676a43a34.png">
