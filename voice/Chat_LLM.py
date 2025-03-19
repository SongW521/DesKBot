import os
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
from message_queen import ZMQPublisher

# 提前加载模型
def load_chat_llm():
    # 星火认知大模型Spark Max的URL值
    SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.5/chat'
    # 星火认知大模型调用秘钥信息
    SPARKAI_APP_ID = '04a71e96'
    SPARKAI_API_SECRET = 'MjRmOTM3ZjI3N2JiOTE0YmU2NmM0MDFj'
    SPARKAI_API_KEY = '6acc3441099d0aeee317f86135d2d455'
    # 星火认知大模型Spark Max的domain值
    SPARKAI_DOMAIN = 'generalv3.5'

    spark_model = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )
    return spark_model

# 从文件中读取系统提示信息
def read_system_tip(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
        return None

def get_user_input():
    user_input = input("请输入您的问题（输入'exit'退出）：")
    return user_input

def sendMessage(publisher:ZMQPublisher, text):
    parts = text.split(" | ")
    if len(parts) == 3:
        cmd = parts[1]  # 第二部分是 cmd
        emo = parts[2]  # 第三部分是 emo
        # 将 cmd 和 emo 放入一个新数组中
        mes = f"{cmd} | {emo}"  # 或者 mes_str = cmd + " | " + emo
        publisher.send_message(mes)
    else:
        print("格式不正确，无法发送消息。")

def main():
    handler = ChunkPrintHandler()
    spark = load_chat_llm()  # 加载模型
    # 获取当前脚本所在的目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # 拼接 systemTip.txt 的路径
    file_path = os.path.join(script_dir, "systemTip.txt")
    print("系统提示文件路径：", file_path)
    # 读取系统提示信息
    systemTip = read_system_tip(file_path)
    publisher = ZMQPublisher()

    if systemTip is None:
        return  # 如果文件未找到或读取失败，则退出程序

    sent_system_message = False  # 用于标记是否已经发送过系统信息

    while True:
        ques = get_user_input()
        if ques.lower() == 'exit':
            break

        messages = []  # 每次都清空消息列表
        if not sent_system_message:  # 如果还没有发送过系统信息，则发送
            # 将系统提示和用户输入都添加到消息列表
            messages = [
                ChatMessage(role="system", content=systemTip),
                ChatMessage(role="user", content=ques)
            ]
        else:
            # 如果系统消息已经发送过，直接添加用户消息
            messages.append(ChatMessage(role="user", content=ques))

        res = spark.generate([messages], callbacks=[handler])  # 调用生成函数
        text_output = res.generations[0][0].text  # 获取生成的文本
        print("蛋黄：", text_output)

        # 发送消息（如果需要的话，调用发送消息函数）
        sendMessage(publisher, text_output)

if __name__ == '__main__':
    main()
