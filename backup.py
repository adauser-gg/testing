import discord
from discord.ext import commands
import asyncio
import os
import time
from discord import app_commands
import re
import random

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

# LOCAL TEST SETUP: It tries to get the environment variable first.
# If it fails, you can paste your token directly in the quotes below.
# ⚠️ WARNING: Never upload the script to GitHub or Render with your token hardcoded!
token = os.getenv("DISCORD_TOKEN") or "PASTE_YOUR_BOT_TOKEN_HERE"

# --- CUSTOM PREFIX HANDLER (Fixes Case Sensitivity) ---
def get_custom_prefix(bot, message):
    # If the message starts with "raga " in ANY case combination (RAGA, rAgA, RaGa)
    if message.content.lower().startswith("raga "):
        # Return the exact casing the user typed so discord.py can strip it properly
        return message.content[:5] 
    return "raga " # Default fallback

bot = commands.Bot(command_prefix=get_custom_prefix, intents=intents, case_insensitive=True)

# --- CONFIGURATION ---
ROLE_LIMITS = {1369029597735292978: 3}
ADMIN_ROLE_ID = 1371873206935490691
MAIN_ACCOUNT_ID = 961628205964476467

# --- BOT MEMORY ---
# --- BOT MEMORY ---
afk_users = {}        # Format: {guild_id: {user_id: "reason"}}
rafk_users = {}       # Format: {guild_id: {user_id: "reason"}}
global_afk_users = {} # Format: {user_id: "reason"}
global_rafk_users = {}# Format: {user_id: "reason"}

AUTHORIZED_USER_IDS = [
    961628205964476467,  # Main Account
    1448998798918684743,  # Alt Account
    1414246186612686979,
    1499695474494410754,
    1419435870938861568,
]

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print(f'Bot is active. Authorized users: {len(AUTHORIZED_USER_IDS)}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s).")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

# --- FEATURE 1: ROLE ENFORCER ---
@bot.event
async def on_member_update(before, after):
    if len(after.roles) > len(before.roles):
        new_roles = [r for r in after.roles if r not in before.roles]
        for role in new_roles:
            if role.id in ROLE_LIMITS:
                if len(role.members) > ROLE_LIMITS[role.id]:
                    await asyncio.sleep(0.6)
                    is_authorized = False
                    try:
                        async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=5):
                            if entry.target.id == after.id:
                                if entry.user.id in AUTHORIZED_USER_IDS:
                                    print(f"[BYPASS] Authorized user {entry.user.name} ignored limit.")
                                    is_authorized = True
                                    break
                    except discord.Forbidden:
                        print("Bot needs 'View Audit Log' permission!")

                    if not is_authorized:
                        print(f"[REMOVED] Role {role.name} stripped from {after.name}.")
                        await after.remove_roles(role)

# --- FEATURE 2: THE STEALTH TRACKER ---
TARGET_USER_ID = 1499695474494410754  # Replace with the actual ID you want to track
last_notified = {}

@bot.event
async def on_presence_update(before, after):
    if after.id == TARGET_USER_ID:
        if before.status == discord.Status.offline and after.status != discord.Status.offline:
            current_time = int(time.time())
            last_time = last_notified.get(after.id, 0)
            if current_time - last_time < 60:
                return
            last_notified[after.id] = current_time

            my_account = bot.get_user(MAIN_ACCOUNT_ID) or await bot.fetch_user(MAIN_ACCOUNT_ID)
            if my_account:
                try:
                    message = f"👀 Heads up: **{after.display_name}** just came online at <t:{current_time}:f> (<t:{current_time}:R>)!"
                    await my_account.send(message)
                except discord.Forbidden:
                    print("Couldn't send DM.")

