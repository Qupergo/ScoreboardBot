import aiohttp
import os
import json
from discord import Activity, ActivityType
from discord.ext.commands import Bot
from keep_alive import keep_alive

DISCORD_MESSAGE_PREFIX = ["s!", "<@641229153433288724>", "s! ", "<@641229153433288724> "]

client = Bot(command_prefix=DISCORD_MESSAGE_PREFIX)

@client.event
async def on_ready():
  print("Im in")
  print(client.user)
  guilds = client.guilds
  iteration = 0
  for guild in guilds:
    print(guild.name)
    iteration += 1
    #Keep from printing too many servers
    if iteration > 100:
      break
  await client.change_presence(activity=Activity(name=f" scoreboards on {len(guilds)} servers", type=ActivityType.watching))

  with open('scoreboards.txt', "r") as scoreboards_orig:
    scoreboards = json.load(scoreboards_orig)
    for guild in guilds:
      if str(guild.id) not in scoreboards.keys():
        scoreboards[guild.id] = {}

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig)


@client.event
async def on_guild_join(guild):
    await client.change_presence(activity=Activity(name=f" scoreboards on {len(client.guilds)} servers", type=ActivityType.watching))

    #Add server id to scoreboards
    with open('scoreboards.txt', "r") as scoreboards_orig:
      scoreboards = json.load(scoreboards_orig)
      for guild in client.guilds:
        if str(guild.id) not in scoreboards.keys():
          scoreboards[guild.id] = {}
      
    with open('scoreboards.txt', "w") as scoreboards_orig:
      json.dump(scoreboards, scoreboards_orig)


#invite
@client.command(name='invite',
                description="Gives you the link to add this bot to a server.",
                brief="Gives you the link to this bot.",
                aliases=['link'])
async def link(ctx):
  await ctx.send('Here you go!')
  await ctx.send('<https://discordapp.com/oauth2/authorize?&client_id=641229153433288724&scope=bot&permissions=0>')


#create
@client.command(name='create',
                description="Creates a scoreboard.\n\nCorrect usage is s!create [scoreboard]",
                brief="Creates a scoreboard.",
                aliases=[' create'])
async def create(ctx, *args):
  correct_usage = "Correct usage is s!create [scoreboard]"
  try:
    scoreboard_name = args[0]
  except IndexError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return

  with open('scoreboards.txt', "r") as scoreboards_orig:
    scoreboards = json.load(scoreboards_orig)
    cur_scoreboards = scoreboards[str(ctx.message.guild.id)]
    cur_scoreboards[scoreboard_name] = {'name':scoreboard_name, 'guild_id':str(ctx.message.guild.id), 'participants_scores':{}}
    scoreboards[str(ctx.message.guild.id)] = cur_scoreboards

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig)
  await ctx.send('Created a scoreboard with the name ' + scoreboard_name) 


#addMember
@client.command(name='addMember',
                description="Adds someone to a specified scoreboard.\n\nCorrect usage is s!addMember [member] [scoreboard]",
                brief="Adds someone to scoreboard.",
                aliases=['add_m', 'addM', 'addmember'])
async def addMember(ctx, *args):
  correct_usage = "Correct usage is s!addMember [member] [scoreboard]"
  try:
    member, scoreboard_name = args
  except ValueError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return

  with open('scoreboards.txt', "r") as scoreboards_orig:

    scoreboards = json.load(scoreboards_orig)
    try:
      scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][member] = 0
    except KeyError:
        await ctx.send(f"The scoreboard {scoreboard_name} does not exist")
        return

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig)
  await ctx.send(f'Added {member} to {scoreboard_name}')


#addPoints
@client.command(name='addPoints',
                description="Adds points to someone on a specified scoreboard.\n\nCorrect usage is s!addPoints [member] [scoreboard] [points]",
                brief="Adds points to someone.",
                aliases=['add_p', 'addP', "addpoints"])
async def addPoints(ctx, *args):

  correct_usage = "Correct usage is s!addMember [member] [scoreboard] [points]"
  try:
    member, scoreboard_name, points = args
  except ValueError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return
    
  with open('scoreboards.txt', "r") as scoreboards_orig:
    scoreboards = json.load(scoreboards_orig)
    
    try:
      scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][member] += int(points)
    except KeyError:
      await ctx.send(f"There does not seem to be a {member} in {scoreboard_name}.\n" + correct_usage)
      return

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig)

  if points == "1":
    await ctx.send(f'Added 1 point to {member}')
  else:
    await ctx.send(f'Added {points} points to {member}')

