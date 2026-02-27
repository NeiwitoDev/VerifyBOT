import discord
from discord.ext import commands
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
CANAL_BIENVENIDAS = 123456789012345678  # ⚠ PON AQUÍ EL ID DEL CANAL DE BIENVENIDA

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
    print(f"✅ Bot conectado como {bot.user}")

# =========================
# BIENVENIDA AUTOMÁTICA
# =========================

@bot.event
async def on_member_join(member):

    canal = member.guild.get_channel(CANAL_BIENVENIDAS)

    if canal is None:
        print("❌ Canal de bienvenida no encontrado.")
        return

    embed = discord.Embed(
        title=f"🎉 ¡Bienvenid@ {member.name}!",
        description=(
            f"¡Bienvenid@ {member.mention} a **{member.guild.name}**!\n\n"
            "Para verificarte ve al canal <#1467928293587026194>\n"
            "Si No sabes como verificarte ve a <#1476952356288462868>\n"
            "Si tienes problemas con la verificacion abre ticket en <#1466240677607244012> "
            "y el <@&1473679599991783586> te ayudara.\n"
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
# COMANDO PANEL
# =========================

@bot.command()
@commands.has_permissions(administrator=True)
async def verify_panel(ctx):

    embed = discord.Embed(
        title="🔐 Panel de Verificación — VCP Villa Carlos Paz RP",
        description=(
            "¡Bienvenido al panel de verificaciones!\n\n"
            'Ve a <#1476952356288462868> si necesitas ayuda con la verificación.\n\n'
            "¿Tienes un problema con la verificación?\n"
            'Abre ticket en <#1466240677607244012>\n'
            "El <@&1473679599991783586> te ayudará."
        ),
        color=0x111214
    )

    embed.set_footer(text="Villa Carlos Paz RP • Sistema Oficial V.1")

    view = VerifyView()
    await ctx.send(embed=embed, view=view)

# =========================
# BOTÓN
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
        label="Ingresa tu nombre de usuario de Roblox",
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

        view = ConfirmView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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
            await interaction.response.send_message(
                "❌ No tienes verificación activa.",
                ephemeral=True
            )
            return

        username = data["username"]
        code = data["code"]

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://users.roblox.com/v1/usernames/users",
                json={"usernames": [username], "excludeBannedUsers": False}
            ) as resp:

                if resp.status != 200:
                    await interaction.response.send_message(
                        "❌ Error al contactar Roblox.",
                        ephemeral=True
                    )
                    return

                result = await resp.json()

        if not result["data"]:
            await interaction.response.send_message(
                "❌ Usuario no encontrado.",
                ephemeral=True
            )
            return

        user_id = result["data"][0]["id"]

        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://users.roblox.com/v1/users/{user_id}"
            ) as resp:
                profile = await resp.json()

        description = profile.get("description", "")

        if code not in description:
            await interaction.response.send_message(
                "❌ El código no fue encontrado en tu biografía.",
                ephemeral=True
            )
            return

        role = interaction.guild.get_role(ROL_VERIFICADO)

        if role is None:
            await interaction.response.send_message(
                "❌ No se encontró el rol configurado.",
                ephemeral=True
            )
            return

        await interaction.user.add_roles(role)

        embed = discord.Embed(
            title="✅ Verificación Exitosa",
            description=(
                f"👤 Usuario: **{username}**\n"
                f"🆔 ID: **{user_id}**\n\n"
                "Bienvenido a Villa Carlos Paz RP."
            ),
            color=0x2ecc71
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

        verification_codes.pop(interaction.user.id, None)

# =========================
# RUN
# =========================

bot.run(TOKEN)