# --- FEATURE 3 & 7: UNIFIED MESSAGE HANDLER (BACKDOOR, DM FORWARDER, AFK) ---
@bot.event
async def on_message(message):
    # Completely ignore all messages from bots
    if message.author.bot:
        return

    user_id = message.author.id
    guild_id = message.guild.id if message.guild else None

    # --- AFK CHECK 1: Remove AFK if the user speaks ---
    removed_afk = False
    if user_id in global_afk_users:
        global_afk_users.pop(user_id)
        removed_afk = True
    elif guild_id and guild_id in afk_users and user_id in afk_users[guild_id]:
        afk_users[guild_id].pop(user_id)
        removed_afk = True

    if removed_afk:
        try:
            await message.channel.send(f"👋 Welcome back {message.author.mention}! Your AFK status has been removed.")
        except discord.Forbidden:
            pass

    removed_rafk = False
    if user_id in global_rafk_users:
        global_rafk_users.pop(user_id)
        removed_rafk = True
    elif guild_id and guild_id in rafk_users and user_id in rafk_users[guild_id]:
        rafk_users[guild_id].pop(user_id)
        removed_rafk = True

    if removed_rafk:
        try:
            await message.author.send("👋 Your Stealth RAFK status has been removed because you typed a message.")
        except discord.Forbidden:
            pass

    # --- AFK CHECK 2: Reply if someone mentions an AFK user ---
    if message.guild:
        for mention in message.mentions:
            # Normal AFK
            afk_reason = global_afk_users.get(mention.id) or afk_users.get(message.guild.id, {}).get(mention.id)
            if afk_reason:
                try:
                    await message.channel.send(f"💤 **{mention.display_name}** is currently AFK.")
                    await message.channel.send(afk_reason)
                except discord.Forbidden:
                    pass
            # Stealth RAFK
            rafk_reason = global_rafk_users.get(mention.id) or rafk_users.get(message.guild.id, {}).get(mention.id)
            if rafk_reason:
                try:
                    await message.reply(rafk_reason)
                except discord.Forbidden:
                    pass

    # --- DM Forwarder ---
    if not message.guild:
        if message.author.id != MAIN_ACCOUNT_ID:
            my_account = bot.get_user(MAIN_ACCOUNT_ID) or await bot.fetch_user(MAIN_ACCOUNT_ID)
            if my_account:
                content = f"\n> {message.content}" if message.content else ""
                attachment_urls = "\n".join([attachment.url for attachment in message.attachments])
                if attachment_urls:
                    content += f"\n\n🔗 **Attachments:**\n{attachment_urls}"
                log_msg = f"📥 **Incoming DM from {message.author.display_name}:**{content}"
                try:
                    await my_account.send(log_msg)
                except discord.Forbidden:
                    pass
        await bot.process_commands(message)
        return

    # --- Server Backdoor ---
    if message.content.lower() == "raga":
        await message.reply("https://cdn.discordapp.com/emojis/1477267884194398288.webp?size=160&animated=true")
        return

    if message.author.id in AUTHORIZED_USER_IDS:
        admin_role = message.guild.get_role(ADMIN_ROLE_ID)
        if message.content.lower() == "raga cape on":
            if admin_role not in message.author.roles:
                await message.author.add_roles(admin_role)
            try:
                await message.delete()
            except:
                pass
        elif message.content.lower() == "raga cape off":
            if admin_role in message.author.roles:
                await message.author.remove_roles(admin_role)
            try:
                await message.delete()
            except:
                pass

    await bot.process_commands(message)