#removeMember
@client.command(name='removeMember',
                description="Removes someone from a specified scoreboard.\n\nCorrect usage is s!removeMember [member] [scoreboard]",
                brief="Removes someone from scoreboard.",
                aliases=['rm_m', 'rmM', "rmMember", "rmMem", "removemember"])
async def removeMember(ctx, *args):

  correct_usage = "Correct usage is s!removeMember [member] [scoreboard]"
  try:
    member, scoreboard_name = args
  except ValueError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return

  with open('scoreboards.txt', "r") as scoreboards_orig:
    scoreboards = json.load(scoreboards_orig)
    try:
      scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"].pop(member)
    except KeyError:
      await ctx.send(f"There does not seem to be a {member} in {scoreboard_name}.\n{correct_usage}")
      return
  
    with open('scoreboards.txt', "w") as scoreboards_orig:
      json.dump(scoreboards, scoreboards_orig)

    await ctx.send(f'Succesfully removed {member} from {scoreboard_name}.')


#removePoints
@client.command(name='removePoints',
                description="Removes points from someone on a specified scoreboard.\n\nCorrect usage is s!removePoints [member] [scoreboard] [points]",
                brief="Removes points from someone.",
                aliases=['remove_p', 'removeP', "rm_p", "rmP", "removepoints"])
async def removePoints(ctx, *args):
  correct_usage = "Correct usage is s!removePoints [member] [scoreboard] [points]"
  try:
    member, scoreboard_name, points = args
  except ValueError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return

  with open('scoreboards.txt', "r") as scoreboards_orig:
    scoreboards = json.load(scoreboards_orig)
    try:
      scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][member] -= int(points)
    
    except KeyError:
      await ctx.send(f"{member} does not seem to exist in {scoreboard_name}.\n{correct_usage}")

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig)

  if points == "1":
    await ctx.send(f'Removed 1 point from {member}')
  else:
    await ctx.send(f'Removed {points} points from {member}')

#show
@client.command(name='show',
                description="Shows a scoreboard.\n\nCorrect usage is s!show [scoreboard]",
                brief="Shows a scoreboard.",
                aliases=['Show'])
async def show(ctx, *args):
  correct_usage = "Correct usage is s!show [scoreboard]"

  try:
    scoreboard_name = args[0]
  except ValueError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return
    
  with open('scoreboards.txt', "r") as scoreboards_orig:
    scoreboards = json.load(scoreboards_orig)

    members = []
    member_order = []
    try:
      #Make a sorted list of the members by their points
      for key, value in scoreboards[str(ctx.message.guild.id)][scoreboard_name]['participants_scores'].items():
        member_order.append([key, value])
      member_order.sort(key=lambda x:int(x[1]), reverse=True)
      
      #Make string look nicer before sending
      for key, value in member_order:
        members.append(f"{key}\t{':'}\t{value}")
      nl = "\n"
      scoreboard_visual = f"__{scoreboard_name}__\n\n{nl.join(members)}"
      await ctx.send(scoreboard_visual)
    
    except KeyError:
      await ctx.send("That scoreboard does not seem to exist on this server.\n" + correct_usage)

@client.command(name='resetScoreboard',
                description="Resets all scores on a specified scoreboard.\n\nCorrect usage is s!resetScores [scoreboard]",
                brief="Resets all scores on a specified scoreboard",
                aliases=['reset_scores', 'resetscores', "ResetScores", "resetScores", 'reset_scoreboard', 'resetscoreboard', "ResetScoreboard"])
async def resetScoreboard(ctx, *args):
  correct_usage = "Correct usage is s!resetScores [scoreboard]"
  try:
    scoreboard_name = args[0]
  except ValueError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return

  with open('scoreboards.txt', "r") as scoreboards_orig:

    # Load scoreboard
    scoreboards = json.load(scoreboards_orig)
    scoreboard = []
    try:
      # Find scoreboard
      scoreboard = scoreboards[str(ctx.message.guild.id)][scoreboard_name]
    except KeyError:
      # If the key can't be found
      await ctx.send("That scoreboard does not seem to exist.")
      return

    for key in scoreboard["participants_scores"].keys():
      scoreboard["participants_scores"][key] = 0

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig)

  await ctx.send(f"Reset all values in {scoreboard_name} to 0.")

keep_alive()
token = os.environ.get("DISCORD_BOT_SECRET")
client.run(token)