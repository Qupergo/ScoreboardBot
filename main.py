import os
import json
import discord
from discord import Activity, ActivityType, Embed
from discord.ext.commands import Bot

from keep_alive import keep_alive
import dbl
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

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
    json.dump(scoreboards, scoreboards_orig, indent=4)




def check_permissions(ctx, *args):
  permissions = ctx.message.channel.permissions_for(ctx.message.author)
  print(permissions)
  print(args)
  if permissions.administrator or permissions.ban_members or permissions.manage_servers or permissions.manage_guild:
    return True
  
  return False

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
      json.dump(scoreboards, scoreboards_orig, indent=4)




#invite
@client.command(name='invite',
                description="Gives you the link to add this bot to a server.",
                brief="Gives you the link to this bot.",
                aliases=['link'])
async def invite(ctx):
  await ctx.send('Here you go!')
  await ctx.send('<https://discordapp.com/oauth2/authorize?&client_id=641229153433288724&scope=bot&permissions=0>')

#create
@client.command(name='create',
                description="Creates a scoreboard.\n\nCorrect usage is s!create [scoreboard]",
                brief="Creates a scoreboard.",
                aliases=[' create'])
@commands.check(check_permissions)
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
    json.dump(scoreboards, scoreboards_orig, indent=4)
  await ctx.send('Created a scoreboard with the name ' + scoreboard_name)

#Member
@client.command(name='member',
                description="Adds or removes members in a scoreboard\n\nCorrect usage is s!member (add/remove) [member/role] [scoreboard_name]",
                brief="Interacts with the members in a scoreboard.",
                aliases=['Member', 'mem', 'Mem'])
async def member(ctx, *args):
  correct_usage = "Correct usage is s!member (add/remove) [member/role] [scoreboard_name]"
  try:
    option, member, scoreboard_name = args
  except ValueError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return

  with open('scoreboards.txt', "r") as scoreboards_orig:

    scoreboards = json.load(scoreboards_orig)
    roles = ctx.message.role_mentions
    members_to_interact = []

    try:
      # If trying to add with role
      if len(roles) > 0:
        role = roles[0]
        for cur_member in ctx.message.guild.members:
          for cur_role in cur_member.roles:
            if role == cur_role:
              members_to_interact.append(cur_member)
              break

      # Else only a single member should be interacted with
      else:
        members_to_interact = [member]

      for cur_member in members_to_interact:
      
        #For some reason, discord adds ! to mentions sometimes
        #This will then count as different people, even though they mention the same person
        #So just default it to <@user_id> instead of <@!user_id>
        if isinstance(cur_member, discord.member.Member):
          cur_member = "<@" + cur_member.id + ">"

        if option.lower() == "add":
          # If the member is already in the scoreboard, don't add them again
          if cur_member in scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"].keys():
            continue
          scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][cur_member] = 0

        elif option.lower() == "remove":
          del scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][cur_member]
        else:
          await ctx.send("Something went wrong!\n" + correct_usage)
    except KeyError:
        await ctx.send(f"The scoreboard {scoreboard_name} does not exist.")
        return

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig, indent=4)

  if option.lower() == "remove":
    await ctx.send(f'removed {member} from {scoreboard_name}')

  elif option.lower() == "add":
    await ctx.send(f"added {member} to {scoreboard_name}")


@client.command(name='test',
                description="test",
                brief="test",
                aliases=['t'])
async def test(ctx, *args):
    for cur_member in ctx.message.guild.members:
      if isinstance(cur_member, discord.member.Member):
        print(cur_member.id)


@client.command(name='points',
                description="Manages someones points on a specified scoreboard. You can add points to all members with a certain role as well\n\nCorrect usage is s!points (add/remove/set) [member/role] [scoreboard_name] [points]",
                brief="Adds points to someone.",
                aliases=['point', 'p'])