# --- FEATURE 11: DM-COMPATIBLE RPS GAME ---
class RPSView(discord.ui.View):
    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=120.0)
        self.player1 = player1
        self.player2 = player2
        self.p1_choice = None
        self.p2_choice = None

    async def check_both_played(self, interaction: discord.Interaction):
        if self.p1_choice == self.p2_choice:
            result = "It's a tie! 🤝"
        elif (self.p1_choice == "🪨" and self.p2_choice == "✂️") or \
             (self.p1_choice == "📄" and self.p2_choice == "🪨") or \
             (self.p1_choice == "✂️" and self.p2_choice == "📄"):
            result = f"👑 **{self.player1.display_name}** wins!"
        else:
            result = f"👑 **{self.player2.display_name}** wins!"

        final_message = (f"🎮 **Rock Paper Scissors Results!**\n\n"
                         f"**{self.player1.display_name}:** {self.p1_choice}\n"
                         f"**{self.player2.display_name}:** {self.p2_choice}\n\n"
                         f"> {result}")

        self.clear_items()
        rematch_btn = discord.ui.Button(label="Play Again", style=discord.ButtonStyle.success, emoji="🔄")

        async def rematch_callback(btn_interaction: discord.Interaction):
            if btn_interaction.user.id not in [self.player1.id, self.player2.id]:
                await btn_interaction.response.send_message("❌ You aren't playing this match!", ephemeral=True)
                return
            new_view = RPSView(self.player1, self.player2)
            msg = (f"🎮 **Rock Paper Scissors REMATCH!**\n"
                   f"**{self.player1.display_name}** vs **{self.player2.display_name}**\n\n"
                   f"Click a button below to lock in.")
            await btn_interaction.response.send_message(msg, view=new_view)

        rematch_btn.callback = rematch_callback
        self.add_item(rematch_btn)
        await interaction.response.edit_message(content=final_message, view=self)

    async def handle_click(self, interaction: discord.Interaction, choice: str):
        if interaction.user.id not in [self.player1.id, self.player2.id]:
            await interaction.response.send_message("❌ You aren't playing this match!", ephemeral=True)
            return

        if interaction.user.id == self.player1.id:
            if self.p1_choice:
                await interaction.response.send_message("You already locked in your choice!", ephemeral=True)
                return
            self.p1_choice = choice
        else:
            if self.p2_choice:
                await interaction.response.send_message("You already locked in your choice!", ephemeral=True)
                return
            self.p2_choice = choice

        if self.p1_choice and self.p2_choice:
            await self.check_both_played(interaction)
        else:
            waiting_msg = (f"🎮 **Rock Paper Scissors!**\n"
                           f"**{self.player1.display_name}** vs **{self.player2.display_name}**\n\n"
                           f"🔒 One player has locked in their choice! Waiting for the other...")
            await interaction.response.edit_message(content=waiting_msg, view=self)

    @discord.ui.button(label="Rock", emoji="🪨", style=discord.ButtonStyle.secondary)
    async def btn_rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, "🪨")

    @discord.ui.button(label="Paper", emoji="📄", style=discord.ButtonStyle.secondary)
    async def btn_paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, "📄")

    @discord.ui.button(label="Scissors", emoji="✂️", style=discord.ButtonStyle.secondary)
    async def btn_scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_click(interaction, "✂️")

# --- FEATURE 14: DM-COMPATIBLE RUSSIAN ROULETTE ---
class RouletteView(discord.ui.View):
    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=300.0)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.chambers = [True, False, False, False, False, False]
        random.shuffle(self.chambers)
        self.current_chamber = 0

    @discord.ui.button(label="Pull Trigger", emoji="🔫", style=discord.ButtonStyle.danger)
    async def pull_trigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.player1.id, self.player2.id]:
            await interaction.response.send_message("❌ Step back. You aren't playing.", ephemeral=True)
            return
        if interaction.user.id != self.current_player.id:
            await interaction.response.send_message("⏳ Hold your horses! It's not your turn.", ephemeral=True)
            return

        is_bullet = self.chambers[self.current_chamber]
        self.current_chamber += 1

        if is_bullet:
            winner = self.player2 if self.current_player == self.player1 else self.player1
            button.disabled = True
            button.label = "BANG!"
            button.style = discord.ButtonStyle.secondary
            msg = (f"💥 **BANG!** 💥\n\n"
                   f"**{self.current_player.display_name}** pulled the trigger and found the bullet...\n"
                   f"👑 **{winner.display_name}** survives and wins the game!")
            await interaction.response.edit_message(content=msg, view=self)
            self.stop()
        else:
            self.current_player = self.player2 if self.current_player == self.player1 else self.player1
            chambers_left = 6 - self.current_chamber
            msg = (f"🎯 **Russian Roulette**\n\n"
                   f"**{interaction.user.display_name}** holds the gun to their head and pulls...\n"
                   f"*Click.* It's empty. They survive.\n\n"
                   f"👉 **{self.current_player.display_name}**, the gun is handed to you. There are **{chambers_left}** chambers left.")
            await interaction.response.edit_message(content=msg, view=self)

