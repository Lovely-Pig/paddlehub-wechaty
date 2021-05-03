import asyncio
import logging
from typing import Optional, Union

from wechaty_puppet import FileBox, ScanStatus  # type: ignore

from wechaty import Wechaty, Contact
from wechaty.user import Message, Room

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class MyBot(Wechaty):
    """
    listen wechaty event with inherited functions, which is more friendly for
    oop developer
    """
    def __init__(self):
        super().__init__()

    async def on_message(self, msg: Message):
        """
        listen for message event
        """
        from_contact = msg.talker()
        text = msg.text()
        room = msg.room()
        
        # 不处理群消息
        if room is None:
            if text == 'hi' or text == '你好':
                conversation = from_contact
                await conversation.ready()
                await conversation.say('这是自动回复：机器人目前的功能有：\n1. 收到"ding"，自动回复"dong dong dong"\n2. 收到"图片"，自动回复一张图片')

            if text == 'ding':
                conversation = from_contact
                await conversation.ready()
                await conversation.say('这是自动回复：dong dong dong')

            if text == '图片':
                conversation = from_contact

                # 从网络上加载图片到file_box
                img_url = 'https://images.unsplash.com/photo-1470770903676-69b98201ea1c?ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&ixlib=rb-1.2.1&auto=format&fit=crop&w=1500&q=80'
                file_box = FileBox.from_url(img_url, name='xx.jpg')
                
                await conversation.ready()
                await conversation.say('这是自动回复：')
                await conversation.say(file_box)

    async def on_login(self, contact: Contact):
        print(f'user: {contact} has login')

    async def on_scan(self, status: ScanStatus, qr_code: Optional[str] = None,
                      data: Optional[str] = None):
        contact = self.Contact.load(self.contact_id)
        print(f'user <{contact}> scan status: {status.name} , '
              f'qr_code: {qr_code}')


bot: Optional[MyBot] = None


async def main():
    """doc"""
    # pylint: disable=W0603
    global bot
    bot = MyBot()
    await bot.start()


asyncio.run(main())