async def points(ctx, *args):
  correct_usage = 'Correct usage is s!points (add/remove/set) [member/role] [scoreboard_name] [points]'

  #Get user input
  try:
    option, member, scoreboard_name, points = args
  except ValueError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return
  
  #Option should be either add, remove or set
  #Otherwise throw error
  if option not in ["add", "remove", "set"]:
    await ctx.send("Incorrect option for s!points, " + option + "\nPlease use either add, remove or set\n" + correct_usage)
    return
  
  with open('scoreboards.txt', "r") as scoreboards_orig:

    scoreboards = json.load(scoreboards_orig)
    allScoreboardMembers = scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"].keys()

    #Check if a role has been mentioned
    roles = ctx.message.role_mentions
    membersAffected = []

    
    if len(roles) > 0:
      #Add all members with the role to membersAffected
      role = roles[0]
      for cur_member in allScoreboardMembers:
        print(cur_member)
        for cur_role in cur_member.roles:
          if role == cur_role:
            membersAffected.append(cur_member)
            break
      





#addPoints
@client.command(name='addPoints',
                description="Adds points to someone on a specified scoreboard.\n\nCorrect usage is s!addPoints [member] [scoreboard] [points]",
                brief="Adds points to someone.",
                aliases=['add_p', 'addP', "addpoints", 'addp'])
async def addPoints(ctx, *args):

  correct_usage = "Correct usage is s!addPoints [member] [scoreboard] [points]"
  try:
    member, scoreboard_name, points = args
  except ValueError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return

  with open('scoreboards.txt', "r") as scoreboards_orig:
    scoreboards = json.load(scoreboards_orig)

    try:
      scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][member] += int(points)
      new_score = scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][member]
    except KeyError:
      await ctx.send(f"There does not seem to be a {member} in {scoreboard_name}.\n" + correct_usage)
      return

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig, indent=4)

  if points == "1":
    await ctx.send(f'Added 1 point to {member}, new score is {new_score}.')
  else:
    await ctx.send(f'Added {points} points to {member}, new score is {new_score}.')


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
      new_score = scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][member]
    except KeyError:
      await ctx.send(f"{member} does not seem to exist in {scoreboard_name}.\n{correct_usage}")

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig, indent=4)

  if points == "1":
    await ctx.send(f'Removed 1 point from {member}, new score is {new_score}.')
  else:
    await ctx.send(f'Removed {points} points from {member}, new score is {new_score}.')

#show
@client.command(name='show',
                description="Shows a scoreboard.\n\nCorrect usage is s!show [scoreboard] <page_number>",
                brief="Shows a scoreboard.",
                aliases=['Show'])
async def show(ctx, *args):
  correct_usage = "Correct usage is s!show [scoreboard] <page_number>"
  page_number = 1
  try:
    scoreboard_name = args[0]
  except:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return

  if len(args) > 1:
    try:
      page_number = int(args[1])
    except:
      pass

  with open('scoreboards.txt', "r") as scoreboards_orig:
    scoreboards = json.load(scoreboards_orig)

    member_order = []
    try:
      #Make a sorted list of the members by their points
      for key, value in scoreboards[str(ctx.message.guild.id)][scoreboard_name]['participants_scores'].items():
        member_order.append([key, value])
      member_order.sort(key=lambda x:int(x[1]), reverse=True)

      iteration = 0
      pages = []
      members_per_page = 20
      current_page = []

      for key, value in member_order:
        current_page.append(f"{key}\t{':'}\t{value}")
        iteration += 1

        if iteration == members_per_page:
          pages.append(current_page.copy())
          current_page = []
          iteration = 0

      if iteration > 0:
        pages.append(current_page)

      if (page_number-1) > len(pages) or (page_number - 1) < 0:
        page_number = len(pages)

      if len(pages) == 0:
        await ctx.send(f"Unfortunately, **{scoreboard_name}** is empty, there is nothing to show.")
        return

      embed = Embed(title=f"**{scoreboard_name}**", colour=discord.Colour(900))

      embed.add_field(name="Members", value="\t\n".join(pages[page_number-1]))
      embed.add_field(name="Page", value=f"{page_number}/{len(pages)}")

      try:
        await ctx.send(embed=embed)
      except:
        await ctx.send("I don't have permissions for that.")

    except KeyError:
      await ctx.send("That scoreboard does not seem to exist on this server.\n" + correct_usage)