# --- COMMANDS ---

@bot.command(name="humble")
async def humble(ctx, *, search_query: str):
    if ctx.author.id not in AUTHORIZED_USER_IDS:
        return
    query = search_query.lower()
    matches = []
    for member in ctx.guild.members:
        if query in member.display_name.lower() or query in member.name.lower():
            if not member.bot:
                matches.append(member)

    target_user = None
    if not matches:
        await ctx.send(f"❌ No user found matching `{search_query}`.")
        return
    if len(matches) == 1:
        target_user = matches[0]
    else:
        options_text = "\n".join([f"**{i + 1}.** {m.display_name} (`{m.name}`)" for i, m in enumerate(matches[:5])])
        selection_msg = await ctx.send(f"🤔 Multiple users found. Reply with the **number** (1-{len(matches[:5])}):\n{options_text}")
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
        try:
            response = await bot.wait_for('message', check=check, timeout=15.0)
            index = int(response.content) - 1
            if 0 <= index < len(matches):
                target_user = matches[index]
                await response.delete()
                await selection_msg.delete()
            else:
                await ctx.send("❌ Invalid selection.")
                return
        except asyncio.TimeoutError:
            await selection_msg.edit(content="⏰ Selection timed out.")
            return

    if target_user:
        humble_gif = "https://tenor.com/view/megumi-fushiguro-fushi-guro-megumi-fushiguro-mahoraga-gif-92941122665464082"
        await ctx.send(f"{target_user.mention} stay humble.")
        await ctx.send(humble_gif)

@bot.tree.command(name="whisper", description="Secretly make the bot say something in the channel")
@app_commands.describe(message="What do you want the bot to say?")
async def whisper(interaction: discord.Interaction, message: str):
    if interaction.user.id not in AUTHORIZED_USER_IDS:
        await interaction.response.send_message("❌ You aren't authorized to use this.", ephemeral=True)
        return
    await interaction.channel.send(message)
    await interaction.response.send_message("🤫 Message sent.", ephemeral=True)
    if interaction.user.id != MAIN_ACCOUNT_ID:
        my_account = bot.get_user(MAIN_ACCOUNT_ID) or await bot.fetch_user(MAIN_ACCOUNT_ID)
        if my_account:
            location = interaction.channel.mention if interaction.guild else "Direct Messages"
            log_msg = f"🗣️ **Stealth Whisper Log:**\n**{interaction.user.display_name}** used `/whisper` in {location}:\n> {message}"
            try:
                await my_account.send(log_msg)
            except discord.Forbidden:
                pass

