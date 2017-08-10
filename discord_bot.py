'''
discord_bot.py

jordan sybesma, 2017, using Rapptz's discord.py library (https://github.com/Rapptz/discord.py)

A simple discord bot that scans incoming messages for keywords corresponding to commands.

NOTE: whitespace in this document is composed of space characters. If you prefer to use
tabs and modify this document, remember to replace the existing whitespace!

'''

import discord # Can be obtained via pip, using "pip install discord"
import asyncio # Automatically installed through pip when installing discord
import sys
import random
import socket

# Identity Variables

client                = discord.Client()
loggingChannels       = {} # Store the log output channel of all connected servers
politeMode            = {} # If enabled, requires a 'please' in your requests.
BOT_NAME              = 'helper bot' # Saves the reference for the bot.
BOT_TOKEN             = "PUT YOUR TOKEN HERE" # Saves the token, effectively the password, of the discord bot.

# Utility Variables

punctuation           = '!,;.?)({}[]" '
compliment_intros     = ["Such a {0} {1}! c: <3 c:","I just want you to know that you're so {0}!  You have the best {1} <3","I'm always excited to see your {0} {1}","You're such a {0} person!  Seeing your {1} brightens up my day.","I may just be a silly robot, but even I can appreciate your {0} {1}!"]
compliment_adjectives = ["gorgeous","lovely","beautiful","amazing","wonderful","fantastic","graceful","stunning","pretty","enchanting"]
compliment_nouns      = ["smile","face","hair","look","sense of humor"]
eightball_responses   = ["It is certain","It is decidedly so","Without a doubt","Yes definitely","You may rely on it","As I see it, yes","Most likely","Outlook good","Yes","Signs point to yes","The Future is hazy, try again"," Ask again later","You don't want to know","I'm sorry, I can't tell you that","Concentrate harder and try again","Don't count on it","Leaning towards 'no'","Doubtful","Outlook not good.","Negative","Heck no"]
lockSocket            = None # Declare the lock socket as a global variable to avoid garbage collection until the program ends

# Utility Functions

def containsPhrase(content, phrase):
    content = content.lower()
    phrase = phrase.lower()
    location = content.find(phrase)
    try:
        if location != -1 and (location == 0 or content[location-1] in punctuation) and content[location+len(phrase)] in punctuation:
            return True

        return False
    except IndexError:
        return True # We found the phrase at the very end of the content, meaning that there can't be any characters after it.

def writeServerTableToFile(fileName, dictionary):
    file = open(fileName,'w')
    for key, value in dictionary.items():
        file.write(key.name + ',' + value.name + '\n')

    file.close()

def importServerTableFromFile(filename, dictionary):
    try:
        file = open(filename,'r')
        lines = file.readlines()
        for line in lines:
            k,v = line.split(',')
            serverFound = False
            channelFound = False
            # Search through servers to find the right one
            for server in client.servers:
                if server.name == k:
                    serverFound = True
                    for channel in server.channels:
                        if channel.name == v:
                            channelFound = False
                            dictionary[server] = channel

            if not (serverFound or channelFound):
                print("Failed to import data for server {0}: channel not found".format(k))
    except OSError:
        print("Failed to import data: datafile not found!")

def get_lock(process_name):
    global lockSocket # Use the global variable to keep our reference open.
    lockSocket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    try:
        lockSocket.bind('\0' + process_name)
        print('This is the only instance of this script.')
    except socket.error:
        print('Another instance of the script exists, exiting.')
        sys.exit()

# Events

'''

Fires when the client logs into all servers.  Imports a dictionary for 
which channel in a server is used for printing logs, seaches for log channels
in servers that failed to import, prints a message upon completion.

'''
@client.event
async def on_ready(): 
    importServerTableFromFile('LoggingChannels.txt',loggingChannels)
    for server in client.servers:
        politeMode[server] = False
        try:
            test = loggingChannels[server]
        except KeyError:
            logChannel = None
            for channel in server.channels:
                if "log" in channel.name:
                    logChannel = channel

            if logChannel == None:
                loggingChannels[server] = server.default_channel
            else:
                loggingChannels[server] = logChannel

        await client.send_message(loggingChannels[server],"{0} v.1.1 back online".format(BOT_NAME))

    print('{0} online. Logged in as {1}{2}'.format(BOT_NAME,client.user.name,client.user.id))

