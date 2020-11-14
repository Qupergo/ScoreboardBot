import os
import json
import discord
from discord import Activity, ActivityType, Embed
from discord.ext.commands import Bot

from keep_alive import keep_alive
import dbl
from discord.ext import commands, tasks
from dotenv import load_dotenv
import logging

load_dotenv()

DEFAULT_MESSAGE_PREFIX = "s!"


dbl_token = os.environ.get("DBL_TOKEN")


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = dbl_token # set this to your DBL token
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

    @commands.Cog.listener()
    async def on_guild_post():
        print("Server count posted successfully")

def setup(bot):
    bot.add_cog(TopGG(bot))




def prefix(bot, message):
    with open('prefixes.json', "r") as prefixFile:
        prefixes = json.load(prefixFile)
    return prefixes.get(str(message.guild.id), DEFAULT_MESSAGE_PREFIX)


client = Bot(command_prefix=prefix)
client.remove_command('help')
setup(client)

async def check_permissions(ctx, *args):
  permissions = ctx.message.channel.permissions_for(ctx.message.author)
  hasPermission = False

  # If I am using the bot, always give me access because I like to abuse my privilieges
  if "168341261516800000" == str(ctx.author.id):
    hasPermission = True
  
  if "scorekeeper" in [role.name.lower() for role in ctx.message.author.roles]:
    hasPermission = True

  if permissions.administrator or hasPermission:
    return True
  await ctx.send(":x: This command requires you to either have a role named `Scorekeeper` or be an `Administrator` to use it")
  return False



@client.command(name='prefix',
                aliases=['pre', 'change_prefix', 'changeprefix', 'changePrefix'],
                pass_context=True)
@commands.check(check_permissions)
async def change_prefix(ctx, *args):
    if len(args) > 0:
        new_prefix = args[0]
    else:
      await ctx.send("You have to give a new prefix\nCorrect usage is `s!prefix [new_prefix]`")
    
    with open('prefixes.json', "r") as prefixFile:
        prefixes = json.load(prefixFile)
    prefixes[str(ctx.guild.id)] = new_prefix

    with open('prefixes.json', 'w') as prefixFile:
        json.dump(prefixes, prefixFile, indent=4)

    await ctx.send(":white_check_mark: Changed prefix to " + new_prefix)

    

@client.event
async def on_ready():
  ##Starting
  print("Im in")

  print(client.user)
  guilds = client.guilds

  

  memberSum = 0
  iteration = 0
  topGuilds = []
  

  for guild in guilds:
    memberSum += len(guild.members)
    topGuilds.append(guild)
    iteration += 1
  topGuilds = sorted(topGuilds, reverse=True, key=lambda x:len(x.members))

  print("The top guilds are:")
  for index, guild in enumerate(topGuilds[:15]):
    print(f"{index+1}. {guild.name}: {len(guild.members)} members")

  print(f"This bot is used by a total of: {memberSum} members")
  print(f"Current amount of servers: {iteration}")

  await client.change_presence(activity=Activity(name=f" scoreboards on {len(guilds)} servers", type=ActivityType.watching))
  #Starting End
  
      


  with open('prefixes.json', "r") as prefixFile:
        prefixes = json.load(prefixFile)
        for guild in client.guilds:
            if str(guild.id) not in prefixes.keys():
                prefixes[str(guild.id)] =  DEFAULT_MESSAGE_PREFIX
    
  with open("prefixes.json", "w") as prefixFile:
      json.dump(prefixes, prefixFile, indent=4)


@client.event
async def on_guild_join(guild):
    await client.change_presence(activity=Activity(name=f" scoreboards on {len(client.guilds)} servers", type=ActivityType.watching))

    for guild in client.guilds:
      open_scoreboard(guild)
    
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
                aliases=[' create'])
