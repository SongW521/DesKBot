
import logging
import os
import time
from pydub import AudioSegment
import sys
import pyaudio
import numpy as np
from sensevoice.onnx.sense_voice_ort_session import SenseVoiceInferenceSession
from sensevoice.utils.frontend import WavFrontend

languages = {"auto": 0, "zh": 3, "en": 4, "yue": 7, "ja": 11, "ko": 12, "nospeech": 13}
formatter = "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
logging.basicConfig(format=formatter, level=logging.INFO)
# 指定模型的文件夹路径
model_folder = model_folder = os.path.join(os.path.dirname(__file__),"onnx_model")

def load_model():
    # 检查模型文件夹是否存在
    if not os.path.exists(model_folder):
        logging.error(f"Model folder '{model_folder}' does not exist.")
        return
    model = SenseVoiceInferenceSession(
        os.path.join(model_folder, "embedding.npy"),
        os.path.join(model_folder, "model_int8.onnx"),  # 使用新的模型文件名
        os.path.join(model_folder, "chn_jpn_yue_eng_ko_spectok.bpe.model"),
        
    )
    return model


def convert_audio(input_file, output_file):
    # 读取音频文件
    audio = AudioSegment.from_file(input_file)

    # 转换采样率为16000Hz
    audio = audio.set_frame_rate(16000)

    # 导出转换后的音频文件
    audio.export(output_file, format="wav")

    print(f"音频转换完成: {output_file}")


def speech_to_text(audio_file,model):
    
    #转换采样率
    convert_audio(audio_file,audio_file)

    
    front = WavFrontend(os.path.join(model_folder, "am.mvn"))
    audio_input = front.get_features(audio_file)
    logging.info(f"{audio_file} 音频时长： {0.06 * len(audio_input)} S")
    start = time.time()
    asr_result = model(
        audio_input[None, ...], language=languages["auto"], use_itn=False
    )
    texts = asr_result.rfind('>') + 1
    res_text = asr_result[texts:].strip()

    print(res_text)
    # decoding_time = time.time() - start
    # logging.info(f"Decoder audio takes {decoding_time} seconds")
    # logging.info(f"The RTF is {decoding_time / (0.06 * len(audio_input))}.")

    return res_text

def real_time_speech_to_text(model):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("开始实时语音识别...")

    try:
        while True:
            start_time = time.time()
            audio_buffer = []

            # 记录两秒的音频数据
            while time.time() - start_time < 2:
                data = stream.read(CHUNK)
                audio_buffer.append(np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0)

            # 将音频数据拼接在一起
            audio_data = np.concatenate(audio_buffer)

            # 提取特征并进行语音识别
            front = WavFrontend(os.path.join(model_folder, "am.mvn"))
            audio_input = front.get_features(audio_data)

            asr_result = model(audio_input[None, ...], language=languages["auto"], use_itn=False)
            texts = asr_result.rfind('>') + 1
            res_text = asr_result[texts:].strip()

            if res_text:
                print(f"识别结果: {res_text}")

    except KeyboardInterrupt:
        print("实时语音识别停止。")
    
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

def main():
    use_model = load_model()
    # 指定当前文件夹下的音频文件名
    audio_file = r"C:\Users\song2\Desktop\AIrobot\DeskBot\voice\voice.wav" 
    speech_to_text(audio_file,use_model)
    # real_time_speech_to_text(use_model)
if __name__ == "__main__":
    main()
