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

DEFAULT_MESSAGE_PREFIX = "s!"


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY0MTIyOTE1MzQzMzI4ODcyNCIsImJvdCI6dHJ1ZSwiaWF0IjoxNTc2MTYzNzk4fQ._imK5bBS2eeLyIXiolADEfeyTliaTrHYI-B05ECV58Q' # set this to your DBL token
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

    async def on_guild_post():
        print("Server count posted successfully")

def setup(bot):
    bot.add_cog(TopGG(bot))


def prefix(bot, message):
    with open('prefixes.json', "r") as prefixFile:
        prefixes = json.load(prefixFile)
    return prefixes.get(str(message.guild.id), DEFAULT_MESSAGE_PREFIX)

  
client = Bot(command_prefix=prefix)


@client.command(name='prefix',
                description="Changes the prefix for the bot",
                brief="Changes prefix for the bot",
                aliases=['pre', 'change_prefix', 'changeprefix', 'changePrefix'],
                pass_context=True)
async def change_prefix(ctx, *args):
    if len(args) > 0:
        new_prefix = args[0]
    else:
      await ctx.send("You have to give a new prefix\nCorrect usage is s!prefix [new_prefix]")
    
    with open('prefixes.json', "r") as prefixFile:
        prefixes = json.load(prefixFile)
    prefixes[str(ctx.guild.id)] = new_prefix

    with open('prefixes.json', 'w') as prefixFile:
        json.dump(prefixes, prefixFile, indent=4)

    await ctx.send("Changed prefix to " + new_prefix)

    

# TODO: Prefix function

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
  

  with open('prefixes.json', "r") as prefixFile:
        prefixes = json.load(prefixFile)
        for guild in client.guilds:
            if str(guild.id) not in prefixes.keys():
                prefixes[str(guild.id)] =  DEFAULT_MESSAGE_PREFIX
    
  with open("prefixes.json", "w") as prefixFile:
      json.dump(prefixes, prefixFile, indent=4)


def check_permissions(ctx, *args):
  permissions = ctx.message.channel.permissions_for(ctx.message.author)

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
    
    
    with open('prefixes.json', "r") as prefixFile:
        prefixes = json.load(prefixFile)
        for guild in client.guilds:
            if str(guild.id) not in prefixes.keys():
                prefixes[str(guild.id)] =  DEFAULT_MESSAGE_PREFIX
    
    with open("prefixes.json", "w") as prefixFile:
        json.dump(prefixes, prefixFile, indent=4)

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
#@commands.check(check_permissions)
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
          cur_member = "<@" + str(cur_member.id) + ">"

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


@client.command(name='points',
                description="Manages someones points on a specified scoreboard. You can add points to all members with a certain role as well\n\nCorrect usage is s!points (add/remove/set) [member/role] [scoreboard_name] [points]",
                brief="Adds points to someone.",
                aliases=['point', 'p'])