@commands.check(check_permissions)
async def create(ctx, *args):
  correct_usage = "Correct usage is `s!create [scoreboard]`"
  try:
    scoreboard_name = args[0]
  except IndexError:
    await ctx.send(":x: Not enough arguments.\n" + correct_usage)
    return

  scoreboards = open_scoreboard(ctx.message.guild)

  scoreboards[scoreboard_name] = {'name':scoreboard_name, 'guild_id':str(ctx.message.guild.id), 'participants_scores':{}}
  save_scoreboards(scoreboards, ctx.message.guild)
  await ctx.send(f':white_check_mark: Created a scoreboard with the name {scoreboard_name}')

#Member
@client.command(name='member',
                aliases=['Member', 'mem', 'Mem'])
@commands.check(check_permissions)
async def member(ctx, *args):
  correct_usage = "Correct usage is `s!member (add/remove) [member/role/position] [scoreboard_name]`"
  try:
    option, member, scoreboard_name = args
  except ValueError:
    await ctx.send(":x: Not enough arguments\n" + correct_usage)
    return

  if option.lower() not in ['add', "+", 'remove', "-"]:
    await ctx.send("Incorrect option for `s!add`. Use either `add` or `remove`\n" + correct_usage)
    return

  scoreboards = open_scoreboard(ctx.message.guild)
  if scoreboard_name not in scoreboards.keys():
    await ctx.send(f":x: The scoreboard `{scoreboard_name}` does not exist.")
    return
    
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
      try:
        # Removing from position
        if member.isdigit():
          sorted_member_list = []

          for ID, value in scoreboards[scoreboard_name]['participants_scores'].items():
            sorted_member_list.append([ID, value])
          
          # TODO: Check settings for how to sort the scoreboard
          sorted_member_list.sort(key=lambda x:int(x[1]), reverse=True)

          if (int(member)) <= len(sorted_member_list):
            member_at_pos = sorted_member_list[int(member) - 1]

          member = member_at_pos[0]

        user = client.get_user(int(''.join(c for c in member if c.isdigit())))
      except:
        user = None
      if user == None:
        members_to_interact = [member]
      else:
        members_to_interact = ["<@" + str(user.id) + ">"]



      for cur_member in members_to_interact:
        #For some reason, discord adds ! to mentions sometimes
        #This will then count as different people, even though they mention the same person
        #So just default it to <@user_id> instead of <@!user_id>
        if isinstance(cur_member, discord.member.Member):
          cur_member = "<@" + str(cur_member.id) + ">"
        

        if option.lower() in ["add", "+"]:
          # If the member is already in the scoreboard, don't add them again
          if cur_member in scoreboards[scoreboard_name]["participants_scores"].keys():
            continue
          scoreboards[scoreboard_name]["participants_scores"][cur_member] = 0
        
        elif option.lower() in ["remove", "-"]:
          # If the member is not in the scoreboard you can't remove them.
          # But if you are removing by role it is completly fine to try and remove a couple member who aren't on the scoreboard.
          # Since expected behaviour is to remove everyone with that role.
          if not cur_member in scoreboards[scoreboard_name]["participants_scores"].keys() and len(members_to_interact) == 1:
            await ctx.send(f":x: The member {cur_member} does not seem to exist in that scoreboard")
            return

          del scoreboards[scoreboard_name]["participants_scores"][cur_member]

  except KeyError:
    await ctx.send(f":x: The member {member} does not seem to exist in that scoreboard.")
    return

  save_scoreboards(scoreboards, ctx.message.guild)

  if option.lower() == "remove":
    await ctx.send(f':white_check_mark: removed {member} from `{scoreboard_name}`')

  elif option.lower() == "add":
    await ctx.send(f":white_check_mark: added {member} to `{scoreboard_name}`")


#points
@client.command(name='points',
                aliases=['point', 'p'])