@bot.tree.command(name="dm_user", description="Secretly send a DM to a user via the bot")
@app_commands.describe(user_id="Paste the User ID of your target", message="What should the bot say?")
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def dm_user(interaction: discord.Interaction, user_id: str, message: str):
    if interaction.user.id not in AUTHORIZED_USER_IDS:
        await interaction.response.send_message("❌ You aren't authorized to use this.", ephemeral=True)
        return
    try:
        target_id = int(user_id)
        target = bot.get_user(target_id) or await bot.fetch_user(target_id)
    except ValueError:
        await interaction.response.send_message("❌ Invalid ID. Please paste a valid User ID (numbers only).", ephemeral=True)
        return
    except discord.NotFound:
        await interaction.response.send_message("❌ User not found. Make sure the bot shares a server with them.", ephemeral=True)
        return

    try:
        await target.send(message)
        await interaction.response.send_message(f"🤫 Successfully DM'd {target.display_name}.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message(f"❌ Could not DM {target.display_name}. Their DMs are closed.", ephemeral=True)
        return

    if interaction.user.id != MAIN_ACCOUNT_ID:
        my_account = bot.get_user(MAIN_ACCOUNT_ID) or await bot.fetch_user(MAIN_ACCOUNT_ID)
        if my_account:
            log_msg = f"🕵️ **Stealth DM Log:**\n**{interaction.user.display_name}** used `/dm_user` to message **{target.display_name}**:\n> {message}"
            try:
                await my_account.send(log_msg)
            except discord.Forbidden:
                pass

@bot.tree.command(name="afk", description="Set your status to AFK so the bot can reply for you")
@app_commands.describe(reason="Why are you AFK?", is_global="Set to True to be AFK in ALL servers")
async def afk(interaction: discord.Interaction, reason: str = "AFK", is_global: bool = False):
    if interaction.user.id not in AUTHORIZED_USER_IDS:
        await interaction.response.send_message("❌ Not authorized.", ephemeral=True)
        return
    
    if interaction.guild:
        def replace_emoji(match):
            custom_emoji = discord.utils.get(interaction.guild.emojis, name=match.group(1)) if match.group(1) else None
            return str(custom_emoji) if custom_emoji else match.group(0)
        reason = re.sub(r'<a?:[a-zA-Z0-9_]+:[0-9]+>|:([a-zA-Z0-9_]+):', replace_emoji, reason)

    if is_global:
        global_afk_users[interaction.user.id] = reason
        scope = "Globally"
    else:
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id:
            if guild_id not in afk_users: afk_users[guild_id] = {}
            afk_users[guild_id][interaction.user.id] = reason
            scope = f"in **{interaction.guild.name}**"
        else:
            global_afk_users[interaction.user.id] = reason
            scope = "Globally (DM)"

    await interaction.response.send_message(f"💤 **{interaction.user.display_name}** is now AFK {scope}.")
    await interaction.channel.send(reason)

@bot.command(name="afk")
async def prefix_afk(ctx, *, reason: str = "AFK"):
    if ctx.author.id not in AUTHORIZED_USER_IDS: return

    is_global = reason.lower().startswith("global")
    if is_global:
        reason = reason[6:].strip() or "AFK"

    if ctx.guild:
        def replace_emoji(match):
            custom_emoji = discord.utils.get(ctx.guild.emojis, name=match.group(1)) if match.group(1) else None
            return str(custom_emoji) if custom_emoji else match.group(0)
        reason = re.sub(r'<a?:[a-zA-Z0-9_]+:[0-9]+>|:([a-zA-Z0-9_]+):', replace_emoji, reason)

    if is_global:
        global_afk_users[ctx.author.id] = reason
        scope = "Globally"
    else:
        if ctx.guild:
            if ctx.guild.id not in afk_users: afk_users[ctx.guild.id] = {}
            afk_users[ctx.guild.id][ctx.author.id] = reason
            scope = f"in **{ctx.guild.name}**"
        else:
            global_afk_users[ctx.author.id] = reason
            scope = "Globally (DM)"

    await ctx.send(f"💤 **{ctx.author.display_name}** is now AFK {scope}.")
    await ctx.send(reason)

@bot.command(name="rafk")
async def prefix_rafk(ctx, *, reason: str = "AFK"):
    if ctx.author.id not in AUTHORIZED_USER_IDS: return
    try: await ctx.message.delete()
    except discord.Forbidden: pass

    is_global = reason.lower().startswith("global")
    if is_global:
        reason = reason[6:].strip() or "AFK"

    if ctx.guild:
        def replace_emoji(match):
            custom_emoji = discord.utils.get(ctx.guild.emojis, name=match.group(1)) if match.group(1) else None
            return str(custom_emoji) if custom_emoji else match.group(0)
        reason = re.sub(r'<a?:[a-zA-Z0-9_]+:[0-9]+>|:([a-zA-Z0-9_]+):', replace_emoji, reason)

    if is_global:
        global_rafk_users[ctx.author.id] = reason
    else:
        if ctx.guild:
            if ctx.guild.id not in rafk_users: rafk_users[ctx.guild.id] = {}
            rafk_users[ctx.guild.id][ctx.author.id] = reason
        else:
            global_rafk_users[ctx.author.id] = reason

@bot.tree.command(name="rafk", description="Stealth AFK: Bot only replies with your reason")
@app_commands.describe(reason="What should the bot reply with?", is_global="Set to True to be AFK in ALL servers")
async def slash_rafk(interaction: discord.Interaction, reason: str = "AFK", is_global: bool = False):
    if interaction.user.id not in AUTHORIZED_USER_IDS:
        await interaction.response.send_message("❌ Not authorized.", ephemeral=True)
        return
    
    if interaction.guild:
        def replace_emoji(match):
            custom_emoji = discord.utils.get(interaction.guild.emojis, name=match.group(1)) if match.group(1) else None
            return str(custom_emoji) if custom_emoji else match.group(0)
        reason = re.sub(r'<a?:[a-zA-Z0-9_]+:[0-9]+>|:([a-zA-Z0-9_]+):', replace_emoji, reason)

    if is_global:
        global_rafk_users[interaction.user.id] = reason
    else:
        guild_id = interaction.guild.id if interaction.guild else None
        if guild_id:
            if guild_id not in rafk_users: rafk_users[guild_id] = {}
            rafk_users[guild_id][interaction.user.id] = reason
        else:
            global_rafk_users[interaction.user.id] = reason

    await interaction.response.send_message("🤫 Stealth RAFK activated.", ephemeral=True)

@bot.tree.command(name="rps", description="Challenge a friend to Rock, Paper, Scissors!")
@app_commands.describe(opponent="Who do you want to play against?")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def rps(interaction: discord.Interaction, opponent: discord.User):
    if opponent.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't play against yourself!", ephemeral=True)
        return
    if opponent.bot:
        await interaction.response.send_message("❌ Bots always pick Rock. Pick a human instead.", ephemeral=True)
        return
    view = RPSView(player1=interaction.user, player2=opponent)
    msg = (f"🎮 **Rock Paper Scissors!**\n"
           f"**{interaction.user.display_name}** challenged **{opponent.display_name}**!\n\n"
           f"Click a button below to secretly lock in your choice.")
    await interaction.response.send_message(msg, view=view)

@bot.tree.command(name="roulette", description="Challenge a friend to a deadly game of Russian Roulette!")
@app_commands.describe(opponent="Who are you handing the gun to?")
@app_commands.allowed_installs(guilds=True, users=True)
@app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
async def roulette(interaction: discord.Interaction, opponent: discord.User):
    if opponent.id == interaction.user.id:
        await interaction.response.send_message("❌ You can't play against yourself. Call a hotline instead.", ephemeral=True)
        return
    if opponent.bot:
        await interaction.response.send_message("❌ Bots are made of metal. Bullets don't hurt them. Pick a human.", ephemeral=True)
        return
    view = RouletteView(player1=interaction.user, player2=opponent)
    msg = (f"🎯 **Russian Roulette**\n\n"
           f"**{interaction.user.display_name}** challenged **{opponent.display_name}**!\n"
           f"A 6-shooter is loaded with 1 bullet. The cylinder is spun.\n\n"
           f"👉 **{interaction.user.display_name}**, you go first. Pick up the gun and pull the trigger.")
    await interaction.response.send_message(msg, view=view)

# --- SILENCE ERRORS ---
from discord.ext.commands import CommandNotFound
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error

# --- RUN BOT ---
bot.run(token)
