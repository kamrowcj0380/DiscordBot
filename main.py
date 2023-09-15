#Discord bot, purpose TBD
#Authors: Andrew, Connor
# bot.py
import os
import sys

import discord
from dotenv import load_dotenv

#if true/1, then print extra information. This may not have a use in a given moment
VERBOSE = 1

def main():
    
    #load the environment
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')
        
    @client.event
    async def on_message(msg):
        # return if the bot is the author
        if msg.author == client.user:
            return
        
        if VERBOSE:
            print("Author:", msg.author)
            print("Content:", msg.content)
            print()
            print("message itself:", msg)

        if "test" in msg.content.lower():
            await msg.channel.send("Shawn was here")
        else:
            await msg.channel.send("Shawn wasn't here")

    client.run(TOKEN)



if __name__ == "__main__":
    main()