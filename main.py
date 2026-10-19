import sqlite3
import discord
from discord import app_commands
from discord.ext import commands

# --- DATABASE SETUP ---
conn = sqlite3.connect("efootball_league.db")
cursor = conn.cursor()

# Create table for players/teams
cursor.execute("""
CREATE TABLE IF NOT EXISTS players (
    user_id INTEGER PRIMARY KEY,
    ign TEXT NOT NULL,
    efootball_id TEXT,
    team_name TEXT,
    key_player TEXT DEFAULT 'None',
    played INTEGER DEFAULT 0,
    won INTEGER DEFAULT 0,
    drawn INTEGER DEFAULT 0,
    lost INTEGER DEFAULT 0,
    goals_for INTEGER DEFAULT 0,
    goals_against INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0
)
""")
conn.commit()

# --- OFFICIAL LEAGUE TEAMS ---
OFFICIAL_TEAMS = [
    "Coach Youssef Mohab's Team",
    "Coach Asser Adel's Team",
    "Coach Fares Nassar's Team",
    "Coach Ahmed Amr's Team",
    "Coach Adam Khattab's Team",
    "Coach Omar Ahmed's Team",
    "Coach Ahmed Mostafa's Team",
]

BOT_NAME = "Vleague Administrator"

# --- LOCAL FOOTBALL PLAYER DATABASE ---
# You can add as many players as you want here easily!
LOCAL_PLAYERS = {
    "messi": {
        "name": "Lionel Messi",
        "team": "Inter Miami / Argentina",
        "nationality": "Argentina",
        "position": "RW / AM",
    },
    "ronaldo": {
        "name": "Cristiano Ronaldo",
        "team": "Al Nassr / Portugal",
        "nationality": "Portugal",
        "position": "ST / LW",
    },
    "ronaldinho": {
        "name": "Ronaldinho Gaúcho",
        "city": "Icon / Legend",
        "team": "FC Barcelona (Legend)",
        "nationality": "Brazil",
        "position": "LW / AM",
    },
    "cruyff": {
        "name": "Johan Cruyff",
        "team": "Ajax / Barcelona (Legend)",
        "nationality": "Netherlands",
        "position": "CF / AM",
    },
    "neymar": {
        "name": "Neymar Jr",
        "team": "Al Hilal / Brazil",
        "nationality": "Brazil",
        "position": "LW / AM",
    },
    "mbappe": {
        "name": "Kylian Mbappé",
        "team": "Real Madrid / France",
        "nationality": "France",
        "position": "ST / LW",
    },
    "haaland": {
        "name": "Erling Haaland",
        "team": "Manchester City / Norway",
        "nationality": "Norway",
        "position": "ST",
    },
    "pele": {
        "name": "Pelé",
        "team": "Santos (Legend)",
        "nationality": "Brazil",
        "position": "ST",
    },
    "maradona": {
        "name": "Diego Maradona",
        "team": "Napoli / Argentina (Legend)",
        "nationality": "Argentina",
        "position": "AM",
    },
    "salah": {
        "name": "Mohamed Salah",
        "team": "Liverpool / Egypt",
        "nationality": "Egypt",
        "position": "RW",
    },
}


# --- BOT SETUP ---
class eFootballBot(commands.Bot):

  def __init__(self):
    intents = discord.Intents.default()
    intents.members = True
    super().__init__(command_prefix="!", intents=intents)

  async def setup_hook(self):
    await self.tree.sync()
    print("Slash commands synced successfully!")


bot = eFootballBot()


@bot.event
async def on_ready():
  print(f"Logged in as {bot.user} (ID: {bot.user.id})")
  print(f"{BOT_NAME} is online and ready for action!")


def create_league_embed(title: str, color: discord.Color) -> discord.Embed:
  embed = discord.Embed(title=title, color=color)
  embed.set_footer(text=f"{BOT_NAME} • Official eFootball League")
  return embed


