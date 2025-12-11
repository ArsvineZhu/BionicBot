#! python3.13
# import os
from bot.core.api_key import API_KEY
from volcenginesdkarkruntime import Ark
from bot.core.model import Content, Message, ApiModel, ROLE_TYPE, ABILITY


MODEL = "doubao-seed-1-6-flash-250828"

client = Ark(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=API_KEY,
)

# 加载身份文件
with open(r".\soul_doc\yuki.md", "r", encoding="utf-8") as file:
    soul = file.read()

# 注入系统提示词
sys_content = Content(soul)
sys_msg = Message(sys_content, ROLE_TYPE.SYSTEM)

user_msgs = []
ai_msgs = []
msgs = []

id_ = "Texas[Arsvine]"
response_id = None

while True:
    # 用户对话 - 带用户身份信息
    user_content = Content(f"{id_}: " + input(f"{id_}: "))
    user_msg = Message(user_content)
    user_msgs.append(user_msg)
    msgs.append(user_msg)

    # 构建数据包
    apimodel = ApiModel(
        MODEL,
        [] if response_id else [sys_msg] + [user_msg],
        response_id,
        thinking=ABILITY.AUTO,
        temperature=1,
    ).export(False)

    response = client.responses.create(**apimodel)
    response_id = response.id  # type: ignore

    try:
        reply: str = response.output[1].content[0].text  # type: ignore
    except:
        reply: str = response.output[0].content[0].text  # type: ignore
    print("Reply(s):", *reply.split("\n"), sep="\n")

    # AI回答注入，构建多轮对话
    ai_content = Content(reply)
    ai_msg = Message(ai_content, ROLE_TYPE.ASSIST)
    ai_msgs.append(ai_msg)
    msgs.append(ai_msg)
