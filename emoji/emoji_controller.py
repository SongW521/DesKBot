import os
import time
import cv2
import random
import re
import asyncio
import zmq.asyncio
from message_queen import ZMQSubscriber

class EmojiController:
    def __init__(self, base_path):
        self.stop_action = False
        self.curEmoji = "Normal"
        self.base_path = base_path

    async def doAction(self, imgpaths, isCycle=False):
        self.stop_action = False  # 允许播放新表情

        if os.path.isdir(imgpaths):
            img_list = [os.path.join(imgpaths, f) for f in os.listdir(imgpaths) if f.endswith(".jpg")]
            img_list.sort(key=lambda x: int(re.search(r'\d+', os.path.basename(x)).group()))  # 按文件名数字排序
            
            if not isCycle:
                for img in img_list:
                    if self.stop_action:  # **收到新指令，立即停止**
                        break
                    emoji = cv2.imread(img)
                    cv2.imshow("Image Viewer", emoji)
                    key = cv2.waitKey(30) & 0xFF
                    if key == ord('q'):
                        break
                    await asyncio.sleep(0.03)  # 避免阻塞
            else:
                count = 0
                while not self.stop_action:
                    emoji = cv2.imread(img_list[count])
                    cv2.imshow("Image Viewer", emoji)
                    key = cv2.waitKey(30) & 0xFF
                    if key == ord('q'):
                        break
                    count = (count + 1) % len(img_list)
                    await asyncio.sleep(0.03)

    async def doEmotionEmoji(self, emoji_type, emoji_state):
        self.stop_action = True  # 先停止当前播放
        
        state_folder = "start" if emoji_state else "end"
        img_path = os.path.join(self.base_path, emoji_type, state_folder)
        
        if emoji_state:
            await self.doAction(img_path, False)
            run_img_path = os.path.join(self.base_path, emoji_type, "run")
            await self.doAction(run_img_path, True)
        else:
            await self.doAction(img_path, False)

    async def doNormalEmoji(self, status):
        time_intervals = [1, 2, 3, 4]  # 秒级随机眨眼间隔
        num = ["run_1", "run_2"]

        while not self.stop_action:
            normal_img = os.path.join(self.base_path, status, "1.jpg")
            img = cv2.imread(normal_img)
            cv2.imshow("Image Viewer", img)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            await asyncio.sleep(random.choice(time_intervals))  # 异步等待
            await self.doRandomAction()

    async def doRandomAction(self):
        imgpaths = [
            os.path.join(self.base_path, "Blink", "run_1"),
            os.path.join(self.base_path, "Blink", "run_2"),
            os.path.join(self.base_path, "Lookleft"),
            os.path.join(self.base_path, "Lookright")
        ]
        act = random.choice(imgpaths)
        if act in (imgpaths[2], imgpaths[3]):  # 左右看
            nums = ["start", "run", "end"]
            for i in nums:
                await self.doAction(os.path.join(act, i), False)
        else:
            await self.doAction(act, False)

    async def triggerHappy(self):
        self.curEmoji = "Happy"
        print("Triggering Happy Emoji")
        await self.doEmotionEmoji(self.curEmoji, True)

    async def triggerSad(self):
        self.curEmoji = "Sad"
        print("Triggering Sad Emoji")
        await self.doEmotionEmoji(self.curEmoji, True)

    async def triggerAngry(self):
        self.curEmoji = "Angry"
        print("Triggering Angry Emoji")
        await self.doEmotionEmoji(self.curEmoji, True)

    async def triggerEnd(self):
        self.stop_action = True  # **停止当前播放**
        await self.doEmotionEmoji(self.curEmoji, False)
        print("Ending current action")

    async def triggerFear(self):
        self.curEmoji = "Fear"
        print("Triggering Fear Emoji")
        await self.doEmotionEmoji(self.curEmoji, True)

    async def triggerDisdain(self):
        self.curEmoji = "Disdain"
        print("Triggering Disdain Emoji")
        await self.doEmotionEmoji(self.curEmoji, True)

    async def listen_for_messages(self, subscriber: ZMQSubscriber):
        while not self.stop_action:
            sub_message = await subscriber.receive_message()
            if sub_message:
                sub_message = sub_message.split(' | ')[-1]
                if sub_message in emoji_callbacks:
                    print(f"Received message: {sub_message}, triggering action.")
                    
                    # 执行新表情时使用锁控制
                    self.stop_action = True  # 停止当前播放
                    await emoji_callbacks[sub_message]()  # 执行表情
                    self.stop_action = False  # 重新允许播放

# 订阅消息回调映射
emoji_callbacks = {
    "0x10": EmojiController.triggerEnd,
    "0x11": EmojiController.triggerHappy,
    "0x12": EmojiController.triggerSad,
    "0x13": EmojiController.triggerAngry,
    "0x14": EmojiController.triggerDisdain,
    "0x15": EmojiController.triggerFear,
}

# 入口函数
async def main():
    base_path = r"C:\Users\song2\Desktop\AIrobot\DeskBot\emoji\EmojiImg_ori"
    emoji_controller = EmojiController(base_path)

    subscriber = ZMQSubscriber()

    # 启动异步任务
    task_listener = asyncio.create_task(emoji_controller.listen_for_messages(subscriber))
    task_display = asyncio.create_task(emoji_controller.doNormalEmoji("Normal"))

    # 并行执行
    await asyncio.gather(task_listener, task_display)

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

    # 退出时清理
    cv2.destroyAllWindows()
