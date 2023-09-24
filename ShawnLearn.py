import discord
from discord.ext import commands
from typing import Any, List, Tuple
import socket, time, logging, re, string
from discord.flags import Intents

from nltk.tokenize import sent_tokenize
from Database import Database
from Tokenizer import detokenize, tokenize
from Log import Log
Log(__file__)

logger = logging.getLogger(__name__)
TOKEN = 'your token here'
database = Database('ShawnBrain')

class ShawnLearns(discord.Client):

    def __init__(self, *, intents: Intents, **options: Any) -> None:
        self.db = database
        self.key_length = 2
        self.max_sentence_length = 25
        self.min_sentence_length = -1
        self.generator = Generation(self.db)
        super().__init__(intents=intents, **options)

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
    
    #run when a message is sent
    async def on_message(self, msg):

        try:
        # return if the bot is the author
            if msg.author == self.user:
                return
            elif msg.channel.id != 840367930704265231:
                return
            #elif main.check_link(msg.content.lower):
                #return
            elif msg.content.startswith('shawn, '):
                params = tokenize(msg.content[7:])
                new_message, success = self.generator.generate(params)
                await msg.channel.send(new_message)
                #await msg.channel.send(generator.generate())
            else:
                # Try to split up sentences. Requires nltk's 'punkt' resource
                try:
                    sentences = sent_tokenize(msg.content.strip())
                # If 'punkt' is not downloaded, then download it, and retry
                except LookupError:
                    logger.debug("Downloading required punkt resource...")
                    import nltk
                    nltk.download('punkt')
                    logger.debug("Downloaded required punkt resource.")
                    sentences = sent_tokenize(msg.content.strip())

                for sentence in sentences:
                    # Get all seperate words
                    words = tokenize(sentence)
                    # Double spaces will lead to invalid rules. We remove empty words here
                    if "" in words:
                        words = [word for word in words if word]
                        
                    # If the sentence is too short, ignore it and move on to the next.
                    if len(words) <= self.key_length:
                        continue
                    
                    # Add a new starting point for a sentence to the <START>
                    #self.db.add_rule(["<START>"] + [words[x] for x in range(self.key_length)])
                    self.db.add_start_queue([words[x] for x in range(self.key_length)])
                    
                    # Create Key variable which will be used as a key in the Dictionary for the grammar
                    key = list()
                    for word in words:
                        # Set up key for first use
                        if len(key) < self.key_length:
                            key.append(word)
                            continue
                        
                        self.db.add_rule_queue(key + [word])
                        
                        # Remove the first word, and add the current word,
                        # so that the key is correct for the next word.
                        key.pop(0)
                        key.append(word)
                    # Add <END> at the end of the sentence
                    self.db.add_rule_queue(key + ["<END>"])
                    print('successful learn')
        except Exception as e:
            logger.exception(e)