# --- COMMAND 1: LOCAL PLAYER SEARCH ---
@bot.tree.command(
    name="search_player",
    description="Search soccer players from the built-in database",
)
@app_commands.describe(
    player_name="Name of the player (e.g., Messi, Ronaldo, Ronaldinho, Salah)"
)
async def search_player(interaction: discord.Interaction, player_name: str):
  await interaction.response.defer()

  query = player_name.strip().lower()

  # Search in our local dictionary
  found_player = None
  for key, data in LOCAL_PLAYERS.items():
    if query in key or query in data["name"].lower():
      found_player = data
      break

  if not found_player:
    await interaction.followup.send(
        f"❌ Player **'{player_name}'** not found in local database. You can"
        " still type their name manually when using `/register`!"
    )
    return

  embed = create_league_embed(
      f"⚽ Player Profile: {found_player['name']}", discord.Color.gold()
  )
  embed.add_field(
      name="Nationality", value=found_player["nationality"], inline=True
  )
  embed.add_field(name="Position", value=found_player["position"], inline=True)
  embed.add_field(
      name="Current Club / Status", value=found_player["team"], inline=False
  )

  await interaction.followup.send(embed=embed)


# --- COMMAND 2: REGISTER FOR LEAGUE ---
@bot.tree.command(
    name="register", description="Register your team for the eFootball Mobile League"
)
@app_commands.choices(
    team_name=[
        app_commands.Choice(
            name="Coach Youssef Mohab's Team", value="Coach Youssef Mohab's Team"
        ),
        app_commands.Choice(
            name="Coach Asser Adel's Team", value="Coach Asser Adel's Team"
        ),
        app_commands.Choice(
            name="Coach Fares Nassar's Team", value="Coach Fares Nassar's Team"
        ),
        app_commands.Choice(
            name="Coach Ahmed Amr's Team", value="Coach Ahmed Amr's Team"
        ),
        app_commands.Choice(
            name="Coach Adam Khattab's Team", value="Coach Adam Khattab's Team"
        ),
        app_commands.Choice(
            name="Coach Omar Ahmed's Team", value="Coach Omar Ahmed's Team"
        ),
        app_commands.Choice(
            name="Coach Ahmed Mostafa's Team",
            value="Coach Ahmed Mostafa's Team",
        ),
    ]
)
@app_commands.describe(
    ign="Your In-Game Name in eFootball",
    efootball_id="Your eFootball User ID",
    team_name="Select your official Coach/Team",
    star_player="Type your key marquee/legend player name",
)
async def register(
    interaction: discord.Interaction,
    ign: str,
    efootball_id: str,
    team_name: app_commands.Choice[str],
    star_player: str = "None",
):
  await interaction.response.defer()
  user_id = interaction.user.id
  selected_team = team_name.value

  cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
  if cursor.fetchone():
    await interaction.followup.send("❌ You are already registered in the league!")
    return

  guild = interaction.guild
  if guild:
    role = discord.utils.get(guild.roles, name=selected_team)
    if role:
      try:
        await interaction.user.add_roles(role)
      except discord.Forbidden:
        print(f"⚠️ {BOT_NAME} lacks permission to assign roles.")

  cursor.execute(
      "INSERT INTO players (user_id, ign, efootball_id, team_name, key_player)"
      " VALUES (?, ?, ?, ?, ?)",
      (user_id, ign, efootball_id, selected_team, star_player),
  )
  conn.commit()

  embed = create_league_embed(
      "⚽ League Registration Successful!", discord.Color.green()
  )
  embed.add_field(
      name="Discord User", value=interaction.user.mention, inline=True
  )
  embed.add_field(name="In-Game Name", value=ign, inline=True)
  embed.add_field(name="eFootball ID", value=efootball_id, inline=True)
  embed.add_field(
      name="Assigned Team & Role", value=selected_team, inline=False
  )
  embed.add_field(
      name="Star Player Registered", value=star_player, inline=False
  )

  await interaction.followup.send(embed=embed)


# --- COMMAND 3: VIEW SQUAD PROFILE ---
@bot.tree.command(
    name="mysquad", description="View your registered eFootball squad details"
)
async def mysquad(interaction: discord.Interaction):
  await interaction.response.defer()
  user_id = interaction.user.id

  cursor.execute("SELECT * FROM players WHERE user_id = ?", (user_id,))
  player = cursor.fetchone()

  if not player:
    await interaction.followup.send(
        "❌ You are not registered yet! Use `/register` to join."
    )
    return

  embed = create_league_embed(
      f"🎮 {player[1]}'s Squad Profile", discord.Color.blue()
  )
  embed.add_field(name="In-Game Name", value=player[1], inline=True)
  embed.add_field(name="eFootball ID", value=player[2], inline=True)
  embed.add_field(name="Team", value=player[3], inline=False)
  embed.add_field(name="Marquee Star Player", value=player[4], inline=False)
  embed.add_field(
      name="Stats",
      value=(
          f"Played: {player[5]} | W: {player[6]} | D: {player[7]} | L:"
          f" {player[8]}\nPoints: **{player[11]}**"
      ),
      inline=False,
  )

  await interaction.followup.send(embed=embed)


