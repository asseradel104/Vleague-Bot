import json
import os
import sqlite3

import discord
from discord import app_commands
from discord.ext import commands

BOT_NAME = "Vleague Administrator"
DB_PATH = os.path.join(os.path.dirname(__file__), "efootball_league.db")
PLAYERS_PATH = os.path.join(os.path.dirname(__file__), "players.json")
BOT_TOKEN = os.getenv("BOT_TOKEN")

OFFICIAL_TEAMS = [
    "Coach Youssef Mohab's Team",
    "Coach Asser Adel's Team",
    "Coach Fares Nassar's Team",
    "Coach Ahmed Amr's Team",
    "Coach Adam Khattab's Team",
    "Coach Omar Ahmed's Team",
    "Coach Ahmed Mostafa's Team",
]


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


conn = connect_db()
conn.execute(
    """
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
    """
)
conn.commit()


def load_players():
    try:
        with open(PLAYERS_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


class VleagueBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced successfully!")


bot = VleagueBot()


def create_league_embed(title: str, color: discord.Color) -> discord.Embed:
    embed = discord.Embed(title=title, color=color)
    embed.set_footer(text=f"{BOT_NAME} • Official eFootball League")
    return embed


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"{BOT_NAME} is online and ready for action!")


@bot.tree.command(name="search_player", description="Search for a football player by name or keyword.")
@app_commands.describe(player_name="Player name or alias (e.g. Messi, Ronaldo, Haaland)")
async def search_player(interaction: discord.Interaction, player_name: str):
    await interaction.response.defer()

    query = player_name.strip().lower()
    players = load_players()

    matched_player = None
    for player in players:
        searchable = " ".join([player.get("name", "").lower(), *[keyword.lower() for keyword in player.get("keywords", [])]])
        if query in searchable:
            matched_player = player
            break

    if not matched_player:
        await interaction.followup.send(f"❌ No player matched '{player_name}'. Try another name or keyword.")
        return

    embed = create_league_embed(f"⚽ {matched_player['name']}", discord.Color.gold())
    embed.add_field(name="Player Name", value=matched_player["name"], inline=True)
    embed.add_field(name="OVR", value=str(matched_player.get("ovr", "N/A")), inline=True)
    embed.add_field(name="Position", value=matched_player.get("position", "N/A"), inline=True)
    embed.add_field(name="Club / Team", value=matched_player.get("team", "N/A"), inline=False)
    if matched_player.get("nationality"):
        embed.add_field(name="Nationality", value=matched_player["nationality"], inline=True)

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="register", description="Register your squad for the official league.")
@app_commands.choices(
    team_name=[
        app_commands.Choice(name="Coach Youssef Mohab's Team", value="Coach Youssef Mohab's Team"),
        app_commands.Choice(name="Coach Asser Adel's Team", value="Coach Asser Adel's Team"),
        app_commands.Choice(name="Coach Fares Nassar's Team", value="Coach Fares Nassar's Team"),
        app_commands.Choice(name="Coach Ahmed Amr's Team", value="Coach Ahmed Amr's Team"),
        app_commands.Choice(name="Coach Adam Khattab's Team", value="Coach Adam Khattab's Team"),
        app_commands.Choice(name="Coach Omar Ahmed's Team", value="Coach Omar Ahmed's Team"),
        app_commands.Choice(name="Coach Ahmed Mostafa's Team", value="Coach Ahmed Mostafa's Team"),
    ]
)
@app_commands.describe(
    ign="Your eFootball in-game name",
    efootball_id="Your eFootball player ID",
    team_name="Choose your official coach/team",
    star_player="Your main star player",
)
async def register(
    interaction: discord.Interaction,
    ign: str,
    efootball_id: str,
    team_name: str,
    star_player: str = "None",
):
    await interaction.response.defer()

    if team_name not in OFFICIAL_TEAMS:
        await interaction.followup.send("❌ Invalid team selected. Please choose one of the official league teams.")
        return

    existing = conn.execute("SELECT 1 FROM players WHERE user_id = ?", (interaction.user.id,)).fetchone()
    if existing:
        await interaction.followup.send("❌ You are already registered in the league.")
        return

    conn.execute(
        "INSERT INTO players (user_id, ign, efootball_id, team_name, key_player) VALUES (?, ?, ?, ?, ?)",
        (interaction.user.id, ign, efootball_id, team_name, star_player),
    )
    conn.commit()

    if interaction.guild:
        role = discord.utils.get(interaction.guild.roles, name=team_name)
        if role:
            try:
                await interaction.user.add_roles(role)
            except discord.Forbidden:
                print(f"⚠️ {BOT_NAME} lacks permission to assign the '{team_name}' role.")

    embed = create_league_embed("⚽ League Registration Successful!", discord.Color.green())
    embed.add_field(name="Discord User", value=interaction.user.mention, inline=True)
    embed.add_field(name="IGN", value=ign, inline=True)
    embed.add_field(name="eFootball ID", value=efootball_id, inline=True)
    embed.add_field(name="Assigned Team", value=team_name, inline=False)
    embed.add_field(name="Star Player", value=star_player, inline=False)
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="mysquad", description="View your registered squad profile and stats.")
async def mysquad(interaction: discord.Interaction):
    await interaction.response.defer()

    row = conn.execute("SELECT * FROM players WHERE user_id = ?", (interaction.user.id,)).fetchone()
    if not row:
        await interaction.followup.send("❌ You are not registered yet. Use `/register` first.")
        return

    embed = create_league_embed(f"🎮 {row['ign']}'s Squad Profile", discord.Color.blue())
    embed.add_field(name="IGN", value=row["ign"], inline=True)
    embed.add_field(name="eFootball ID", value=row["efootball_id"], inline=True)
    embed.add_field(name="Team", value=row["team_name"], inline=False)
    embed.add_field(name="Star Player", value=row["key_player"], inline=False)
    embed.add_field(
        name="Stats",
        value=(
            f"Played: {row['played']} | W: {row['won']} | D: {row['drawn']} | L: {row['lost']}\n"
            f"GF: {row['goals_for']} | GA: {row['goals_against']} | GD: {row['goals_for'] - row['goals_against']} | Points: {row['points']}"
        ),
        inline=False,
    )

    await interaction.followup.send(embed=embed)