'''

Manages all message events - ie someone submitting a command for our bot in a channel.  
Half of these are novelty commands, like forcing users to ask the bot nicely before it 
reads commands, or asking for a dice roll.  The remaining half are utility commands, like
banning or kicking users from a given server, and require that the requesting user is a
server administrator.

'''
@client.event
async def on_message(message):
    perms = message.author.permissions_in(message.channel)
    myperms = message.server.me.permissions_in(message.channel)

    # Check if we should care about the message

    if not containsPhrase(message.content, BOT_NAME):
        return # No reason to keep reading this if it's not addressed to the bot.

    if politeMode[message.server] == True and not (containsPhrase(message.content, 'please') or containsPhrase(message.content, 'pls') or containsPhrase(message.content, 'plz')):
        await client.send_message(message.channel, "What's the magic word, " + message.author.display_name + "?")
        return # Mind your manners!

    if containsPhrase(message.content, 'commands'):
        if perms.administrator:
            embed = discord.Embed(title="{0} Commands".format(BOT_NAME), description="I don't take in specific commands, but I listen for keywords.  Let me tell you what I look for:", color=0x10e440)
            embed.add_field(name = "Compliment", value = "Tag a user, and I'll compliment them!  Happy to spread some positivity! <3", inline = False)
            embed.add_field(name = "Polite", value = "Toggles Polite Mode.  Don't forget the magic word!", inline = False)
            embed.add_field(name = "Future | 8ball", value = "Ask me about the future! I'll use my divine soothsaying powers and also the magic eightball I found in the attic to respond.", inline = False)
            embed.add_field(name = "Roll d20 / die", value = "Ask me to roll a d20 or d6!", inline = False)
            embed.add_field(name = "Flip Coin", value = "Channel your inner Harvey Dent and get some 50/50 odds.", inline = False)
            embed.add_field(name = "Shut Down", value = "Shuts down {0}.  Please don't use unless necessary, since I'll have to be restarted from a command line!".format(BOT_NAME), inline = False)
            embed.add_field(name = "Set Log Channel", value = "Sets the current channel as the log channel for a given server.", inline = False)
            embed.add_field(name = "Kick", value = "Kicks any mentioned players from the server.", inline = False)
            embed.add_field(name = "Ban", value = "Bans any mentioned players from the server.", inline = False)
            await client.send_message(message.channel, embed=embed)

        else: # Non-Administrators don't need to know about administrator commands.
            embed = discord.Embed(title="{0} Commands".format(BOT_NAME), description="I don't take in specific commands, but I listen for keywords.  Let me tell you what I look for:", color=0x10e440)
            embed.add_field(name = "Compliment", value = "Tag a user, and I'll compliment them!  Happy to spread some positivity! <3", inline = False)
            embed.add_field(name = "Polite", value = "Toggles Polite Mode.  Don't forget the magic word!", inline = False)
            embed.add_field(name = "Future | 8ball", value = "Ask me about the future! I'll use my divine soothsaying powers and also the magic eightball I found in the attic to respond.", inline = False)
            embed.add_field(name = "Roll d20 / die", value = "Ask me to roll a d20 or d6!", inline = False)
            embed.add_field(name = "Flip Coin", value = "Channel your inner Harvey Dent and get some 50/50 odds.", inline = False)
            await client.send_message(message.channel, embed=embed)

    # Public / Novelty Commands

    elif containsPhrase(message.content, "compliment"):
        if len(message.mentions) > 0:
            for user in message.mentions:
                phrase = compliment_intros[random.randint(0,len(compliment_intros)-1)].format(compliment_adjectives[random.randint(0,len(compliment_adjectives)-1)], compliment_nouns[random.randint(0,len(compliment_nouns)-1)])
                await client.send_message(message.channel, user.display_name + ", " + phrase)

    elif containsPhrase(message.content, "roll"):
        if containsPhrase(message.content, "d20"):
            await client.send_message(message.channel, "Rolling d20 - it's a " + str(random.randint(1,20)))
        elif containsPhrase(message.content,"die"):
            await client.send_message(message.channel, "Rolling die - it's a " + str(random.randint(1,6)))

    elif containsPhrase(message.content, "flip") and containsPhrase(message.content, "coin"):
        num = random.randint(1,100)
        if num > 50:
            await client.send_message(message.channel, "Flipping a coin - It's Heads!")
        else:
            await client.send_message(message.channel, "Flipping a coin - It's Tails!")

    elif containsPhrase(message.content, "future") or containsPhrase(message.content,"eightball") or containsPhrase(message.content,"8ball"):
        await client.send_message(message.channel, message.author.display_name + ", the magic eight ball says: " + eightball_responses[random.randint(1,len(eightball_responses))])

    # Administrator Commands

    elif perms.administrator 
        if containsPhrase(message.content, 'shut') and containsPhrase(message.content, 'down'):
            await client.send_message(message.channel, 'Powering down.  Good night everyone!')
            writeServerTableToFile('LoggingChannels.txt',loggingChannels)
            await client.close()
            sys.exit(0)

        elif containsPhrase(message.content, 'polite'): # Still a novelty command, but not everyone needs to toggle it.
            politeMode[message.server] = not politeMode[message.server]
            if politeMode[message.server]:
                await client.send_message(message.channel, 'Manners mode enabled.  Watch your language!')
            else:
                await client.send_message(message.channel, "Manners mode disabled.")

        elif perms.administrator and containsPhrase(message.content, 'set') and containsPhrase(message.content, 'log') and containsPhrase(message.content, 'channel'):
            loggingChannels[message.server] = message.channel
            writeServerTableToFile('LoggingChannels.txt',loggingChannels) # Save the updated logging channels in case of a failure.
            await client.send_message(message.channel,"Setting this channel as the primary log channel for the server.")

        elif perms.administrator and containsPhrase(message.content, 'ban'):
            if myperms.ban_members:
                if len(message.mentions) > 0:
                    for user in message.mentions:
                        await client.send_message(message.channel, "Banning " + user.display_name + ".")
                        await client.ban(user,0)
            else:
                client.send_message(message.channel, "I'm sorry, " + message.author.display_name + ", I'm afraid I can't do that.")


        elif perms.administrator and containsPhrase(message.content, 'kick'):
            if myperms.kick_members:
                if len(message.mentions) > 0:
                    for user in message.mentions:
                        await client.send_message(message.channel, "Kicking " + user.display_name +".")
                        await client.kick(user)

    else: # No commands found, notify the requesting user
        client.send_message(message.channel, "I'm sorry, " + message.author.display_name + ", I'm afraid I can't do that.")

