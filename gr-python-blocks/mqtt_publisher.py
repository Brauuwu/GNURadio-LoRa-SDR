import numpy as np
from gnuradio import gr
import paho.mqtt.client as mqtt
import threading
import queue


class mqtt_publisher(gr.sync_block):
    """
    MQTT Publisher Block (Local Broker)
    - Nhận byte stream từ GNU Radio
    - Gom thành chuỗi (theo '\n') và publish lên MQTT
    """

    def __init__(self, host="127.0.0.1", port=1883,
                 username=None, password=None,
                 topic="gnuradio/output"):
        gr.sync_block.__init__(
            self,
            name="MQTT Publisher",
            in_sig=[np.uint8],
            out_sig=None
        )

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic

        self.buffer = bytearray()

        # MQTT client
        self.client = mqtt.Client()
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self.on_connect

        # Thread MQTT
        self.mqtt_thread = threading.Thread(target=self._mqtt_loop, daemon=True)
        self.mqtt_thread.start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] Publisher connected to local broker")
        else:
            print("[MQTT] Publisher failed, rc=", rc)

    def _mqtt_loop(self):
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_forever()

    def work(self, input_items, output_items):
        data = input_items[0]
        
        if len(data) > 0:
            msg = bytes(data).decode("utf-8", errors="ignore")
            if msg.strip():
                self.client.publish(self.topic, msg)
                print(f"[MQTT] Published: {msg}")

        return len(data)

