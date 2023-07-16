import time

import httpx

from pycqBot import cqHttpApi, cqLog
from pycqBot.data import Message

from chatgpt import ChatGPT
from account_db import AccountsDB

ACCOUNTS_DB_FILE_PATH = "pycq_bot/accounts.db"
PYCQ_BOT_PATH = "pycq_bot"
PYCQ_BOT_LOG_PATH = "pycq_bot/cqLogs"

WEBSOCKET_HOST = "ws://127.0.0.8080"

HTTP_REQUEST_TIMEOUT_SECOND = 60
UPDATE_LIMIT_SECOND = 15 * 60

accounts = AccountsDB(ACCOUNTS_DB_FILE_PATH)
query_qids = set()


def query_gpt(command_data, message: Message):
    message.reply(chatgpt.query(message.raw_message))


def query_b50(command_data, message: Message):
    qid = message.sender.id
    account = accounts.query_account_by_qid(qid)
    if len(account) == 0:
        message.reply("先向 bot 私聊注册查分器账户哦！小窗私聊 bot 输入 #help 查看注册指令（#b50_register）的使用方法。")
        return

    if qid in query_qids:
        message.reply("你已经在更新了！请等待此次更新完毕！")
        return

    response = httpx.post("https://maimai.bakapiano.com/bot", json=account, timeout=HTTP_REQUEST_TIMEOUT_SECOND)
    trace_url = response.text
    message.reply(f'''
    已提交 b50 更新申请！
    bot 在 添加好友/添加完成开始更新/更新完成 三个阶段会通知你。
    你也可以通过链接手动查询进度：{trace_url}。
    ''')

    query_qids.add(qid)
    start_time = time.time()
    sent_friend_request = False
    start_update = False

    '''
        https://maimai.bakapiano.com/#/trace/d07a36c7-519f-4513-bc6e-af7dab273879/
        变为：
        https://maimai.bakapiano.com/trace?uuid=d07a36c7-519f-4513-bc6e-af7dab273879
    '''
    get_url = trace_url.replace("#/", "").replace("trace/", "trace?uuid=")
    get_url = get_url[:len(get_url) - 1]

    while time.time() - start_time < UPDATE_LIMIT_SECOND:

        response = httpx.get(get_url, timeout=HTTP_REQUEST_TIMEOUT_SECOND)
        print(response.text)

        if not sent_friend_request and "好友请求发送成功" in response.text:
            sent_friend_request = True
            message.reply("Bot 已向你添加好友，请打开 舞萌|中二 微信公众号同意！")

        if not start_update and "开始更新" in response.text:
            start_update = True
            message.reply("好友添加完成。Bot 开始更新！")

        if "玩家不存在" in response.text:
            message.reply("好友代码错误，推荐向请重新向 bot 注册信息！")
            query_qids.remove(message.sender.id)
            return

        if "长时间未接受好友请求" in response.text:
            message.reply("5 分钟内未接受好友请求，请重新更新！")
            query_qids.remove(message.sender.id)
            return

        if "更新完成" in response.text:
            message.reply("更新完成！自动帮你询问 b50。")
            time.sleep(1)
            message.reply("b50 " + accounts.query_account_by_qid(message.sender.id)["user_name"])
            query_qids.remove(message.sender.id)
            return

        time.sleep(5)

    message.reply("更新超时，请重新更新！")
    query_qids.remove(message.sender.id)


def register_b50(command_data, message: Message):
    qid = message.sender.id
    if len(command_data) == 3:
        accounts.insert_account(qid, command_data[0], command_data[1], command_data[2])
        message.reply("注册成功！")
    else:
        message.reply("参数个数错误！格式为：查分器账号 密码 好友代码, 不要有多余的空格！")


if __name__ == "__main__":
    gpt_api_key = input('输入 chatgpt key, 留空代表不使用: ')
    chatgpt = ChatGPT(gpt_api_key)
    cqLog(logPath=PYCQ_BOT_LOG_PATH)

    cq_api = cqHttpApi(download_path=PYCQ_BOT_PATH)

    bot = cq_api.create_bot(
        group_id_list=[
            882148260,
            768509926
        ],
        host=WEBSOCKET_HOST
    )

    bot.command(query_gpt, "chatgpt", {
        "help": ["#chatgpt - 询问 chatgpt-3.5（上下文整个群有效）。\n"],
        "type": "group"
    }).command(register_b50, "b50_register", {
        "help": ["#b50_register - 在 bot 处保存查分器账号密码。",
                 "格式：#b50_register 查分器账号 密码 好友代码",
                 "如：#b50_register Cody 114514 1919810\n"],
        "type": "all"
    }).command(query_b50, "b50_update", {
        "help": ["#b50_update - 更新 b50, 请提前告诉 bot 你的查分器账号密码，以及 maimai 好友代码。",
                 "私聊 bot '#help' 可以获得注册的方法",
                 "在更新之后，请尽快打开 maimai 微信公众号添加机器人为好友，限时为 5 分钟。\n"],
        "type": "all"
    })

    bot.start(go_cqhttp_path=PYCQ_BOT_PATH)

    bot.stop()
    accounts.close()
