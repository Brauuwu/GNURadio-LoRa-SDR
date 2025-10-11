import numpy as np
from gnuradio import gr
import paho.mqtt.client as mqtt
import threading
import queue

class mqtt_subscriber(gr.sync_block):
    """
    MQTT Subscriber Block (Local Broker)
    - Nhận message từ Node-RED hoặc client MQTT khác
    - Segment payload thành subpayload (<= max_len, thêm '\n')
    - Xuất ra stream GNU Radio (byte)
    """

    def __init__(self, host="127.0.0.1", port=1883,
                 username=None, password=None,
                 topic="gnuradio/input", buf_len=1024, max_len=255):
        gr.sync_block.__init__(
            self,
            name="MQTT Subscriber",
            in_sig=None,
            out_sig=[np.uint8]
        )

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic
        self.buf_len = buf_len
        self.max_len = max_len

        self.queue = queue.Queue()

        # MQTT client
        self.client = mqtt.Client()
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        # Thread MQTT
        self.mqtt_thread = threading.Thread(target=self._mqtt_loop, daemon=True)
        self.mqtt_thread.start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] Connected to local broker")
            client.subscribe(self.topic)
        else:
            print("[MQTT] Failed to connect, rc=", rc)

    def on_message(self, client, userdata, msg):
        text = msg.payload.decode("utf-8")
        print(f"[MQTT] Received: {text}")

        # Segmenter
        data = text.encode("utf-8")
        for i in range(0, len(data), self.max_len):
            sub = data[i:i + self.max_len]
            if len(sub) < 2:
                sub = sub + b' '
            sub = sub + b'\n'
            arr = np.frombuffer(sub, dtype=np.uint8)
            for b in arr:
                self.queue.put(b)

    def _mqtt_loop(self):
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_forever()

    def work(self, input_items, output_items):
        out = output_items[0]

        i = 0
        while not self.queue.empty() and i < len(out):
            out[i] = self.queue.get()
            i += 1

        return i
