import zmq
import time
import asyncio

#发布者
class ZMQPublisher:  
    def __init__(self, address="tcp://127.0.0.1:5555"):
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(address)
        print(f"Publisher bound to {address}")

    async def send_message(self, message):
        await self.socket.send_string(message)
        print(f"Sent: {message}")

    async def close(self):
        self.socket.close()
        await self.context.term()
#订阅者
class ZMQSubscriber:
    def __init__(self, address="tcp://127.0.0.1:5555"):
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(address)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")  # 订阅所有消息
        print(f"Subscriber connected to {address}")

    async def receive_message(self):
        message = await self.socket.recv_string()
        print(f"Received: {message}")
        return message

    async def close(self):
        self.socket.close()
        await self.context.term()

