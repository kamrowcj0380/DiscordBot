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
    
    #load the environment from file
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    #set the intents of the bot to default
    intents = discord.Intents.default()
    #allow the bot to see message content in 'intents'
    intents.message_content = True
    #create the bot client
    client = discord.Client(intents=intents)

    #print confirmation when bot connects
    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord!')
    
    #run when a message is sent
    @client.event
    async def on_message(msg):
        # return if the bot is the author
        if msg.author == client.user:
            return
        
        #if verbose, show author and information
        if VERBOSE:
            print("Author:", msg.author)
            print("Content:", msg.content)
            print()

        #simple response testing
        if "test" in msg.content.lower():
            await msg.channel.send("Shawn was here")
        else:
            await msg.channel.send("Where is Shawn...")

    #run the client using the loaded token
    client.run(TOKEN)



if __name__ == "__main__":
    main()