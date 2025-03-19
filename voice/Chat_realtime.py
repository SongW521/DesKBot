import logging
import os
import pyaudio
import numpy as np
import webrtcvad
import asyncio
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage
from sensevoice.utils.frontend import WavFrontend
from sensevoice.use_sensevoice import load_model
from myTTS import start_TTS

# 日志配置
logging.basicConfig(level=logging.INFO)

languages = {"auto": 0, "zh": 3, "en": 4, "yue": 7, "ja": 11, "ko": 12, "nospeech": 13}
model_folder = os.path.join(os.path.dirname(__file__),"sensevoice\\onnx_model")

def load_chat_llm():
    SPARKAI_URL = 'wss://spark-api.xf-yun.com/v3.5/chat'
    SPARKAI_APP_ID = '04a71e96'
    SPARKAI_API_SECRET = 'MjRmOTM3ZjI3N2JiOTE0YmU2NmM0MDFj'
    SPARKAI_API_KEY = '6acc3441099d0aeee317f86135d2d455'
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

def is_speech(frame, sample_rate=16000):
    vad = webrtcvad.Vad(1)  # 可以调整敏感度（0-3）
    return vad.is_speech(frame, sample_rate)

async def process_audio(audio_buffer, model, spark_model, systemtip):
    try:
        # 提取特征并进行语音识别
        front = WavFrontend(os.path.join(model_folder, "am.mvn"))
        audio_input = front.get_features(np.concatenate(audio_buffer))

        if len(audio_input) == 0:
            logging.warning("音频数据为空，跳过此轮处理")
            return  # 如果音频数据为空，跳过处理

        asr_result = model(audio_input[None, ...], language=languages["zh"], use_itn=False)
        texts = asr_result.rfind('>') + 1
        res_text = asr_result[texts:].strip()

        if res_text:
            print(f"识别结果: {res_text}")

            # 生成用户消息
            messages = [ChatMessage(role="system", content=systemtip)
                        ,ChatMessage(role="user", content=res_text)]

            # 向LLM发送消息并获取响应
            res = spark_model.generate([messages], callbacks=[ChunkPrintHandler()])
            text_output = res.generations[0][0].text
            print(text_output)

            # 语音合成
            start_TTS(text_output)

    except Exception as e:
        logging.error("音频识别和处理错误: %s", e)

async def real_time_speech_to_text(model, spark_model, systemtip):
    CHUNK = 320  # 20ms = 320 samples at 16kHz
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    BUFFER_SECONDS = 3  # 每次处理 1 秒的音频数据
    BUFFER_SIZE = RATE * BUFFER_SECONDS  # 缓冲区样本数（1秒）

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("开始实时语音识别...")

    audio_buffer = []
    speech_detected = False

    try:
        while True:
            data = stream.read(CHUNK)

            if is_speech(data):  # 直接传递原始字节数据
                audio_buffer.append(np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0)
                speech_detected = True
            elif speech_detected:
                if len(np.concatenate(audio_buffer)) >= BUFFER_SIZE:
                    # 处理缓冲区数据
                    await process_audio(audio_buffer, model, spark_model, systemtip)
                    # 清空音频缓冲区准备下一次
                    audio_buffer.clear()
                    speech_detected = False

    except KeyboardInterrupt:
        print("实时语音识别停止。")

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

# 从文件中读取系统提示信息
def read_system_tip(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到。")
        return None

async def main():
    # 提前加载模型
    spark = load_chat_llm()
    asr = load_model()
    # 启动时发送一次 system 消息
    systemtip = read_system_tip(r'.\systemTip.txt')
    # 启动实时语音识别
    await real_time_speech_to_text(asr, spark, systemtip)

if __name__ == "__main__":
    asyncio.run(main())
