import numpy as np
from gnuradio import gr
import adi
import time

class pluto_gain_stream_source(gr.sync_block):
    """
    GRC Block: Đọc Hardware Gain từ Pluto và xuất ra dưới dạng Byte Stream (cổng tím).

    PHIÊN BẢN SỬA ĐỔI: Khối này tạo ra một luồng byte thay vì message.
    Đây là cách làm phức tạp hơn và ít được khuyến khích.
    """
    def __init__(self, sdr_uri='ip:192.168.2.1', update_interval=1.0):
        gr.sync_block.__init__(
            self,
            name='Pluto Gain Source',
            in_sig=[],
            # ĐỊNH NGHĨA ĐẦU RA LÀ BYTE STREAM (màu tím)
            out_sig=[np.byte]
        )

        self.sdr_uri = sdr_uri
        self.update_interval = update_interval
        self.last_update_time = 0
        
        # Bộ đệm (buffer) nội bộ để chứa các byte đang chờ được gửi đi
        self.pending_bytes = bytearray()

    def work(self, input_items, output_items):
        out_buffer = output_items[0]
        n_out = len(out_buffer) # Số byte có thể ghi ra ở lần gọi này
        
        current_time = time.time()
        
        # 1. Kiểm tra xem đã đến lúc đọc giá trị mới từ SDR chưa
        if (current_time - self.last_update_time) > self.update_interval:
            self.last_update_time = current_time
            
            try:
                sdr = adi.Pluto(self.sdr_uri)
                gain_raw = sdr._ctrl.find_channel('voltage0').attrs['hardwaregain'].value
                gain_str = str(int(float(gain_raw.split()[0])))
                
                # Thêm dữ liệu mới (đã mã hóa) vào bộ đệm đang chờ
                self.pending_bytes.extend(gain_str.encode('utf-8'))
                del sdr
            except Exception as e:
                print(f"[Pluto Gain Stream] Lỗi: {e}")

        # 2. Kiểm tra xem có byte nào đang chờ trong bộ đệm không
        if len(self.pending_bytes) > 0:
            # Xác định số byte sẽ được ghi ra lần này
            num_to_write = min(n_out, len(self.pending_bytes))
            
            # Sao chép byte từ bộ đệm đang chờ sang bộ đệm đầu ra
            out_buffer[:num_to_write] = self.pending_bytes[:num_to_write]
            
            # Xóa các byte đã được ghi khỏi bộ đệm đang chờ
            self.pending_bytes = self.pending_bytes[num_to_write:]
            
            # Trả về số byte đã thực sự ghi ra
            return num_to_write
        else:
            # Nếu không có gì để ghi, trả về 0
            return 0
