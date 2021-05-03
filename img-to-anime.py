import cv2
import asyncio
import logging
import paddlehub as hub
from typing import Optional, Union

from wechaty_puppet import FileBox, ScanStatus  # type: ignore

from wechaty import Wechaty, Contact
from wechaty.user import Message, Room

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# 定义paddlehub模型
model = hub.Module(name='animegan_v2_shinkai_33', use_gpu=True)

# 将图片转换为动漫风格
def img_to_anime(img_name, img_path):
    # 图片名保持不变
    img_new_name = img_name

    # 图片路径改变
    img_new_path = './images-new/' + img_new_name

    # 模型预测
    result = model.style_transfer(images=[cv2.imread(img_path)])

    # 将新图片存储到新路径
    cv2.imwrite(img_new_path, result[0])

    return img_new_path


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
        type = msg.type()
        room = msg.room()

        # 不处理群消息
        if room is None:
            if text == 'hi' or text == '你好':
                conversation = from_contact
                await conversation.ready()
                await conversation.say('这是自动回复：机器人目前的功能有：\n1 收到"ding"，自动回复"dong dong dong"\n2 收到"图片"，自动回复一张图片\n3 收到一张图片，将这张图片转换为动漫风格并返回')

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

            # 如果消息类型是图片
            if type == Message.Type.MESSAGE_TYPE_IMAGE:
                conversation = from_contact
                await conversation.ready()
                await conversation.say('这是自动回复：正在飞速处理中...')

                # 将msg转换为file_box
                file_box = await msg.to_file_box()

                # 获取图片名
                img_name = file_box.name

                # 图片保存的路径
                img_path = './images/' + img_name

                # 将图片保存到文件中
                await file_box.to_file(file_path=img_path, overwrite=True)

                # 调用函数，获取图片新路径
                img_new_path = img_to_anime(img_name, img_path)

                # 从文件中加载图片到file_box
                file_box_new = FileBox.from_file(img_new_path)

                await conversation.say(file_box_new)


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