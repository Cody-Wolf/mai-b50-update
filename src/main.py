import time
import httpx

from pycqBot import cqHttpApi, cqLog
from pycqBot.data import Message

from chatgpt import ChatGPT

accounts = {}
query_qids = set()


def query_gpt(command_data, message: Message):
    print("command_data", command_data)
    message.reply(chatgpt.query(message.raw_message))


def query_b50(command_data, message: Message):
    print("common_data", command_data)

    if message.sender.id not in accounts:
        message.reply("先向 bot 私聊注册查分器账户哦！小窗私聊 bot 输入 #help 查看 #b50_register 的使用方法。")
        return

    if message.sender.id in query_qids:
        message.reply("你已经在更新了！请等待此次更新完毕！")
        return

    response = httpx.post("https://maimai.bakapiano.com/bot", json=accounts[message.sender.id], timeout=60)
    trace_url = response.text
    message.reply(
        "已提交更新申请！bot在 添加好友/开始更新/更新完成 三个阶段会通知你。你也可以手动查询进度。\n trace url：" + trace_url)

    query_qids.add(message.sender.id)

    start_time = time.time()
    sent_friend_request = False
    start_update = False
    get_url = trace_url.replace("#/", "").replace("trace/", "trace?uuid=")
    get_url = get_url[:len(get_url) - 1]

    while time.time() - start_time < 15 * 60:

        response = httpx.get(get_url, timeout=60)
        print(response.text)

        if not sent_friend_request and "好友请求发送成功" in response.text:
            sent_friend_request = True
            message.reply("Bot 已向你添加好友，请打开 maimai 微信公众号同意！")

        if not start_update and "开始更新" in response.text:
            start_update = True
            message.reply("好友添加完成。Bot 开始更新！")

        if "玩家不存在" in response.text:
            message.reply("好友代码错误，请重新向 bot 注册信息！")
            query_qids.remove(message.sender.id)
            return

        if "长时间未接受好友请求" in response.text:
            message.reply("5 分钟内未接受好友请求，请重新更新！")
            query_qids.remove(message.sender.id)
            return

        if "更新完成" in response.text:
            message.reply("更新完成！自动帮你询问 b50。")
            time.sleep(1)
            message.reply("b50 " + accounts[message.sender.id]["username"])
            query_qids.remove(message.sender.id)
            return

        time.sleep(5)

    message.reply("更新超时，请重新更新！")
    query_qids.remove(message.sender.id)


def register_b50(command_data, message: Message):
    print("command_data", command_data)
    if len(command_data) == 3:
        accounts[message.sender.id] = {"username": command_data[0],
                                       "password": command_data[1],
                                       "friendCode": command_data[2]}
        message.reply("注册成功！")

    else:
        message.reply("参数个数错误！格式为：查分器账号 密码 好友代码")


if __name__ == "__main__":
    gpt_api_key = input('输入 chatgpt key, 留空代表不使用: ')
    chatgpt = ChatGPT(gpt_api_key)
    cqLog(logPath="pycq_bot")

    cq_api = cqHttpApi(download_path="pycq_bot")

    bot = cq_api.create_bot(
        group_id_list=[
            882148260,
            768509926
        ]
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

    bot.start("pycq_bot")
