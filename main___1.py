"""
Main Discord bot script
"""
import discord
import asyncio
import re
import phonenumbers
from string import Template
import loco_functions

CANT_SEND_VERIF_CODE_MSG = \
"""
**Error sending verification code.**
"""
CANT_AUTH_MSG = \
"""
**Can\'t authorize on Loco server.**
Try again later.
"""

SENT_VERIF_CODE_MSG = \
"""
**Check your phone!**
Verification code is sent.
To start getting coins type `;code <otp_you_received>`"""

WAITING_MSG = \
"""
*Please wait...*
"""
PRACTICE_STATUS_TEMPLATE = \
"""
**Game status** :trophy:
```
Coins Added : $total_coins
Questions answered : $questions
Games played : $games
       ©made by MYRAN & RAHUL```
"""
PRACTICE_ERR_MSG = \
"""
**Something went wrong!**
Maybe Loco server too busy.
Please try again.
"""

HELP_MESSAGE = \
"""
Hi! I\'m Loco coins bot.free coin form KESHAV{Dev}
To get some coins type `;play <phone_number>`
**Phone number should be in international format.**
*e.g.:* `;play +9212312312312`
"""

class LocoCoinsBot(discord.Client):
    async def on_ready(self):
        print('Logged in as: %s' % self.user.name)
        self.play_requests = {}

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return
        # Make sure to not respond to DM messages
        if isinstance(message.author, discord.User):
            return

        """
        ;help
        """
        if message.content.startswith(';help'):
            await message.channel.send(HELP_MESSAGE)
            return

        """
        ;play <phone_number>
        """
        if message.content.startswith(';play'):
            # parse phone number
            try:
                phone = message.content.split()[1]
                pp = phonenumbers.parse(phone)
                country_abbrev = phonenumbers.region_code_for_number(pp).lower()
                national_number = str(pp.national_number)
            except:
                await message.channel.send('**Wrong command or phone number**. '\
                                           'Usage: `;play <phone_number>`')
                return

            # requesting sms code to user phone from Loco
            res = loco_functions.get_sms_code_from_Loco(country_abbrev=country_abbrev,\
                                                  national_number=national_number)
            if res is None:
                await message.channel.send(CANT_SEND_VERIF_CODE_MSG)
                return

            play_answer = await message.channel.send(SENT_VERIF_CODE_MSG)

            # waiting for SMS code from same user
            try:
                def is_correct_sms_code(m):
                    if m.author != message.author:
                        return False
                    m = re.match(r';code ([\d]{4})', m.content)
                    if m is None:
                        return False
                    global sms_code
                    sms_code = m.group(1)
                    return True

                await self.wait_for('message', check=is_correct_sms_code,\
                                                   timeout=40.0)
            except asyncio.TimeoutError:
                return await play_answer.edit(content=\
                                 play_answer.content+'\nSMS code has expired')

            await play_answer.edit(content=SENT_VERIF_CODE_MSG+WAITING_MSG)

            profile_token = loco_functions.authorize(country_abbrev=country_abbrev,
                                                  national_number=national_number,
                                                  sms_code=sms_code)
            if profile_token is None:
                await play_answer.edit(content=play_answer.content+CANT_AUTH_MSG)
                return

            try:
                for res in loco_functions.main_play_loop(country_abbrev=country_abbrev,
                        national_number=national_number,
                        profile_token=profile_token):

                    if 'error' in res.keys():
                        await play_answer.edit(content=play_answer.content+PRACTICE_ERR_MSG)
                        return

                    practice_msg = Template(PRACTICE_STATUS_TEMPLATE).substitute(res)
                    await play_answer.edit(content=SENT_VERIF_CODE_MSG+practice_msg)
            except:
                await play_answer.edit(content=play_answer.content+PRACTICE_ERR_MSG)
                return
            else:
                await play_answer.edit(content=play_answer.content+'\n**All games are played!**')
                return

bot = LocoCoinsBot()

bot.run('NTg1OTQyMzQ3ODk2OTc5NDY4.XRepWg.oZangan14199Tc45Bp2iLx0GqSs')

