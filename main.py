import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import random
import aiohttp

# =========================
# CARGAR TOKEN
# =========================

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("No se encontró el TOKEN en el archivo .env")

# =========================
# CONFIGURACIÓN
# =========================

ROL_VERIFICADO = 1467926654880846168
CANAL_BIENVENIDAS = 1466215432418492416
ROL_ALERTA = 1466440467204800597

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

verification_codes = {}

# =========================
# READY
# =========================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Bot conectado como {bot.user}")

# =========================
# BIENVENIDA
# =========================

@bot.event
async def on_member_join(member):

    canal = member.guild.get_channel(CANAL_BIENVENIDAS)

    if canal is None:
        return

    embed = discord.Embed(
        title=f"🎉 ¡Bienvenid@ {member.name}!",
        description=(
            f"Bienvenid@ {member.mention} a **{member.guild.name}**\n\n"
            "Para verificarte usa el panel correspondiente.\n"
            "Si tienes problemas abre ticket."
        ),
        color=0x2ecc71
    )

    embed.set_thumbnail(url=member.display_avatar.url)
    await canal.send(embed=embed)

# =========================
# PANEL VERIFICACIÓN
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def verify_panel(ctx):

    embed = discord.Embed(
        title="🔐 Panel de Verificación — VCP RP",
        description="Presiona el botón para comenzar tu verificación.",
        color=0x111214
    )

    await ctx.send(embed=embed, view=VerifyView())

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verificarse", style=discord.ButtonStyle.green, emoji="✅")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

class VerifyModal(discord.ui.Modal, title="Verificación Roblox - VCP"):

    username = discord.ui.TextInput(
        label="Ingresa tu usuario de Roblox",
        placeholder="Ejemplo: Braill_x",
        required=True,
        max_length=30
    )

    async def on_submit(self, interaction: discord.Interaction):

        code = f"VCP-{random.randint(10000,99999)}"

        verification_codes[interaction.user.id] = {
            "username": self.username.value,
            "code": code
        }

        embed = discord.Embed(
            title="📌 Último Paso",
            description=(
                f"Coloca este código en tu biografía de Roblox:\n\n"
                f"```{code}```\n\n"
                "Luego presiona confirmar."
            ),
            color=0xf1c40f
        )

        await interaction.response.send_message(
            embed=embed,
            view=ConfirmView(),
            ephemeral=True
        )

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(label="Confirmar Verificación", style=discord.ButtonStyle.blurple)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        data = verification_codes.get(interaction.user.id)

        if not data:
            await interaction.response.send_message("❌ No tienes verificación activa.", ephemeral=True)
            return

        username = data["username"]
        code = data["code"]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://users.roblox.com/v1/usernames/users",
                json={"usernames": [username], "excludeBannedUsers": False}
            ) as resp:

                if resp.status != 200:
                    await interaction.response.send_message("❌ Error con Roblox.", ephemeral=True)
                    return

                result = await resp.json()

        if not result["data"]:
            await interaction.response.send_message("❌ Usuario no encontrado.", ephemeral=True)
            return

        user_id = result["data"][0]["id"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://users.roblox.com/v1/users/{user_id}"
            ) as resp:
                profile = await resp.json()

        description = profile.get("description", "")

        if code not in description:
            await interaction.response.send_message("❌ Código no encontrado en biografía.", ephemeral=True)
            return

        role = interaction.guild.get_role(ROL_VERIFICADO)

        if role is None:
            await interaction.response.send_message("❌ Rol no configurado.", ephemeral=True)
            return

        await interaction.user.add_roles(role)

        embed = discord.Embed(
            title="✅ Verificación Exitosa",
            description=f"Usuario **{username}** verificado correctamente.",
            color=0x2ecc71
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        verification_codes.pop(interaction.user.id, None)

# =========================
# COMANDO ALERTA
# =========================

@bot.tree.command(name="alerta", description="Establece el nivel de alerta del servidor RP")
@app_commands.describe(nivel="Verde, Amarilla o Roja")
async def alerta(interaction: discord.Interaction, nivel: str):

    if not any(role.id == ROL_ALERTA for role in interaction.user.roles):
        await interaction.response.send_message("❌ No tienes permiso.", ephemeral=True)
        return

    nivel = nivel.lower()

    if nivel not in ["verde", "amarilla", "roja"]:
        await interaction.response.send_message("❌ Usa: Verde, Amarilla o Roja.", ephemeral=True)
        return

    if nivel == "verde":
        color = 0x2ecc71
        titulo = "🟢 ALERTA VERDE"
        descripcion = "Ciudad en estado normal.\nPatrullaje habitual autorizado."

    elif nivel == "amarilla":
        color = 0xf1c40f
        titulo = "🟡 ALERTA AMARILLA"
        descripcion = "Situación preventiva.\nArmamento intermedio autorizado."

    else:
        color = 0xe74c3c
        titulo = "🔴 ALERTA ROJA"
        descripcion = "Estado crítico.\nArmamento pesado autorizado."

    embed = discord.Embed(title=titulo, description=descripcion, color=color)
    embed.set_footer(text="Sistema Oficial de Alertas VCP RP")

    await interaction.response.send_message(embed=embed)

# =========================
# RUN
# =========================

bot.run(TOKEN)