@commands.check(check_permissions)
async def points(ctx, *args):
  correct_usage = 'Correct usage is `s!points (add/remove/set) [member/role] [scoreboard_name] [points]`'

  #Get user input
  try:
    option, member, scoreboard_name, points = args
    points = round(float(points), 3)
  except ValueError:
    await ctx.send(":x: Invalid arguments.\n" + correct_usage)
    return
  
  #Option should be either add, remove or set
  #Otherwise throw error
  if option not in ["add", "remove", "set"]:
    await ctx.send(f":x: Incorrect option for `s!points` {option}\nPlease use either `add`, `remove` or `set`\n" + correct_usage)
    return
  
  scoreboards = open_scoreboard(ctx.message.guild)

  if scoreboard_name not in scoreboards.keys():
    await ctx.send(f":x: The scoreboard `{scoreboard_name}` does not seem to exist.")
    return
  

  scoreboard_members = scoreboards[scoreboard_name]["participants_scores"].keys()

  #Check if a role has been mentioned
  roles = ctx.message.role_mentions
  membersAffected = []

  if len(roles) > 0:
    #Add all members with the role to membersAffected
    role = roles[0]
    for cur_member in scoreboard_members:
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

    if len(membersAffected) == 0:
      await ctx.send(f":x: There does not seem to be anyone with the role {role} in `{scoreboard_name}`")
      return
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
      if option == "add":
        scoreboards[scoreboard_name]["participants_scores"][cur_member] += points
      elif option == "remove":
        scoreboards[scoreboard_name]["participants_scores"][cur_member] -= points
      elif option == "set":
        scoreboards[scoreboard_name]["participants_scores"][cur_member] = points
    except KeyError:
      if len(membersAffected) == 1:
        await ctx.send(f":x: {membersAffected[0]} does not seem to exist in `{scoreboard_name}`")
        return

  save_scoreboards(scoreboards, ctx.message.guild)

  if option == "add":
    await ctx.send(f":white_check_mark: Successfully added {points} point(s) to {member}")
  elif option == "remove":
    await ctx.send(f":white_check_mark: Successfully removed {points} point(s) from {member}")
  elif option == "set":
    await ctx.send(f":white_check_mark: Successfully set {member} points to {points}")




#show
@client.command(name='show',
                aliases=['Show'])
async def show(ctx, *args):
  correct_usage = "Correct usage is `s!show [scoreboard] <page_number>`"
  page_number = 1
  try:
    scoreboard_name = args[0]
  except:
    await ctx.send(":x: Invalid arguments.\n" + correct_usage)
    return

  if len(args) > 1:
    try:
      page_number = int(args[1])
    except:
      pass
    
  scoreboards = open_scoreboard(ctx.message.guild)

  member_order = []
  if scoreboard_name not in scoreboards.keys():
    await ctx.send(f":x: `{scoreboard_name}` does not seem to exist on this server.\n" + correct_usage)
    return

  #Make a sorted list of the members by their points
  for key, value in scoreboards[scoreboard_name]['participants_scores'].items():
    member_order.append([key, value])
  member_order.sort(key=lambda x:float(x[1]), reverse=True)

  iteration = 0
  pages = []
  try:
    settings = scoreboards[scoreboard_name]["settings"]
  except:
    scoreboards[scoreboard_name]["settings"] = default_settings()
    settings = scoreboards[scoreboard_name]["settings"]



  members_per_page = int(settings["members_per_page"])
  formatting = settings["format"]

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
    await ctx.send(f"Unfortunately, `{scoreboard_name}` is empty, there is nothing to show.")
    return

  # Default
  if page_number == 1:
    embed = Embed(title=f"{scoreboard_name}", colour=discord.Colour(0x00FFFF))
  else:
    embed = Embed(colour=discord.Colour(0x00FFFF))
  embed.add_field(name="Page", value=f"{page_number}/{len(pages)}")
  
  current_page = pages[page_number - 1]

  #
  #TABLE
  #
  if formatting == "table":
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


      username = await get_username_from_id(member)
      
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
        table = table.replace(f"l{index}", f" {(index - offset) + (page_number-1) * members_per_page}.".ljust(rankLength, " "))
    
    embed.add_field(name="_", value=f"```{table}```", inline=False)

  #
  # Classic
  #
  elif formatting == "classic":
    title = "💠 🔷 🔹🔹 **" + scoreboard_name + "** 🔹🔹 🔷 💠"
    point_prefix = "🔹"
    scoreboard_classic = ""
    for index, member_points in enumerate(current_page):
      member = member_points[0]
      points = member_points[1]
      username = await get_username_from_id(member)

      scoreboard_classic += f"{index+1}. {username}\n{point_prefix} {points}\n\n"
    embed.add_field(name="_", value=f"{scoreboard_classic}", inline=False)
    embed.title = title
  



  if (len(embed) >= 1024):
    await ctx.send("Scoreboard exceeds discord's character limit\nYou can try to lower the members per page or change the formatting using `s!settings`")
    return
  else:
    message = await ctx.send(embed=embed)

