import zmq
import time

class ZMQPublisher:
    def __init__(self, address="tcp://127.0.0.1:5555"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(address)
        print(f"Publisher bound to {address}")
    
    def send_message(self, message):
        self.socket.send_string(message)
        print(f"Sent: {message}")
    
    def close(self):
        self.socket.close()
        self.context.term()

class ZMQSubscriber:
    def __init__(self, address="tcp://127.0.0.1:5555"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket.connect(address)
        self.socket.setsockopt_string(zmq.SUBSCRIBE, "")  # 订阅所有消息
        print(f"Subscriber connected to {address}")
    
    def receive_message(self):
        message = self.socket.recv_string()
        print(f"Received: {message}")
    
    def close(self):
        self.socket.close()
        self.context.term()