#@commands.check(check_permissions)
async def points(ctx, *args):
  correct_usage = 'Correct usage is s!points (add/remove/set) [member/role] [scoreboard_name] [points]'

  #Get user input
  try:
    option, member, scoreboard_name, points = args
    points = int(points)
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
        for server_member in ctx.message.guild.members:
          if cur_member == ("<@" + str(server_member.id) + ">"):
            cur_member = server_member
            break
        else:
          continue
        for cur_role in cur_member.roles:
          if role == cur_role:
            membersAffected.append(cur_member)
            break
    else:
      # If only a single user is mentioned
      try:
        user = client.get_user(int(''.join(c for c in member if c.isdigit())))
      except:
        user = None
      if user == None:
        membersAffected = [member]
      else:
        membersAffected = ["<@" + str(user.id) + ">"]

    for cur_member in membersAffected:
      if isinstance(cur_member, discord.member.Member):
        cur_member = "<@" + str(cur_member.id) + ">"
      
      try:
        scoreboards[str(ctx.message.guild.id)][scoreboard_name]
      except KeyError:
        await ctx.send(f"The scoreboard *{scoreboard_name}* does not seem to exist\n" + correct_usage)
        return
      try:
        if option == "add":
          scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][cur_member] += points
        elif option == "remove":
          scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][cur_member] -= points
        elif option == "set":
          scoreboards[str(ctx.message.guild.id)][scoreboard_name]["participants_scores"][cur_member] = points
      except KeyError:
        # If a member is not on the scoreboard just continue, this should not happen but it is not the users fault
        continue

      try:
        with open('scoreboards.txt', "w") as scoreboards_orig:
          json.dump(scoreboards, scoreboards_orig, indent=4)
      except:
        await ctx.send("Internal server error, count to 10 and try again")
      
    if option == "add":
      await ctx.send(f"Successfully added {points} point(s) to {member}")
    elif option == "remove":
      await ctx.send(f"Successfully removed {points} point(s) from {member}")
    elif option == "set":
      await ctx.send(f"Successfully set {member} points to {points}")



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
      members_per_page = 10
      current_page = []

      for key, value in member_order:
        current_page.append([key, value])
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

      embed = Embed(title=f"{scoreboard_name}", colour=discord.Colour(900))

      current_page = pages[page_number - 1]

      default_table = """
      ╔r╦m╦p╗
      ║l1000║n1000║s1000║
      ╠r╬m╬p╣
      ║l1001║n1001║s1001║
      ╠r╬m╬p╣
      ║l1002║n1002║s1002║
      ╚r╩m╩p╝
      """
      table = ""

      # To not have duplicates
      offset = 1000

      # This will be the minimum length of each row
      memberLength = len("member")
      pointsLength = len("points")
      rankLength = len("rank")

      tableLenghtener = "═"
      current_page.insert(0, ["Member", "Points"])
      usernames = []
      for index, member_points in enumerate(current_page, offset):
        member = member_points[0]
        points = member_points[1]

        # Member is in format <@id>
        try:
          user = client.get_user(int(member[2:len(member)-1]))
        except:
          user = None
        # If user is not found, replace with the member since it is probably not in the format above
        if user == None:
          username = member
        else:
          username = "@" + user.name

        
        usernames.append(username)
        # Make the length equal the longest name
        if len(username) > memberLength:
          memberLength = len(username)
        
        if (len(str(points))) > pointsLength:
          pointsLength = len(str(points))
        
        if (index - offset) == 0:
          table += f"╔r╦m╦p╗\n"
          table += f"║l{index}║n{index}║s{index}║\n"
          table += f"╠r╬m╬p╣\n"
        elif (index - offset) == (len(current_page) - 1):
          table += f"║l{index}║n{index }║s{index}║\n"
          table += "╚r╩m╩p╝\n"
        else:
          table += f"║l{index}║n{index}║s{index}║\n"
          table += "╠r╬m╬p╣\n"
      
      # Add 2 spaces to create margin
      margin = 2
      memberLength += margin 
      pointsLength += margin
      rankLength += margin
      
      table = table.replace("r", tableLenghtener*rankLength)
      table = table.replace("m", tableLenghtener*memberLength)
      table = table.replace("p", tableLenghtener*pointsLength)
      

      for index, member_points in enumerate(current_page, offset):
        member = member_points[0]
        points = member_points[1]
        table = table.replace(f"n{index}", f" {usernames[index - offset]}".ljust(memberLength, " "))
        table = table.replace(f"s{index}", f"{str(points)}".center(pointsLength, " "))

        if (index - offset) == 0:
          table = table.replace(f"l{index}", " Rank".ljust(rankLength, " "))
      
        else:
          table = table.replace(f"l{index}", f" {(index - offset) + page_number * members_per_page}.".ljust(rankLength, " "))
        

      embed.add_field(name="_", value=f"```{table}```", inline=False)
      embed.add_field(name="Page", value=f"{page_number}/{len(pages)}")


      await ctx.send(embed=embed)
      if (len(embed) > 1024):
        await ctx.send("Scoreboard is too large")


    except KeyError:
      await ctx.send("That scoreboard does not seem to exist on this server.\n" + correct_usage)

#ResetScoreboard
@client.command(name='resetScoreboard',
                description="Resets all scores on a specified scoreboard.\n\nCorrect usage is s!resetScores [scoreboard]",
                brief="Resets all scores on a specified scoreboard",
                aliases=['reset_scores', 'resetscores', "ResetScores", "resetScores", 'reset_scoreboard', 'resetscoreboard', "ResetScoreboard", "wipe", "Wipe"])
#@commands.check(check_permissions)
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
#@commands.check(check_permissions)
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
