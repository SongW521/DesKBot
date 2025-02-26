import pyttsx3

def start_TTS(text):
    # 创建 TTS 引擎
    engine = pyttsx3.init()
    # 获取可用的语音列表
    voices = engine.getProperty('voices')
    # 列出可用的声音
    engine.setProperty('voice', voices[0].id)
    # 说出文本
    engine.say(text)
    engine.runAndWait()