# --- COMMAND 4: REPORT MATCH RESULT ---
@bot.tree.command(
    name="report_match", description="Report a score against an opponent coach"
)
@app_commands.describe(
    opponent="Select your opponent user",
    your_score="Goals you scored",
    opponent_score="Goals opponent scored",
)
async def report_match(
    interaction: discord.Interaction,
    opponent: discord.User,
    your_score: int,
    opponent_score: int,
):
  await interaction.response.defer()
  p1_id = interaction.user.id
  p2_id = opponent.id

  if p1_id == p2_id:
    await interaction.followup.send("❌ You cannot play against yourself!")
    return

  cursor.execute("SELECT * FROM players WHERE user_id = ?", (p1_id,))
  p1 = cursor.fetchone()
  cursor.execute("SELECT * FROM players WHERE user_id = ?", (p2_id,))
  p2 = cursor.fetchone()

  if not p1 or not p2:
    await interaction.followup.send(
        "❌ Both players must be registered using `/register` before reporting."
    )
    return

  p1_pts, p2_pts = 0, 0
  p1_w, p1_d, p1_l = 0, 0, 0
  p2_w, p2_d, p2_l = 0, 0, 0

  if your_score > opponent_score:
    p1_pts, p1_w, p2_l = 3, 1, 1
  elif your_score < opponent_score:
    p2_pts, p2_w, p1_l = 3, 1, 1
  else:
    p1_pts, p2_pts = 1, 1
    p1_d, p2_d = 1, 1

  cursor.execute(
      """
        UPDATE players SET 
            played = played + 1, won = won + ?, drawn = drawn + ?, lost = lost + ?,
            goals_for = goals_for + ?, goals_against = goals_against + ?, points = points + ?
        WHERE user_id = ?
    """,
      (p1_w, p1_d, p1_l, your_score, opponent_score, p1_pts, p1_id),
  )

  cursor.execute(
      """
        UPDATE players SET 
            played = played + 1, won = won + ?, drawn = drawn + ?, lost = lost + ?,
            goals_for = goals_for + ?, goals_against = goals_against + ?, points = points + ?
        WHERE user_id = ?
    """,
      (p2_w, p2_d, p2_l, opponent_score, your_score, p2_pts, p2_id),
  )

  conn.commit()

  embed = create_league_embed("📊 Match Result Recorded!", discord.Color.gold())
  embed.add_field(
      name=f"{p1[1]} ({p1[3]})", value=f"**{your_score}**", inline=True
  )
  embed.add_field(name="VS", value="-", inline=True)
  embed.add_field(
      name=f"{p2[1]} ({p2[3]})", value=f"**{opponent_score}**", inline=True
  )

  await interaction.followup.send(embed=embed)


# --- COMMAND 5: LEAGUE STANDINGS ---
@bot.tree.command(name="standings", description="View the current league table")
async def standings(interaction: discord.Interaction):
  await interaction.response.defer()
  cursor.execute("""
        SELECT ign, team_name, played, won, drawn, lost, (goals_for - goals_against) AS gd, points 
        FROM players 
        ORDER BY points DESC, gd DESC
    """)
  rows = cursor.fetchall()

  if not rows:
    await interaction.followup.send("No players registered yet!")
    return

  table = "```\n"
  table += (
      f"{'#':<3} {'Player':<12} {'Team':<25} {'P':<3} {'W':<3} {'D':<3}"
      f" {'L':<3} {'GD':<4} {'PTS':<3}\n"
  )
  table += "-" * 65 + "\n"

  for idx, row in enumerate(rows, 1):
    table += (
        f"{idx:<3} {row[0][:10]:<12} {row[1][:23]:<25} {row[2]:<3} {row[3]:<3}"
        f" {row[4]:<3} {row[5]:<3} {row[6]:<4} {row[7]:<3}\n"
    )

  table += "```"

  embed = create_league_embed("🏆 Vleague Standings Table", discord.Color.gold())
  embed.description = table
  await interaction.followup.send(embed=embed)


# --- RUN BOT ---
BOT_TOKEN =  "MTU2MTQ4MzUzNDc3NjkzMDMwNg.GEpPys.3TNo7_vNoPiMLI65mA2dTLagylWMGkGEwxj5Es"

if __name__ == "__main__":
  bot.run(BOT_TOKEN)
    
