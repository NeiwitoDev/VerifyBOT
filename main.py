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
# BIENVENIDA (COMO EN TU IMAGEN)
# =========================

@bot.event
async def on_member_join(member):

    canal = member.guild.get_channel(CANAL_BIENVENIDAS)
    if canal is None:
        return

    embed = discord.Embed(
        title=f"🎉 ¡Bienvenid@ {member.name}!",
        description=(
            f"¡Bienvenid@ {member.mention} a **[VCP] Villa Carlos Paz RP | Beta!**\n\n"
            "Para verificarte ve al canal <#1467928293587026194>\n"
            "Si No sabes como verificarte ve a <#1476952356288462868>\n"
            "Si tienes problemas con la verificacion abre ticket en <#1466240677607244012> "
            "y el <@&1473679599991783586> te ayudara.\n\n"
            "¡Disfruta de tu estadia!\n\n"
            "**Tambien te recomendamos visitar estos canales:**\n"
            "<#1466215119372554260>\n"
            "<#1466216894242492436>\n"
            "<#1466229592858558565>\n"
            "<#1466240677607244012>"
        ),
        color=0x2ecc71
    )

    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Ahora contamos con {member.guild.member_count} miembros")

    await canal.send(embed=embed)

# =========================
# COMANDO !verify-panel
# =========================

@bot.command(name="verify-panel")
@commands.has_permissions(administrator=True)
async def verify_panel(ctx):

    embed = discord.Embed(
        title="🔐 Panel de Verificación — VCP Villa Carlos Paz RP",
        description=(
            "¡Bienvenido al sistema oficial de verificación!\n\n"
            "Presiona el botón para comenzar el proceso.\n"
            "Coloca el código en tu biografía de Roblox y confirma.\n\n"
            "Si tienes problemas abre ticket."
        ),
        color=0x111214
    )

    embed.set_footer(text="Sistema Oficial VCP RP • Verificación Roblox")

    await ctx.send(embed=embed, view=VerifyView())

# =========================
# BOTÓN VERIFICACIÓN
# =========================

class VerifyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verificarse", style=discord.ButtonStyle.green, emoji="✅")
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(VerifyModal())

# =========================
# MODAL
# =========================

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
                "Luego presiona **Confirmar Verificación**."
            ),
            color=0xf1c40f
        )

        await interaction.response.send_message(embed=embed, view=ConfirmView(), ephemeral=True)

# =========================
# CONFIRMAR
# =========================

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
                result = await resp.json()

        if not result["data"]:
            await interaction.response.send_message("❌ Usuario no encontrado.", ephemeral=True)
            return

        user_id = result["data"][0]["id"]

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://users.roblox.com/v1/users/{user_id}") as resp:
                profile = await resp.json()

        if code not in profile.get("description", ""):
            await interaction.response.send_message("❌ Código no encontrado en tu biografía.", ephemeral=True)
            return

        role = interaction.guild.get_role(ROL_VERIFICADO)
        await interaction.user.add_roles(role)

        embed = discord.Embed(
            title="✅ Verificación Exitosa",
            description=f"👤 Usuario: **{username}**\n🆔 ID: **{user_id}**\n\nBienvenido a VCP RP.",
            color=0x2ecc71
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
        verification_codes.pop(interaction.user.id, None)

# =========================
# SLASH COMMAND ALERTA (MEJORADO)
# =========================

@bot.tree.command(name="alerta", description="Cambiar nivel de alerta del servidor")
@app_commands.describe(nivel="Verde, Amarilla o Roja")
async def alerta(interaction: discord.Interaction, nivel: str):

    if not any(role.id == ROL_ALERTA for role in interaction.user.roles):
        await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)
        return

    nivel = nivel.lower()

    if nivel not in ["verde", "amarilla", "roja"]:
        await interaction.response.send_message("❌ Usa: Verde, Amarilla o Roja.", ephemeral=True)
        return

    if nivel == "verde":
        color = 0x2ecc71
        titulo = "🟢 ESTADO DE ALERTA VERDE"
        descripcion = (
            "La ciudad se encuentra en estado normal.\n\n"
            "✔ Patrullaje habitual\n"
            "✔ Operativos estándar\n"
            "✔ Sin amenazas activas\n\n"
            "Las fuerzas policiales operan con normalidad."
        )

    elif nivel == "amarilla":
        color = 0xf1c40f
        titulo = "🟡 ESTADO DE ALERTA AMARILLA"
        descripcion = (
            "Se detectaron situaciones sospechosas.\n\n"
            "⚠ Patrullaje reforzado\n"
            "⚠ Oficiales en máxima atención\n"
            "🔫 Armamento intermedio autorizado\n\n"
            "Se recomienda precaución."
        )

    else:
        color = 0xe74c3c
        titulo = "🔴 ESTADO DE ALERTA ROJA"
        descripcion = (
            "La ciudad se encuentra en estado crítico.\n\n"
            "🔥 Amenaza activa confirmada\n"
            "🚨 Operativos especiales activos\n"
            "🔫 Armamento pesado autorizado\n\n"
            "Todas las unidades deben responder inmediatamente."
        )

    embed = discord.Embed(title=titulo, description=descripcion, color=color)
    embed.set_footer(text=f"Activado por {interaction.user}", icon_url=interaction.user.display_avatar.url)
    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)

    await interaction.response.send_message(embed=embed)

# =========================
# RUN
# =========================

bot.run(TOKEN)