#ResetScoreboard
@client.command(name='resetScoreboard',
                aliases=['reset_scores', 'resetscores', "ResetScores", "resetScores", 'reset_scoreboard', 'resetscoreboard', "ResetScoreboard", "wipe", "Wipe"])
@commands.check(check_permissions)
async def resetScoreboard(ctx, *args):
  correct_usage = "Correct usage is `s!resetScores [scoreboard]`"
  try:
    scoreboard_name = args[0]
  except IndexError:
    await ctx.send(":x: Invalid arguments.\n" + correct_usage)
    return

  scoreboards = open_scoreboard(ctx.message.guild)
  if scoreboard_name not in scoreboards.keys():
    await ctx.send(f":x: `{scoreboard_name}` does not seem to exist.")
    return
  



  for key in scoreboards[scoreboard_name]["participants_scores"].keys():
    scoreboards[scoreboard_name]["participants_scores"][key] = 0

  save_scoreboards(scoreboards, ctx.message.guild)

  await ctx.send(f":white_check_mark: Reset all values in `{scoreboard_name}` to 0.")


#list
@client.command(name='list',
                aliases=[])
@commands.check(check_permissions)
async def list(ctx, *args):
  correct_usage = "Correct usage is `s!list`"

  for guild in client.guilds:
    #open_scoreboard makes sure the guild has a file
    open_scoreboard(guild)
    with open('scoreboards.txt', "r") as scoreboards_orig:
        scoreboards = json.load(scoreboards_orig)
        save_scoreboards(scoreboards[str(guild.id)], guild)
  print(len(client.guilds))
  
  scoreboards = open_scoreboard(ctx.message.guild)

  scoreboards_display = f"There are currently {len(scoreboards)} scoreboards on this server\n" + "".join([("\n`"+scoreboard+"`") for scoreboard in scoreboards])
  await ctx.send(scoreboards_display)





#removeScoreboard
@client.command(name='removeScoreboard',
                aliases=['RemoveScoreboard', "remove_scoreboard"])
@commands.check(check_permissions)
async def removeScoreboard(ctx, *args):
  correct_usage = "Correct usage is `s!removeScoreboard [scoreboard]`"
  try:
    scoreboard_name = args[0]
  except IndexError:
    await ctx.send(":x: Invalid arguments.\n" + correct_usage)
    return

  scoreboards = open_scoreboard(ctx.message.guild)

  if scoreboard_name not in scoreboards.keys():
    await ctx.send(f":x: `{scoreboard_name}` does not seem to exist.")
    return

  del scoreboards[scoreboard_name]

  save_scoreboards(scoreboards, ctx.message.guild)

  await ctx.send(f":white_check_mark: Removed `{scoreboard_name}`")


