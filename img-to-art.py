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
model = hub.Module(name="stylepro_artistic")

# 将第一张图片转换为第二张图片的风格
def img_to_art(img_name, img_path, img_art_path):
    # 图片名保持不变
    img_new_name = img_name

    # 图片路径改变
    img_new_path = './images-new/' + img_new_name

    # 模型预测
    result = model.style_transfer(images=[{'content': cv2.imread(img_path),'styles': [cv2.imread(img_art_path)]}])

    # 将新图片存储到新路径
    cv2.imwrite(img_new_path, result[0]['data'])

    return img_new_path


class MyBot(Wechaty):
    """
    listen wechaty event with inherited functions, which is more friendly for
    oop developer
    """
    def __init__(self):
        super().__init__()

        # 图像信息
        # [flag, img, img_name, img_path, img_new_name, img_new_path]
        self.img = [True, None, None, None, None, None]

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
                await conversation.say('这是自动回复：机器人目前的功能有：\n1 收到"ding"，自动回复"dong dong dong"\n2 收到"图片"，自动回复一张图片\n3 收到两张图片，将第一张图片转换为第二张图片的风格并返回，如需使用此功能，请回复“风格转换”')

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

            if text == '风格转换':
                self.img[1] = 0
                conversation = from_contact
                await conversation.ready()
                await conversation.say('这是自动回复：请输入第一张图片')

            # 如果消息类型是图片
            if type == Message.Type.MESSAGE_TYPE_IMAGE:
                if from_contact == self.friend_contact:
                    self.img[0] = not self.img[0]
                    if self.img[1] == 0:

                        self.img[1] = 1
                        # 将msg转换为file_box
                        file_box = await msg.to_file_box()

                        # 获取图片名
                        self.img[2] = file_box.name

                        # 图片保存的路径
                        self.img[3] = './images/' + self.img[2]

                        # 将图片保存到文件中
                        await file_box.to_file(file_path=self.img[3], overwrite=True)

                        conversation = from_contact
                        await conversation.ready()
                        await conversation.say('这是自动回复：请输入第二张图片')

                    if self.img[1] == 1 and self.img[0]:

                        self.img[1] = None

                        conversation = from_contact
                        await conversation.ready()
                        await conversation.say('这是自动回复：正在飞速处理中...')

                        # 将msg转换为file_box
                        file_box_art = await msg.to_file_box()

                        # 获取图片名
                        self.img[4] = file_box_art.name

                        # 图片保存的路径
                        self.img[5] = './images/' + self.img[4]

                        # 将图片保存到文件中
                        await file_box_art.to_file(file_path=self.img[5], overwrite=True)

                        # 调用函数，获取图片新路径
                        img_new_path = img_to_art(self.img[2], self.img[3], self.img[5])

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