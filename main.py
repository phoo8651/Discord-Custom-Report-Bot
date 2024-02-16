from typing import Final
import os
from dotenv import load_dotenv
from discord import Intents, Client, Message, Embed, PermissionOverwrite, PermissionOverwrite, PermissionOverwrite
import uuid
import asyncio

# STEP 0: Load OUR TOKEN FROM SOMEWHERE SAFE
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
print("Discord Token: " + TOKEN)
REPORT_CHANNEL: Final[str] = os.getenv('REPORT_CHANNEL')
print("신고 채널 ID: " + REPORT_CHANNEL)
CATEGORY_ID: Final[str] = os.getenv('CATEGORY_ID')
print("신고 카테고리 ID: " + CATEGORY_ID)
LOG_CHANNEL_ID: Final[str] = os.getenv('LOG_CHANNEL_ID')
print("로그 채널 ID: " +LOG_CHANNEL_ID)

ReportList = []

# STEP 1: BOT SETUP
intents: Intents = Intents.default()
intents.message_content = True # NOQA
client: Client = Client(intents=intents)

# STEP 2: MESSAGE FUNCTIONALITY
async def send_message(message: Message, user_message: str) -> None:
  if not user_message:
    print('(Message was empty because intents were not enabled probably)')
    return

  if is_private := user_message[0] == '?':
    user_message = user_message[1:]
    
  try:
    if user_message == '!신고':
      if message.channel.id != int(REPORT_CHANNEL):
        print('(Message was not sent in the report channel)')
        return

      channel_name = str(uuid.uuid4())

      category = client.get_channel(int(CATEGORY_ID))
      if not category:
        return await message.channel.send("신고 카테고리를 찾을 수 없습니다.")

      if len(ReportList) >= 10:
        return await message.channel.send("신고 채널이 가득 찼습니다. 잠시 후 다시 시도해주세요.")

      overwrites = {
        message.guild.default_role: PermissionOverwrite(read_messages=False),
        message.guild.me: PermissionOverwrite(read_messages=True),
        message.author: PermissionOverwrite(read_messages=True)
      }

      channel = await category.create_text_channel(channel_name, overwrites=overwrites)
      ReportList.append(channel.id)
      await channel.send("신고자명: (이름) / 신고 일시: (시간) / 신고 내용: (내용)")

      def check(message):
        return message.channel == channel and message.author == message.author

      try :
        await client.wait_for('message', check=check, timeout=1800)  # 30분 대기
      except asyncio.TimeoutError:
        await message.author.send("시간이 초과되었습니다. 신고가 취소되었습니다.")
        await channel.delete()
        
    else :
      for report in ReportList :
        if message.channel.id == int(report) :
          break
        else :
          return

      log_channel = client.get_channel(int(LOG_CHANNEL_ID))
      content = message.content.split('/')

      if len(content) != 3:
        await message.channel.send("신고 양식이 올바르지 않습니다. 모든 정보를 입력해주세요.")
        return
      
      try:
        report_info = {
          '신고자명': content[0].split(':')[1].strip(),
          '신고 일시': content[1].split(':')[1].strip(),
          '신고 내용': content[2].split(':')[1].strip()
        }

        embed = Embed(title="신고 정보", color=0xff0000)
        embed.add_field(name="신고자명", value=report_info['신고자명'], inline=False)
        embed.add_field(name="신고 일시", value=report_info['신고 일시'], inline=False)
        embed.add_field(name="신고 내용", value=report_info['신고 내용'], inline=False)

        await log_channel.send(embed=embed)
        await message.author.send("신고가 접수 되었습니다. 감사합니다.")
        ReportList.remove(report)
        print(ReportList)
        await message.channel.delete()
      except Exception as e:
        print(e)
  except Exception as e:
    print(e)

# STEP 3: HANDLING THE STARTUP FOR OUR BOT
@client.event 
async def on_ready() -> None:
  print(f'{client.user} has connected to Discord!')

# STEP 4: HANDLING INCOMING MESSAGES
@client.event
async def on_message(message: Message) -> None:
  if message.author == client.user:
    return

  user_message: str = message.content
  await send_message(message, user_message)

# STEP 5: MAIN ENTRY POINT
def main() -> None:
  client.run(token=TOKEN)

if __name__ == '__main__':
  main()