@client.command(pass_context=True)
@commands.check(check_permissions)  
async def settings(ctx, *args):
  correct_usage = "Correct usage is `s!settings [scoreboard/all] [setting] [change]` write `s!help settings` for more info"
  formats = ["table", "classic_crimson", "classic", "classic_gamble"]
  settings = ["prefix", "members_per_page", "membersperpage", "format"]
  try:
    scoreboard_name, setting, change = args
    setting = setting.lower()
    change = change.lower()
  except:
    await ctx.send(":x: Invalid arguments.\n" + correct_usage)
    return
  # Settings:
  # Prefix
  # Members per page
  # formatting
  # Show settings


  if setting not in settings:
    await ctx.send(f"{setting} is not a valid setting\n{correct_usage}")
    return

  # Check if valid change
  if setting in ["formatting", "format"]:
    if change.lower() not in formats:
      await ctx.send(f":x: `{change}` is not a valid format.\n{correct_usage}")
      return
  
  elif setting in ["members_per_page", "mpp", "membersperpage"]:
    if not change.isdigit():
      await ctx.send(f":x: `{change}` needs to be a number.\n{correct_usage}")
      return


  scoreboards = open_scoreboard(ctx.message.guild)

  if scoreboard_name.lower() == "all":
    for scoreboard_name in scoreboards.keys():
      # If there is no setting page
      # Just create one with default settings
      if "settings" not in scoreboards[scoreboard_name].keys():
        scoreboards[scoreboard_name]["settings"] = default_settings()
      
      scoreboards[scoreboard_name]["settings"][setting] = change

  elif scoreboard_name in scoreboards.keys():

    if "settings" not in scoreboards[scoreboard_name].keys():
      scoreboards[scoreboard_name]["settings"] = default_settings()
    
    scoreboards[scoreboard_name]["settings"][setting] = change

  else:
    await ctx.send(f":x: A scoreboard with the name `{scoreboard_name}` does not seem to exist.")
    return

  save_scoreboards(scoreboards, ctx.message.guild)

  await ctx.send(f":white_check_mark: Sucessfully changed `{setting}` to `{change}`")

    

def default_settings():
  return {
    "format":"table",
    "prefix":"s!",
    "members_per_page":10,
          }

async def get_username_from_id(member):
  # Member is in format <@id> or <@!id> if it is a mentioned user
  print("Member: " + member)
  try:
    id = int(''.join(c for c in member if c.isdigit()))
    user = client.get_user(id)
    print("Found user")
    print(user)
    print(id)
  except:
    user = None
  # If user is not found, replace with the member since it is probably not in the format above
  if user == None:
    username = member
  else:
    username = "@" + user.name
    print(user.name)
  return username

#save_scoreboards
def save_scoreboards(scoreboards, guild):
  with open(os.path.join("scoreboards/", str(guild.id) + ".txt"), "w") as scoreboards_orig:
      json.dump(scoreboards, scoreboards_orig, indent=4)

#open_scoreboard
def open_scoreboard(guild, create_new_if_missing=True):

  scoreboards = "{}"
  try:
    with open(os.path.join("scoreboards/", str(guild.id) + ".txt"), "r") as scoreboards_orig:
      scoreboards = json.load(scoreboards_orig)
  except FileNotFoundError:
    if create_new_if_missing:
      with open(os.path.join("scoreboards/", str(guild.id) + ".txt"), "w") as scoreboards_orig:
        scoreboards_orig.write("{}")
    else:
      scoreboards = None

  return scoreboards