class Generation:

    def __init__(self, db):
        self.db = db
        self.key_length = 2
        self.max_sentence_length = 25
        self.min_sentence_length = -1
        self.sent_separator = " - "
        

    def generate(self, params: List[str] = None) -> "Tuple[str, bool]":
        
        """Given an input sentence, generate the remainder of the sentence using the learned data.

        Args:
            params (List[str]): A list of words to use as an input to use as the start of generating.
        
        Returns:
            Tuple[str, bool]: A tuple of a sentence as the first value, and a boolean indicating
                whether the generation succeeded as the second value.
        """
        if params is None:
            params = []

        # List of sentences that will be generated. In some cases, multiple sentences will be generated,
        # e.g. when the first sentence has less words than self.min_sentence_length.
        sentences = [[]]

        # Check for commands or recursion, eg: !generate !generate
        if len(params) > 0:
            if False:#self.check_if_other_command(params[0]):
                return "You can't make me do commands, you madman!", False

        # Get the starting key and starting sentence.
        # If there is more than 1 param, get the last 2 as the key.
        # Note that self.key_length is fixed to 2 in this implementation
        if len(params) > 1:
            key = params[-self.key_length:]
            # Copy the entire params for the sentence
            sentences[0] = params.copy()

        elif len(params) == 1:
            # First we try to find if this word was once used as the first word in a sentence:
            key = self.db.get_next_single_start(params[0])
            if key == None:
                # If this failed, we try to find the next word in the grammar as a whole
                key = self.db.get_next_single_initial(0, params[0])
                if key == None:
                    # Return a message that this word hasn't been learned yet
                    return f"I haven't extracted \"{params[0]}\" from chat yet.", False
            # Copy this for the sentence
            sentences[0] = key.copy()

        else: # if there are no params
            # Get starting key
            key = self.db.get_start()
            if key:
                # Copy this for the sentence
                sentences[0] = key.copy()
            else:
                # If nothing's ever been said
                return "There is not enough learned information yet.", False
        
        # Counter to prevent infinite loops (i.e. constantly generating <END> while below the 
        # minimum number of words to generate)
        i = 0
        while self.sentence_length(sentences) < self.max_sentence_length and i < self.max_sentence_length * 2:
            # Use key to get next word
            if i == 0:
                # Prevent fetching <END> on the first word
                word = self.db.get_next_initial(i, key)
            else:
                word = self.db.get_next(i, key)

            i += 1

            if word == "<END>" or word == None:
                # Break, unless we are before the min_sentence_length
                if i < self.min_sentence_length:
                    key = self.db.get_start()
                    # Ensure that the key can be generated. Otherwise we still stop.
                    if key:
                        # Start a new sentence
                        sentences.append([])
                        for entry in key:
                            sentences[-1].append(entry)
                        continue
                break

            # Otherwise add the word
            sentences[-1].append(word)
            
            # Shift the key so on the next iteration it gets the next item
            key.pop(0)
            key.append(word)
        
        # If there were params, but the sentence resulting is identical to the params
        # Then the params did not result in an actual sentence
        # If so, restart without params
        if len(params) > 0 and params == sentences[0]:
            return "I haven't learned what to do with \"" + detokenize(params[-self.key_length:]) + "\" yet.", False

        return self.sent_separator.join(detokenize(sentence) for sentence in sentences), True
    def sentence_length(self, sentences: List[List[str]]) -> int:
            """Given a list of tokens representing a sentence, return the number of words in there.

            Args:
                sentences (List[List[str]]): List of lists of tokens that make up a sentence,
                    where a token is a word or punctuation. For example:
                    [['Hello', ',', 'you', "'re", 'Tom', '!'], ['Yes', ',', 'I', 'am', '.']]
                    This would return 6.

            Returns:
                int: The number of words in the sentence.
            """
            count = 0
            for sentence in sentences:
                for token in sentence:
                    if token not in string.punctuation and token[0] != "'":
                        count += 1
            return count

    def extract_modifiers(self, emotes: str) -> List[str]:
        """Extract emote modifiers from emotes, such as the the horizontal flip.

        Args:
            emotes (str): String containing all emotes used in the message.
        
        Returns:
            List[str]: List of strings that show modifiers, such as "_HZ" for horizontal flip.
        """
        output = []
        try:
            while emotes:
                u_index = emotes.index("_")
                c_index = emotes.index(":", u_index)
                output.append(emotes[u_index:c_index])
                emotes = emotes[c_index:]
        except ValueError:
            pass
        return output

def check_link(self, message: str) -> bool:
        """True if `message` contains a link.

        Args:
            message (str): The message to check for a link.

        Returns:
            bool: True if the message contains a link.
        """
        return self.link_regex.search(message)

def main():
    #set the intents of the bot to default
    intents = discord.Intents.default()
    #allow the bot to see message content in 'intents'
    intents.message_content = True
    #create the bot client
    client = ShawnLearns(intents = intents)
    #run the client using the loaded token
    client.run(TOKEN)





if __name__ == "__main__":
    main()