"""
Embedded Python Blocks:

Mỗi lần tệp này được lưu, GRC sẽ khởi tạo lớp đầu tiên mà nó tìm thấy
để lấy các cổng và tham số của khối của bạn. Các đối số của __init__
sẽ là các tham số. Tất cả chúng đều phải có giá trị mặc định!
"""

import numpy as np
from gnuradio import gr
import pmt  # Thư viện cần thiết để xử lý message

class msg_to_byte_stream(gr.sync_block):
    """
    Khối Python chuyển đổi dữ liệu từ Message Port thành Byte Stream.
    
    - Đầu vào: Một message port tên là 'msg_in' (màu xám).
    - Đầu ra: Một stream port kiểu Byte (màu tím).
    """

    def __init__(self):  # Khối này không cần tham số
        """
        Hàm khởi tạo này sẽ được gọi khi GRC tạo khối.
        """
        gr.sync_block.__init__(
            self,
            name='Async to Char',  # Tên sẽ hiển thị trong GRC
            in_sig=[],  # Không có đầu vào dạng stream
            out_sig=[np.byte]  # Đầu ra là một luồng byte (màu tím)
        )
        
        # 1. Đăng ký một cổng nhận message có tên là 'msg_in'
        self.message_port_register_in(pmt.intern('msg_in'))
        
        # 2. Thiết lập hàm 'handle_msg' để xử lý bất kỳ message nào đến cổng 'msg_in'
        self.set_msg_handler(pmt.intern('msg_in'), self.handle_msg)
        
        # 3. Tạo một bộ đệm (buffer) nội bộ để lưu trữ các byte từ message
        #    trước khi chúng được gửi ra stream.
        self.buffer = bytearray()

    def handle_msg(self, msg):
        """
        Hàm này là một "callback", nó sẽ tự động được gọi mỗi khi
        một message được gửi đến cổng 'msg_in'.
        """
        # Kiểm tra xem message có phải là PDU hợp lệ không (dạng pair)
        if pmt.is_pair(msg):
            # Trích xuất payload (phần thân) của message
            payload = pmt.cdr(msg)
            
            # Kiểm tra xem payload có phải là một vector byte (u8vector) không
            if pmt.is_u8vector(payload):
                # Chuyển đổi u8vector thành một đối tượng byte của Python
                # và thêm vào cuối bộ đệm nội bộ của chúng ta.
                self.buffer.extend(pmt.u8vector_elements(payload))
        # Nếu message không hợp lệ, nó sẽ bị bỏ qua.

    def work(self, input_items, output_items):
        """
        Hàm work() được scheduler của GNU Radio gọi liên tục để xử lý dữ liệu stream.
        """
        # Lấy bộ đệm đầu ra mà chúng ta có thể ghi vào
        out = output_items[0]
        
        # Số lượng byte tối đa chúng ta có thể ghi trong lần gọi này
        n_out = len(out)
        
        # Kiểm tra xem bộ đệm nội bộ của chúng ta có dữ liệu để gửi đi không
        if len(self.buffer) > 0:
            # Xác định số byte sẽ được ghi: là số nhỏ hơn giữa
            # số byte đang chờ và không gian có sẵn trong bộ đệm đầu ra.
            num_to_write = min(n_out, len(self.buffer))
            
            # Sao chép dữ liệu từ bộ đệm nội bộ sang bộ đệm đầu ra
            out[:num_to_write] = self.buffer[:num_to_write]
            
            # Xóa các byte đã được ghi khỏi bộ đệm nội bộ
            self.buffer = self.buffer[num_to_write:]
            
            # Trả về số byte đã được ghi ra
            return num_to_write
        else:
            # Nếu không có dữ liệu trong bộ đệm, không ghi gì cả
            return 0