@bot.tree.command(name="report_match", description="Save the result of a match between two registered players.")
@app_commands.describe(
    opponent="Opponent user",
    your_score="Goals scored by you",
    opponent_score="Goals scored by your opponent",
)
async def report_match(
    interaction: discord.Interaction,
    opponent: discord.User,
    your_score: int,
    opponent_score: int,
):
    await interaction.response.defer()

    if interaction.user.id == opponent.id:
        await interaction.followup.send("❌ You cannot play against yourself.")
        return

    if your_score < 0 or opponent_score < 0:
        await interaction.followup.send("❌ Match scores cannot be negative.")
        return

    p1 = conn.execute("SELECT * FROM players WHERE user_id = ?", (interaction.user.id,)).fetchone()
    p2 = conn.execute("SELECT * FROM players WHERE user_id = ?", (opponent.id,)).fetchone()

    if not p1 or not p2:
        await interaction.followup.send("❌ Both users must be registered before reporting a match.")
        return

    if your_score > opponent_score:
        p1_points, p1_w, p1_d, p1_l = 3, 1, 0, 0
        p2_points, p2_w, p2_d, p2_l = 0, 0, 0, 1
    elif your_score < opponent_score:
        p1_points, p1_w, p1_d, p1_l = 0, 0, 0, 1
        p2_points, p2_w, p2_d, p2_l = 3, 1, 0, 0
    else:
        p1_points, p1_w, p1_d, p1_l = 1, 0, 1, 0
        p2_points, p2_w, p2_d, p2_l = 1, 0, 1, 0

    conn.execute(
        """
        UPDATE players
        SET played = played + 1,
            won = won + ?,
            drawn = drawn + ?,
            lost = lost + ?,
            goals_for = goals_for + ?,
            goals_against = goals_against + ?,
            points = points + ?
        WHERE user_id = ?
        """,
        (p1_w, p1_d, p1_l, your_score, opponent_score, p1_points, interaction.user.id),
    )
    conn.execute(
        """
        UPDATE players
        SET played = played + 1,
            won = won + ?,
            drawn = drawn + ?,
            lost = lost + ?,
            goals_for = goals_for + ?,
            goals_against = goals_against + ?,
            points = points + ?
        WHERE user_id = ?
        """,
        (p2_w, p2_d, p2_l, opponent_score, your_score, p2_points, opponent.id),
    )
    conn.commit()

    embed = create_league_embed("📊 Match Result Recorded!", discord.Color.gold())
    embed.add_field(name=f"{p1['ign']} ({p1['team_name']})", value=f"**{your_score}**", inline=True)
    embed.add_field(name="VS", value="-", inline=True)
    embed.add_field(name=f"{p2['ign']} ({p2['team_name']})", value=f"**{opponent_score}**", inline=True)
    await interaction.followup.send(embed=embed)


@bot.tree.command(name="standings", description="View the current league standings table.")
async def standings(interaction: discord.Interaction):
    await interaction.response.defer()

    rows = conn.execute(
        """
        SELECT ign, team_name, played, won, drawn, lost,
               (goals_for - goals_against) AS gd,
               points
        FROM players
        ORDER BY points DESC, gd DESC, won DESC, ign ASC
        """
    ).fetchall()

    if not rows:
        await interaction.followup.send("No players are registered yet.")
        return

    table_lines = [
        "```",
        f"{'#':<3} {'Player':<14} {'Team':<28} {'P':<3} {'W':<3} {'D':<3} {'L':<3} {'GD':<4} {'PTS':<4}",
        "-" * 80,
    ]

    for index, row in enumerate(rows, 1):
        team_name = row["team_name"] or "Unassigned"
        table_lines.append(
            f"{index:<3} {row['ign'][:14]:<14} {team_name[:28]:<28} {row['played']:<3} {row['won']:<3} {row['drawn']:<3} {row['lost']:<3} {row['gd']:<4} {row['points']:<4}"
        )

    table_lines.append("```")
    embed = create_league_embed("🏆 Vleague Standings", discord.Color.gold())
    embed.description = "\n".join(table_lines)
    await interaction.followup.send(embed=embed)


if __name__ == "__main__":
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Add it to your environment before running the bot.")
    bot.run(BOT_TOKEN)
