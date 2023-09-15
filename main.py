#Discord bot, purpose TBD
#Authors: Andrew, Connor
# bot.py
import os
import sys

import discord
from dotenv import load_dotenv



def main():
    print("Hello World!")

    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')


    client.run(TOKEN)



if __name__ == "__main__":
    main()