#ResetScoreboard
@client.command(name='resetScoreboard',
                description="Resets all scores on a specified scoreboard.\n\nCorrect usage is s!resetScores [scoreboard]",
                brief="Resets all scores on a specified scoreboard",
                aliases=['reset_scores', 'resetscores', "ResetScores", "resetScores", 'reset_scoreboard', 'resetscoreboard', "ResetScoreboard", "wipe", "Wipe"])
async def resetScoreboard(ctx, *args):
  correct_usage = "Correct usage is s!resetScores [scoreboard]"
  try:
    scoreboard_name = args[0]
  except IndexError:
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
    json.dump(scoreboards, scoreboards_orig, indent=4)

  await ctx.send(f"Reset all values in {scoreboard_name} to 0.")


@client.command(name='list',
                description="Lists all scoreboards.\n\nCorrect usage is s!list",
                brief="Lists all scoreboards.",
                aliases=[])
@commands.check(check_permissions)
async def list(ctx, *args):
  correct_usage = "Correct usage is s!list"

  with open('scoreboards.txt', "r") as scoreboards_orig:
    scoreboards = json.load(scoreboards_orig)
    cur_scoreboards = scoreboards[str(ctx.message.guild.id)]

  scoreboards_display = f"There are currently {len(cur_scoreboards)} scoreboards on this server\n" + "".join([("\n"+scoreboard) for scoreboard in cur_scoreboards])
  await ctx.send(scoreboards_display)





#removeScoreboard
@client.command(name='removeScoreboard',
                description="Removes a specified scoreboard.\n\nCorrect usage is s!removeScoreboard [scoreboard]",
                brief="Removes a scoreboard",
                aliases=['RemoveScoreboard', "removescoreboard"])
async def removeScoreboard(ctx, *args):
  correct_usage = "Correct usage is s!removeScoreboard [scoreboard]"
  try:
    scoreboard_name = args[0]
  except IndexError:
    await ctx.send("Something went wrong!\n" + correct_usage)
    return

  with open('scoreboards.txt', "r") as scoreboards_orig:

    # Load scoreboard
    scoreboards = json.load(scoreboards_orig)
    scoreboard = []
    try:
      # Find scoreboard
      del scoreboards[str(ctx.message.guild.id)][scoreboard_name]
    except KeyError:
      # If the key can't be found
      await ctx.send("That scoreboard does not seem to exist.")
      return

  with open('scoreboards.txt', "w") as scoreboards_orig:
    json.dump(scoreboards, scoreboards_orig, indent=4)

  await ctx.send(f"Removed {scoreboard_name}.")



#Deprecated functions

#addMember (deprecated)
@client.command(name='addMember',
                description="Previously added a member to a scoreboard, now use s!member add",
                brief="Use s!member add [member|role] [scoreboard]",
                aliases=['add_m', 'addmember', 'AddMember'])
async def addMember(ctx):
  await ctx.send("This command has been replaced with\ns!member add [member|role] [scoreboard]")

#removeMember (deprecated)
@client.command(name='removeMember',
                description="Previously removed a member from a scoreboard, now use s!member remove",
                brief="Use s!member remove [member|role] [scoreboard]",
                aliases=['remove_m', 'rm', 'removemember', 'RemoveMember'])
async def removeMember(ctx):
  await ctx.send("This command has been replaced with\ns!member remove [member|role] [scoreboard]")


token = os.environ.get("DISCORD_BOT_SECRET")

client.run(token)