'''

Detect message edits in the server, post the log to the designated logging channel

'''

@client.event
async def on_message_edit(before, after):
    if before.content == after.content:
        return # avoid equivalent edits.
    embed = discord.Embed(title="Message Edited", color=0x7ba9e1)
    embed.add_field(name = "Author", value = after.author, inline = True)
    embed.add_field(name = "Channel", value = after.channel.name, inline = True)
    embed.add_field(name = "Original Text", value = before.content, inline = False)
    embed.add_field(name = "Edited Text", value = after.content, inline = False)
    await client.send_message(loggingChannels[before.server], embed=embed)

'''

Detect deleted messages in the server, post the log to the designated logging channel

'''

@client.event
async def on_message_delete(message):
    embed = discord.Embed(title="Message Deleted", color=0xf3012c)
    embed.add_field(name = "Author", value= message.author, inline = True)
    embed.add_field(name = "Channel", value = message.channel.name, inline = True)
    embed.add_field(name = "Text", value = message.content, inline = False)
    await client.send_message(loggingChannels[message.server], embed = embed)

'''

main() function is designed to be executed by an automated task.  Checks for an instance of this code running
by attempting to open a socket, then if successful connects to the discord API and initializes the discord library
event loop.

'''

def main():
    # Make sure we don't have any other instances running.
    get_lock('jordan_sybesma.discordbot')
    global client
    client.run(BOT_TOKEN) 
    print(lockSocket)

if __name__ == "__main__":
    main()