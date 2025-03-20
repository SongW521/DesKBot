import os
import time
import cv2
import random
import re
import asyncio
import zmq.asyncio
from message_queen import ZMQSubscriber

# 全局变量
stop_action = False
curEmoji = "Normal"
base_path = r"C:\Users\song2\Desktop\AIrobot\DeskBot\emoji\EmojiImg_ori"

# 异步表情播放函数
async def playEmoji():
    global stop_action, curEmoji
    previous_emoji = None  # 记录上一次的表情类型
    while True:
        if stop_action:
            await asyncio.sleep(0.1)  # 等待停止信号解除
            continue

        # 如果表情类型发生变化，重新加载表情
        if curEmoji != previous_emoji:
            print(f"Switching to new emoji: {curEmoji}")
            previous_emoji = curEmoji

        # 根据当前表情类型选择路径
        if curEmoji == "Normal":
            await playNormalEmoji()
        else:
            await playEmotionEmoji(curEmoji)

# 播放默认表情
async def playNormalEmoji():
    global stop_action
    time_intervals = [1, 2, 3, 4]  # 秒级随机眨眼间隔
    normal_img = os.path.join(base_path, "Normal", "1.jpg")

    while not stop_action and curEmoji == "Normal":
        img = cv2.imread(normal_img)
        cv2.imshow("Image Viewer", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        await asyncio.sleep(random.choice(time_intervals))  # 异步等待
        await playRandomAction()

# 播放随机动作
async def playRandomAction():
    global stop_action
    imgpaths = [
        os.path.join(base_path, "Blink", "run_1"),
        os.path.join(base_path, "Blink", "run_2"),
        os.path.join(base_path, "Lookleft"),
        os.path.join(base_path, "Lookright")
    ]
    act = random.choice(imgpaths)
    if act in (imgpaths[2], imgpaths[3]):  # 左右看
        nums = ["start", "run", "end"]
        for i in nums:
            if stop_action:
                break
            await playAction(os.path.join(act, i), False)
    else:
        await playAction(act, False)

# 播放情绪表情
async def playEmotionEmoji(emoji_type):
    global stop_action
    state_folder = "start"
    img_path = os.path.join(base_path, emoji_type, state_folder)

    if not stop_action:
        await playAction(img_path, False)

    run_img_path = os.path.join(base_path, emoji_type, "run")
    while not stop_action and curEmoji == emoji_type:
        await playAction(run_img_path, True)

# 播放具体动作
async def playAction(imgpaths, isCycle=False):
    global stop_action
    if os.path.isdir(imgpaths):
        img_list = [os.path.join(imgpaths, f) for f in os.listdir(imgpaths) if f.endswith(".jpg")]
        img_list.sort(key=lambda x: int(re.search(r'\d+', os.path.basename(x)).group()))  # 按文件名数字排序

        if not isCycle:
            for img in img_list:
                if stop_action:
                    break
                emoji = cv2.imread(img)
                cv2.imshow("Image Viewer", emoji)
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    break
                await asyncio.sleep(0.03)
        else:
            count = 0
            while not stop_action:
                emoji = cv2.imread(img_list[count])
                cv2.imshow("Image Viewer", emoji)
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    break
                count = (count + 1) % len(img_list)
                await asyncio.sleep(0.03)

# 监听消息
async def listenForMessages(subscriber: ZMQSubscriber):
    global curEmoji, stop_action
    while True:
        sub_message = await subscriber.receive_message()
        if sub_message:
            sub_message = sub_message.split(' | ')[-1]
            if sub_message in emoji_callbacks:
                print(f"Received message: {sub_message}, triggering action.")
                stop_action = True  # 停止当前表情
                curEmoji = emoji_callbacks[sub_message]  # 更新当前表情
                stop_action = False  # 允许播放新表情
                print(f"当前表情: {curEmoji}")

# 表情回调映射
emoji_callbacks = {
    "0x10": "Normal",
    "0x11": "Happy",
    "0x12": "Sad",
    "0x13": "Angry",
    "0x14": "Disdain",
    "0x15": "Fear",
}

# 主函数
async def main():
    global stop_action
    stop_action = False

    subscriber = ZMQSubscriber()

    # 启动表情播放和消息监听
    await asyncio.gather(
        playEmoji(),
        listenForMessages(subscriber)
    )

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

    # 退出时清理
    cv2.destroyAllWindows()