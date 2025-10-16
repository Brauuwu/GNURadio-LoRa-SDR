import numpy as np
from gnuradio import gr
import paho.mqtt.client as mqtt
import threading
import pmt

class mqtt_publisher(gr.basic_block):
    """
    MQTT Publisher (PDU Input, Raw Byte Output)
    - Nhận đầu vào là Message (PDU).
    - Gửi payload của PDU dưới dạng dữ liệu thô (raw bytes).
    """
    def __init__(self, host="127.0.0.1", port=1883,
                 username=None, password=None,
                 topic="gnuradio/output"):

        # Khối này chỉ xử lý message, không có cổng stream
        gr.basic_block.__init__(
            self,
            name="MQTT Publisher (PDU)",
            in_sig=None,
            out_sig=None
        )

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.topic = topic

        # Đăng ký cổng nhận message và hàm xử lý
        self.message_port_register_in(pmt.intern("pdu_in"))
        self.set_msg_handler(pmt.intern("pdu_in"), self.handle_pdu)

        # Cài đặt MQTT Client
        self.client = mqtt.Client()
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        self.client.on_connect = self.on_connect
        self.mqtt_thread = threading.Thread(target=self._mqtt_loop, daemon=True)
        self.mqtt_thread.start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] Publisher (PDU, Raw) connected to broker")
        else:
            print("[MQTT] Publisher connection failed, rc=", rc)

    def _mqtt_loop(self):
        try:
            self.client.connect(self.host, self.port, keepalive=60)
            self.client.loop_forever()
        except Exception as e:
            print(f"[MQTT] Connection error: {e}")

    def handle_pdu(self, msg):
        """
        Hàm được gọi khi có PDU đến.
        Trích xuất payload và publish dưới dạng raw bytes.
        """
        # Kiểm tra PDU có chứa u8vector không
        if not pmt.is_u8vector(pmt.cdr(msg)):
            print("[MQTT Publisher] Received a PDU without a u8vector payload. Ignoring.")
            return
        
        # Trích xuất payload và chuyển sang đối tượng bytes của Python
        payload_pmt = pmt.cdr(msg)
        data_bytes = bytes(pmt.u8vector_elements(payload_pmt))
        
        # Gửi trực tiếp payload dạng bytes
        self.client.publish(self.topic, data_bytes)
        
        # Tùy chọn: In log để gỡ lỗi (bỏ comment nếu cần)
        # print(f"[MQTT] Published {len(data_bytes)} raw bytes.")