#Help
@client.command(pass_context=True)
async def help(ctx, *args):
  if len(args) > 0:
    in_depth_command = args[0]
  else:
    in_depth_command = "None"
  
  author = ctx.message.author
  embed = Embed(colour=discord.Colour(0x00FFFF))

  if in_depth_command.lower() == "settings":
    embed.set_author(name="Help Settings")

    embed.add_field(name="s!settings", value="`s!settings [scoreboard/all] [setting] [change]`\nThe settings you can change are:", inline=False)

    embed.add_field(name="Format, this changes the look of the scoreboard.", value="These are the available formats:\n", inline=False)
    embed.add_field(name="💠 🔷 🔹🔹 **Classic** 🔹🔹 🔷 💠\n\n", value="```╔═══════╗\n║ Table ║\n╚═══════╝```\n`s!settings [scoreboard/all] format table|classic`", inline=False)

    embed.add_field(name="\n\nMembers per page, this changes the amount of members per page.", value="`s!settings [scoreboard/all] members_per_page 15`", inline=False)
  else:
    # All commands: s!create, s!show, s!member, s!points, s!list, s!prefix, s!removescoreboards, s!resetscoreboards, , s!help, 

    embed.set_author(name="Help")

    embed.add_field(name="s!create", value="Creates a scoreboard.\n`s!create [scoreboard_name]`", inline=False)

    embed.add_field(name="s!show", value="Displays a scoreboard.\n`s!show [scoreboard]`", inline=False)

    embed.add_field(name="s!member", value="Adds or removes members in a scoreboard.\n`s!member (add/remove) [@member|@role|position] [scoreboard_name]`", inline=False)

    embed.add_field(name="s!points", value="Add, remove or set points in a scoreboard.\n`s!points (add|remove|set) [@member|@role] [scoreboard_name]`", inline=False)

    embed.add_field(name="s!list", value="Lists all scoreboards in the server.\n`s!list`", inline=False)

    embed.add_field(name="s!prefix", value="Changes the prefix for the bot.\n`s!prefix [new_prefix]`", inline=False)

    embed.add_field(name="s!remove_scoreboard", value="Removes a scoreboard.\n`s!remove_scoreboard [scoreboard]`", inline=False)

    embed.add_field(name="s!reset_scoreboard", value="Resets all scores in a scoreboard.\n`s!reset_scoreboard [scoreboard]`", inline=False)

    embed.add_field(name="s!help", value="Shows you this message.\n`s!help`", inline=False)

    embed.add_field(name="s!invite", value="Sends you a link to invite this bot\n`s!invite`", inline=False)

    embed.add_field(name="s!settings", value="Allows you to change various settings for Scoreboarder\n`s!settings [setting] [scoreboard/all] [change]` \nwrite `s!help settings` for more info")

  await ctx.send("Sent you a DM containing the help message.")
  await author.send(embed=embed)






















#Deprecated functions

#addMember (deprecated)
@client.command(name='addMember',
                aliases=['add_m', 'addmember', 'AddMember'])
async def addMember(ctx):
  await ctx.send("This command has been replaced with\ns!member add [member|role] [scoreboard]")

#removeMember (deprecated)
@client.command(name='removeMember',
                aliases=['remove_m', 'rm', 'removemember', 'RemoveMember'])
async def removeMember(ctx):
  await ctx.send("This command has been replaced with\ns!member remove [member|role] [scoreboard]")

#addPoints
@client.command(name='addPoints',
                aliases=['add_p', 'addP', "addpoints", 'addp'])
@commands.check(check_permissions)
async def addPoints(ctx, *args):


  correct_usage = "This command has been deprecated, consider using ```s!points add``` instead."
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
    await ctx.send(f'Added 1 point to {member}, new score is {new_score}.\nThis command has been deprecated, consider using ```s!points add``` instead.')
  else:
    await ctx.send(f'Added {points} points to {member}, new score is {new_score}.\nThis command has been deprecated, consider using ```s!points add``` instead.')


#removePoints
@client.command(name='removePoints',
                aliases=['remove_p', 'removeP', "rm_p", "rmP", "removepoints"])
@commands.check(check_permissions)
async def removePoints(ctx, *args):
  correct_usage = "This command has been deprecated, consider using `s!points remove` instead."
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
    await ctx.send(f'Removed 1 point from {member}, new score is {new_score}.\nThis command has been deprecated, consider using `s!points remove` instead.')
  else:
    await ctx.send(f'Removed {points} points from {member}, new score is {new_score}.\nThis command has been deprecated, consider using `s!points remove` instead.')

saving_scoreboard = False

token = os.environ.get("DISCORD_BOT_SECRET")

client.run(token)
