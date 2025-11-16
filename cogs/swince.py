import asyncio
import discord
from discord.ext import commands
from utils.mentions import format_mentions, extract_mentions


class ConfirmView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.value = None

    @discord.ui.button(label="Oui", style=discord.ButtonStyle.green)
    async def yes_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Ceci n'est pas votre soumission!", ephemeral=True)
            return
        self.value = True
        self.stop()
        await interaction.response.defer()

    @discord.ui.button(label="Non", style=discord.ButtonStyle.red)
    async def no_button(self, button: discord.ui.Button, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Ceci n'est pas votre soumission!", ephemeral=True)
            return
        self.value = False
        self.stop()
        await interaction.response.defer()

class SwinceHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = set()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None:
            return

        video_attachments = [
            a for a in message.attachments
            if a.content_type and a.content_type.startswith("video")
        ]

        if len(video_attachments) != 1:
            return

        if message.author.id in self.sessions:
            await message.channel.send(
                f"{message.author.mention}, vous avez déjà une soumission active. Veuillez terminer ou attendre.",
                delete_after=10
            )
            return

        self.sessions.add(message.author.id)
        try:
            await self._handle_submission(message)
        finally:
            self.sessions.discard(message.author.id)

    async def _handle_submission(self, message):
        user = message.author
        channel = message.channel

        # Step 1: Initial confirmation
        embed = self._create_submission_embed(
            "**Cette vidéo est-elle une soumission de swince ?**"
        )
        status_msg = await message.reply(embed=embed, mention_author=False)

        if not await self._wait_for_confirmation(user, status_msg, embed):
            return

        # Main submission loop
        while True:
            # Step 2: Get present users
            embed = self._create_submission_embed(
                "**Merci de bien vouloir mentionner/taguer les personne(s) ayant effectué une swince**"
            )
            await status_msg.edit(embed=embed, view=None)

            present_users = await self._wait_for_mentions(user, channel, status_msg, embed)
            if present_users is None:
                return

            # Step 3: Get nominees
            present_text = format_mentions(present_users) or "..."
            embed = self._create_submission_embed(
                "**Merci de bien vouloir mentionner/taguer les personne(s) nominée(s)**",
                present_text=present_text
            )
            await status_msg.edit(embed=embed)

            nominees = await self._wait_for_mentions(user, channel, status_msg, embed)
            if nominees is None:
                return

            # Step 4: Review and confirm
            nominees_text = format_mentions(nominees) or "..."
            embed = self._create_submission_embed(
                "**Est-ce que les informations ci-dessous sont correctes ?**",
                present_text=present_text,
                nominees_text=nominees_text
            )
            await status_msg.edit(embed=embed)

            if await self._wait_for_confirmation(user, status_msg, embed):
                await self._finalize_submission(status_msg)
                break

    @staticmethod
    def _create_submission_embed(instruction, present_text="...", nominees_text="..."):
        """Create a submission embed with the given instruction and data."""
        description = (
            "Afin de pouvoir soumettre votre swince correctement et mettre à jour les **points** et "
            "les **nominations en cours**, merci de suivre les __instructions__ ci-dessous.\n\n"
            f"{instruction}\n\n"
            f"Personne(s) dans la vidéo\n> {present_text}\n\n"
            f"Personne(s) nominée(s)\n> {nominees_text}\n"
        )
        embed = discord.Embed(
            title="Soumission de Swince",
            description=description,
            color=0xFFFFFF
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2599/2599570.png")
        return embed

    async def _wait_for_confirmation(self, user, status_msg, embed, timeout=60):
        """Wait for button confirmation with countdown."""
        view = ConfirmView(user.id)
        embed.set_footer(
            text=f"Temps restant pour terminer la soumission : {timeout} secondes",
            icon_url="https://img.icons8.com/ios7/512/FFFFFF/clock--v3.png"
        )

        countdown_task = asyncio.create_task(
            self._update_countdown(status_msg, embed, view, timeout)
        )
        await status_msg.edit(embed=embed, view=view)
        await view.wait()
        countdown_task.cancel()

        embed.remove_footer()
        await status_msg.edit(embed=embed, view=None)

        if view.value is None:
            await self._show_timeout(status_msg, "Aucune confirmation reçue. Processus annulé.")

        return view.value

    async def _wait_for_mentions(self, user, channel, status_msg, embed, timeout=60):
        """Wait for a message with mentions with countdown."""
        def check(m):
            return m.author.id == user.id and m.channel == channel and m.mentions

        embed.set_footer(
            text=f"Temps restant pour terminer la soumission : {timeout} secondes",
            icon_url="https://img.icons8.com/ios7/512/FFFFFF/clock--v3.png"
        )

        countdown_task = asyncio.create_task(
            self._update_countdown(status_msg, embed, None, timeout)
        )

        try:
            reply = await self.bot.wait_for("message", check=check, timeout=timeout)
            countdown_task.cancel()

            embed.remove_footer()
            await status_msg.edit(embed=embed)

            mentioned_users = extract_mentions(reply, channel.guild)
            await reply.delete()
            return mentioned_users

        except asyncio.TimeoutError:
            countdown_task.cancel()
            await self._show_timeout(status_msg, "Aucune mention reçue. Processus annulé.")
            return None
        except discord.NotFound:
            # Message already deleted, not a critical error
            return mentioned_users if 'mentioned_users' in locals() else None

    @staticmethod
    async def _update_countdown(message, embed, view, total_seconds):
        """Update embed footer with countdown every second."""
        try:
            for remaining in range(total_seconds - 1, 0, -1):
                updated_embed = embed.copy()
                updated_embed.set_footer(
                    text=f"Temps restant pour terminer la soumission : {remaining} secondes",
                    icon_url="https://img.icons8.com/ios7/512/FFFFFF/clock--v3.png"
                )
                await message.edit(embed=updated_embed, view=view)
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        except discord.NotFound:
            pass

    @staticmethod
    async def _show_timeout(status_msg, description):
        """Display timeout message."""
        embed = discord.Embed(
            title="⏱️ Temps écoulé",
            description=description,
            color=0xFF0000
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2599/2599570.png")
        await status_msg.edit(embed=embed, view=None)

    @staticmethod
    async def _finalize_submission(status_msg):
        """Display success message."""
        embed = discord.Embed(
            title="✅ Soumission de Swince Reçue",
            description="Votre soumission a été enregistrée avec succès !",
            color=0x00FF00
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2599/2599570.png")
        await status_msg.edit(embed=embed, view=None)


def setup(bot):
    bot.add_cog(SwinceHandler(bot))
