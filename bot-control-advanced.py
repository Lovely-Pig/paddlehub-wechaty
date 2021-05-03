import cv2
import asyncio
import logging
import paddlehub as hub
from typing import Optional, Union

from wechaty_puppet import FileBox, ScanStatus  # type: ignore

from wechaty import Wechaty, Contact
from wechaty.user import Message, Room, contact

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# 定义paddlehub模型
model_anime = hub.Module(name='animegan_v2_shinkai_33', use_gpu=True)

# 将图片转换为动漫风格
def img_to_anime(img_name, img_path):
    # 图片名保持不变
    img_new_name = img_name

    # 图片路径改变
    img_new_path = './images-new/' + img_new_name

    # 模型预测
    result = model_anime.style_transfer(images=[cv2.imread(img_path)])

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
        # 主人的contact
        self.host_contact = None

        # 所有好友的contact
        self.friend_contacts = None

        # 群聊的room
        self.rooms = None

        # 好友的权限以及功能
        self.friend_allow = {}

        # 群聊的权限以及功能
        self.room_allow = {}


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
            # 识别主人
            if text == '你好我的机器人' and self.host_contact is None:
                # 记录主人的contact
                self.host_contact = from_contact

                # 列举所有好友的contact
                friend_contacts = await self.Contact.find_all()

                # 列举所有群
                self.rooms = await self.Room.find_all()

                # 过滤一些contact
                self.friend_contacts = [contact for contact in friend_contacts if len(contact.contact_id) > 50]

                # 初始化好友权限
                self.friend_allow = {contact: [False, None] for contact in self.friend_contacts}

                # 初始化群聊权限
                self.room_allow = {room: [False, None] for room in self.rooms}

                # 对主人开启权限
                self.friend_allow[self.host_contact] = [True, None]

                # 给主人发消息
                conversation = self.host_contact
                await conversation.ready()
                await conversation.say('你好亲爱的主人，机器人目前的功能有：\n1 将图片转换为动漫风格\n2 对好友开启机器人\n3 对好友关闭机器人\n4 对群聊开启机器人\n5 对群聊关闭机器人\n主人回复相应数字即可开启对应功能')

            # 如果是主人的消息
            if from_contact == self.host_contact:
                conversation = self.host_contact
                await conversation.ready()

                if self.friend_allow[self.host_contact][1] == 2:
                    # 关闭功能
                    self.friend_allow[self.host_contact][1] = None

                    # 获取好友备注或昵称
                    friend_name = text

                    # 记录是否找到好友
                    is_find = False

                    # 查找好友
                    for contact in self.friend_contacts:
                        if friend_name == contact.payload.alias or friend_name == contact.name:
                            # 找到
                            is_find = True
                            
                            # 对好友开启权限
                            self.friend_allow[contact] = [True, None]

                            # 给好友发消息
                            conversation_friend = contact
                            await conversation_friend.ready()
                            await conversation_friend.say('这是自动回复：你好，我是机器人，我的主人是Lovely-Pig，主人对你开启了机器人的功能')
                            await conversation_friend.say('这是自动回复：机器人目前的功能有：\n1 将图片转换为动漫风格\n回复相应数字即可开启对应功能')
                            break

                    # 给主人反馈
                    if is_find:
                        await conversation.say(f'亲爱的主人，已对{friend_name}开启机器人功能')

                    if not is_find:
                        await conversation.say(f'亲爱的主人，{friend_name}不在您的好友列表里，“对好友开启机器人”功能已关闭')


                if self.friend_allow[self.host_contact][1] == 3:
                    # 关闭功能
                    self.friend_allow[self.host_contact][1] = None

                    # 获取好友备注或昵称
                    friend_name = text

                    # 记录是否找到好友
                    is_find = False

                    # 查找好友
                    for contact in self.friend_contacts:
                        if friend_name == contact.payload.alias or friend_name == contact.name:
                            # 找到
                            is_find = True
                            
                            # 对好友关闭权限
                            self.friend_allow[contact] = [False, None]

                            # 给好友发消息
                            conversation_friend = contact
                            await conversation_friend.ready()
                            await conversation_friend.say('这是自动回复：你好，我是机器人，我的主人是Lovely-Pig，主人对你关闭了机器人的功能')
                            break

                    # 给主人反馈
                    if is_find:
                        await conversation.say(f'亲爱的主人，已对{friend_name}关闭机器人功能')

                    if not is_find:
                        await conversation.say(f'亲爱的主人，{friend_name}不在您的好友列表里，“对好友关闭机器人”功能已关闭')


                if self.friend_allow[self.host_contact][1] == 4:
                    # 关闭功能
                    self.friend_allow[self.host_contact][1] = None

                    # 获取群聊名称
                    room_name = text

                    # 记录是否找到群聊
                    is_find = False

                    # 查找群聊
                    for room in self.rooms:
                        if room_name == await room.topic():
                            # 找到
                            is_find = True
                            
                            # 对群聊开启权限
                            self.room_allow[room] = [True, None]

                            # 给群聊发消息
                            conversation_room = room
                            await conversation_room.ready()
                            await conversation_room.say('这是自动回复：你们好，我是机器人，我的主人是Lovely-Pig，主人对群开启了机器人的功能')
                            await conversation_room.say('这是自动回复：机器人目前的功能有：\n1 将图片转换为动漫风格\n回复相应数字即可开启对应功能')
                            break

                    # 给主人反馈
                    if is_find:
                        await conversation.say(f'亲爱的主人，已对{room_name}开启机器人功能')

                    if not is_find:
                        await conversation.say(f'亲爱的主人，{room_name}不在您的群聊列表里，“对群聊开启机器人”功能已关闭')

                
                if self.friend_allow[self.host_contact][1] == 5:
                    # 关闭功能
                    self.friend_allow[self.host_contact][1] = None

                    # 获取群聊名称
                    room_name = text

                    # 记录是否找到群聊
                    is_find = False

                    # 查找群聊
                    for room in self.rooms:
                        if room_name == await room.topic():
                            # 找到
                            is_find = True
                            
                            # 对群聊开启权限
                            self.room_allow[room] = [False, None]

                            # 给群聊发消息
                            conversation_room = room
                            await conversation_room.ready()
                            await conversation_room.say('这是自动回复：你们好，我是机器人，我的主人是Lovely-Pig，主人对群关闭了机器人的功能')
                            break

                    # 给主人反馈
                    if is_find:
                        await conversation.say(f'亲爱的主人，已对{room_name}关闭机器人功能')

                    if not is_find:
                        await conversation.say(f'亲爱的主人，{room_name}不在您的群聊列表里，“对群聊关闭机器人”功能已关闭')


                if text == '1':
                    self.friend_allow[self.host_contact][1] = 1
                    await conversation.say('亲爱的主人，您已开启“将图片转换为动漫风格”功能，请发给我一张图片')

                if text == '2':
                    self.friend_allow[self.host_contact][1] = 2
                    await conversation.say('亲爱的主人，您已开启“对好友开启机器人”功能，请指明是哪一个好友')

                if text == '3':
                    self.friend_allow[self.host_contact][1] = 3
                    await conversation.say('亲爱的主人，您已开启“对好友关闭机器人”功能，请指明是哪一个好友')

                if text == '4':
                    self.friend_allow[self.host_contact][1] = 4
                    await conversation.say('亲爱的主人，您已开启“对群聊开启机器人”功能，请指明是哪一个群')

                if text == '5':
                    self.friend_allow[self.host_contact][1] = 5
                    await conversation.say('亲爱的主人，您已开启“对群聊关闭机器人”功能，请指明是哪一个群')


            # 好友的消息
            if from_contact in self.friend_contacts and from_contact != self.host_contact:
                # 如果好友有权限
                if self.friend_allow[from_contact][0]:
                    conversation = from_contact
                    await conversation.ready()

                    if text == '1':
                        self.friend_allow[from_contact][1] = 1
                        await conversation.say('这是自动回复：你已开启“将图片转换为动漫风格”功能，请发给我一张图片')


            # 如果消息类型是图片
            if type == Message.Type.MESSAGE_TYPE_IMAGE:
                # 如果有权限
                if from_contact in self.friend_contacts and self.friend_allow[from_contact][0]:
                    # 判断功能
                    if self.friend_allow[from_contact][1] == 1:

                        # 关闭功能
                        self.friend_allow[from_contact][1] = None

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

              
        # 如果群聊有权限
        if room is not None and self.room_allow[room][0]:
            conversation = room
            await conversation.ready()

            if text == '1':
                self.room_allow[room][1] = 1
                await conversation.say('这是自动回复：已开启“将图片转换为动漫风格”功能，请发给我一张图片')

            # 如果消息类型是图片
            if type == Message.Type.MESSAGE_TYPE_IMAGE:
                # 判断功能
                if self.room_allow[room][1] == 1:

                    # 关闭功能
                    self.room_allow[room][1] = None

                    conversation = room
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
