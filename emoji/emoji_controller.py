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
async def doAction(imgpaths, isCycle=False):
    global stop_action
    stop_action = False  # 允许播放新表情

    if os.path.isdir(imgpaths):
        img_list = [os.path.join(imgpaths, f) for f in os.listdir(imgpaths) if f.endswith(".jpg")]
        img_list.sort(key=lambda x: int(re.search(r'\d+', os.path.basename(x)).group()))  # 按文件名数字排序
        
        if not isCycle:
            for img in img_list:
                if stop_action:  # **收到新指令，立即停止**
                    break
                emoji = cv2.imread(img)
                cv2.imshow("Image Viewer", emoji)
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    break
                await asyncio.sleep(0.03)  # 避免阻塞
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

# 表情播放
async def doEmotionEmoji(emoji_type, emoji_state):
    global stop_action
    stop_action = True  # 先停止当前播放
    
    state_folder = "start" if emoji_state else "end"
    img_path = os.path.join(base_path, emoji_type, state_folder)
    
    if emoji_state:
        await doAction(img_path, False)
        run_img_path = os.path.join(base_path, emoji_type, "run")
        await doAction(run_img_path, True)
    else:
        await doAction(img_path, False)

# 默认状态
async def doNormalEmoji(status):
    global stop_action
    time_intervals = [1, 2, 3, 4]  # 秒级随机眨眼间隔
    num = ["run_1", "run_2"]

    while not stop_action:
        normal_img = os.path.join(base_path, status, "1.jpg")
        img = cv2.imread(normal_img)
        cv2.imshow("Image Viewer", img)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        await asyncio.sleep(random.choice(time_intervals))  # 异步等待
        await doRandomAction()

# 随机动作
async def doRandomAction():
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
            await doAction(os.path.join(act, i), False)
    else:
        await doAction(act, False)

# 表情回调
async def triggerHappy():
    global curEmoji
    curEmoji = "Happy"
    print("Triggering Happy Emoji")
    await doEmotionEmoji(curEmoji, True)

async def triggerSad():
    global curEmoji
    curEmoji = "Sad"
    print("Triggering Sad Emoji")
    await doEmotionEmoji(curEmoji, True)

async def triggerAngry():
    global curEmoji
    curEmoji = "Angry"
    print("Triggering Angry Emoji")
    await doEmotionEmoji(curEmoji, True)

async def triggerEnd():
    global stop_action
    stop_action = True  # **停止当前播放**
    await doEmotionEmoji(curEmoji, False)
    print("Ending current action")

async def triggerFear():
    global curEmoji
    curEmoji = "Fear"
    print("Triggering Fear Emoji")
    await doEmotionEmoji(curEmoji, True)

async def triggerDisdain():
    global curEmoji
    curEmoji = "Disdain"
    print("Triggering Disdain Emoji")
    await doEmotionEmoji(curEmoji, True)

# 订阅消息回调映射
emoji_callbacks = {
    "0x10": triggerEnd,
    "0x11": triggerHappy,
    "0x12": triggerSad,
    "0x13": triggerAngry,
    "0x14": triggerDisdain,
    "0x15": triggerFear,
}

# 监听消息（异步）
async def listen_for_messages(subscriber: ZMQSubscriber):
    global stop_action
    while not stop_action:
        sub_message = await subscriber.receive_message()
        if sub_message:
            sub_message = sub_message.split(' | ')[-1]
            if sub_message in emoji_callbacks:
                print(f"Received message: {sub_message}, triggering action.")
                
                # 执行新表情时使用锁控制
                stop_action = True  # 停止当前播放
                await emoji_callbacks[sub_message]()  # 执行表情
                stop_action = False  # 重新允许播放

# 入口函数
async def main():
    global stop_action
    stop_action = False

    subscriber = ZMQSubscriber()

    # 启动异步任务
    task_listener = asyncio.create_task(listen_for_messages(subscriber))
    task_display = asyncio.create_task(doNormalEmoji("Normal"))

    # 并行执行
    await asyncio.gather(task_listener, task_display)

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

    # 退出时清理
    cv2.destroyAllWindows()
