import re
import asyncio
import logging
from numpy import mean
import paddlehub as hub
from typing import Optional, Union

from wechaty_puppet import FileBox, ScanStatus  # type: ignore

from wechaty import Wechaty, Contact
from wechaty.user import Message, Room, contact

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# 定义主模型
modle_main = hub.Module(name="ernie_skep_sentiment_analysis")

# 定义辅助模型
model_lstm = hub.Module(name="senta_lstm")
model_bilstm = hub.Module(name="senta_bilstm")
model_gru = hub.Module(name="senta_gru")

def analyse_kind(text):
    # 转换文本为列表形式
    text = [text]

    # 主模型输出结果
    results_main = modle_main.predict_sentiment(text, use_gpu=True)
    result_main = results_main[0]

    # 辅助模型输出结果
    results_lstm = model_lstm.sentiment_classify(text, use_gpu=True)
    result_lstm = results_lstm[0]

    results_bilstm = model_bilstm.sentiment_classify(text, use_gpu=True)
    result_bilstm = results_bilstm[0]

    results_gru = model_gru.sentiment_classify(text, use_gpu=True)
    result_gru = results_gru[0]

    results = [result_lstm, result_bilstm, result_gru]

    list_score = []

    # 如果消息是友好的
    if result_main['sentiment_label'] == 'positive':
        score = result_main['positive_probs'] * 5
        list_score.append(score)
        for result in results:
            if result['sentiment_label'] == 'positive':
                score = result['positive_probs'] * 5
                list_score.append(score)


    # 如果消息是不友好的
    elif result_main['sentiment_label'] == 'negative':
        score = result_main['negative_probs'] * (-5)
        list_score.append(score)
        for result in results:
            if result['sentiment_label'] == 'negative':
                score = result['negative_probs'] * (-5)
                list_score.append(score)

    score = mean(list_score)
    score = round(score, 2)

    return score


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

        # 好友友好账户
        self.account_kind = {}

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

                # 过滤一些contact
                self.friend_contacts = [contact for contact in friend_contacts if contact.is_personal()]

                # 移除主人的contact
                self.friend_contacts.remove(self.host_contact)

                # 初始化好友的友好账户
                self.account_kind = {contact: 0 for contact in self.friend_contacts}

                # 给主人发消息
                conversation = self.host_contact
                await conversation.ready()
                await conversation.say('你好我亲爱的主人，我是主人的好友友好账户管家，目前的功能有：\n1 管理主人的好友友好账户\n2 查询主人的好友友好账户\n主人回复相应数字即可查询详细功能')

            # 如果是主人的消息
            if from_contact == self.host_contact:
                conversation = self.host_contact
                await conversation.ready()

                if text == '1':
                    await conversation.say('当有好友给主人发消息时，将自动分析这句话的友好分数，并记录在主人的好友友好账户上')

                if text == '2':
                    await conversation.say('主人按照以下格式即可查询好友的友好账户\n查询 好友 张三\n\n主人按照以下格式即可查询好友友好账户排名前五\n查询 前5\n\n主人按照以下格式即可查询好友友好账户排名后五\n查询 后5')

                if '查询 好友' in text:
                    # 提取好友备注或昵称
                    friend_name = text.split(' ')[-1]
                    # 遍历字典，找打好友的友好账户分数并返回
                    for contact, score in list(self.account_kind.items()):
                        if friend_name == contact.name or friend_name == contact.payload.alias:
                            friend_score = round(score, 2)
                            break

                    await conversation.say(f'亲爱的主人，{friend_name}目前的友好分数为：{friend_score}')

                if '查询 前' in text:
                    # 提取数字
                    number = re.findall(r'\d+', text)
                    number = int(number[0])

                    # 按照账户分数大小给字典排序
                    sorted_account_kind = {contact: score for contact, score in sorted(self.account_kind.items(), key=lambda item: item[1], reverse=True)}

                    # 给主人发的消息内容
                    msg_to_host = f'亲爱的主人，目前好友友好账户排名前{number}的是：'
                    for contact, score in list(sorted_account_kind.items())[:number]:
                        # 获取好友备注或昵称
                        friend_name = contact.payload.alias if contact.payload.alias != '' else contact.name
                        msg_to_host += f'\n{friend_name}：{round(score, 2)}'

                    await conversation.say(msg_to_host)


                if '查询 后' in text:
                    # 提取数字
                    number = re.findall(r'\d+', text)
                    number = int(number[0])
                    sorted_account_kind = {contact: score for contact, score in sorted(self.account_kind.items(), key=lambda item: item[1])}

                    # 给主人发的消息内容
                    msg_to_host = f'亲爱的主人，目前好友友好账户排名后{number}的是：'
                    for contact, score in list(sorted_account_kind.items())[:number]:
                        # 获取好友备注或昵称
                        friend_name = contact.payload.alias if contact.payload.alias != '' else contact.name
                        msg_to_host += f'\n{friend_name}：{round(score, 2)}'

                    await conversation.say(msg_to_host)

            # 好友的消息
            if from_contact in self.friend_contacts and type == Message.Type.MESSAGE_TYPE_TEXT:
                # 计算好友消息的友好分数
                score = analyse_kind(text)

                # 更新好友的友好账户
                self.account_kind[from_contact] += score
                self.account_kind[from_contact] = round(self.account_kind[from_contact], 2)

                # 获取好友备注或昵称
                friend_name = from_contact.payload.alias if from_contact.payload.alias != '' else from_contact.name

                # 给主人汇报消息
                conversation = self.host_contact
                await conversation.ready()
                await conversation.say(f'亲爱的主人，{friend_name}给您发了一条消息\n消息内容是: {text}\n友好分数是: {score}\n{friend_name}目前的友好分数为：{self.account_kind[from_contact]}')


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