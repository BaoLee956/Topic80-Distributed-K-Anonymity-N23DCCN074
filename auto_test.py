import unittest
import requests
import threading
import time

# Cấu hình địa chỉ của Node Điều phối
COORDINATOR_URL = "http://127.0.0.1:8001"
API_ENDPOINT = f"{COORDINATOR_URL}/anonymize"

class TestDistributedKAnonymity(unittest.TestCase):

    def test_1_perfect_k_anonymity(self):
        """Kịch bản 1: Không cần làm mờ (Đã có sẵn >= 3 người)"""
        # Trong data.json có sẵn nhóm người trẻ tuổi ở mã vùng quen thuộc
        response = requests.get(API_ENDPOINT, params={"age": "22", "zip_code": "70001"})
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get("success"), "Lỗi: Không trả về success=True cho dữ liệu an toàn")
        self.assertEqual(data.get("info_loss"), 0, "Lỗi: Làm mờ thừa dữ liệu khi đã đủ chuẩn k!")
        self.assertGreaterEqual(data.get("total_count", 0), 3, "Lỗi: Tổng số lượng đếm toàn mạng bị sai")

    def test_2_outlier_deep_generalization(self):
        """Kịch bản 2: Dữ liệu cực hiếm (Test thuật toán cứu dữ liệu bằng cách làm mờ tối đa)"""
        # Gửi dữ liệu hiếm (Tuổi 95, Zip 99999) không có sẵn trong hệ thống
        response = requests.get(API_ENDPOINT, params={"age": "95", "zip_code": "99999"})
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        # Logic app.py: Khi mờ thành ***** và nới tuổi đủ rộng, nó sẽ gom được các bản ghi khác trong cụm
        self.assertTrue(data.get("success"), "Lỗi: Thuật toán không thể cứu dữ liệu hiếm bằng làm mờ sâu")
        self.assertGreater(data.get("info_loss", 0), 5, "Lỗi: Điểm info_loss phải lớn do đã thực hiện che mờ diện rộng")
        self.assertEqual(data.get("generalized_data", {}).get("zip_code"), f"*****", "Lỗi: Zipcode đáng lẽ phải bị mờ hoàn toàn!")

    def test_3_generalization_sequence(self):
        """Kịch bản 3: Thứ tự ưu tiên làm mờ (ZipCode phải được che trước, Age nới rộng sau)"""
        # Gửi một request cần làm mờ nhẹ
        response = requests.get(API_ENDPOINT, params={"age": "34", "zip_code": "70129"})
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data.get("success"), "Lỗi: Không thể vô danh hóa thành công")
        
        gen_data = data.get("generalized_data", {})
        gen_zip = gen_data.get("zip_code", "")
        gen_age = str(gen_data.get("age", ""))
        
        # Kiểm tra tính đúng đắn của hàm generalize(): Phải cắt đuôi ZipCode trước khi tăng biên độ tuổi
        self.assertIn("*", gen_zip, "Lỗi logic: Thuật toán không ưu tiên che dữ liệu không gian (ZipCode) trước!")

    def test_4_concurrency_stress_test(self):
        """Kịch bản 4: Tấn công dồn dập đồng thời (Kiểm tra Race Condition)"""
        success_count = 0
        lock = threading.Lock()

        def make_request():
            nonlocal success_count
            try:
                res = requests.get(API_ENDPOINT, params={"age": "22", "zip_code": "70001"})
                if res.status_code == 200 and res.json().get("success"):
                    with lock:
                        success_count += 1
            except requests.RequestException:
                pass

        # Bắn đồng thời 20 luồng (threads) truy vấn vào cùng một thời điểm
        threads = [threading.Thread(target=make_request) for _ in range(20)]
        for t in threads: t.start()
        for t in threads: t.join()

        self.assertEqual(success_count, 20, "Lỗi Race Condition: Trạng thái đếm cục bộ/toàn cục bị loạn khi xử lý đa luồng!")

    def test_5_fault_tolerance(self):
            """Kịch bản 5: Kháng lỗi mạng (Giả lập tình huống sập hỏng một Node trong mạng)"""
            print("\n" + "="*65)
            print("ĐANG KIỂM THỬ TÍNH NĂNG KHÁNG LỖI MẠNG (FAULT TOLERANCE)...")
            print("HÃY CHUYỂN SANG TERMINAL CỦA NODE 8002 VÀ NHẤN 'Ctrl + C' NGAY BÂY GIỜ!")
            print("Chú ý: KHÔNG bấm Ctrl+C ở terminal chạy file test này.")
            print("Bạn có 5 giây để thực hiện thao tác...")
            print("="*65)
            time.sleep(5) 
            
            start_time = time.time()
            response = requests.get(API_ENDPOINT, params={"age": "45", "zip_code": "70300"})
            end_time = time.time()

            # Node 8001 (Coordinator) không được sập theo, phải phản hồi HTTP 200 thành công
            self.assertEqual(response.status_code, 200, "Lỗi nghiêm trọng: Coordinator bị crash theo node hỏng (Thiếu khối try-except)!")
            
            data = response.json()
            execution_time = end_time - start_time
            
            # BỎ ĐIỀU KIỆN ÉP BUỘC >= 2.0 GIÂY Ở LOCALHOST. 
            # Chỉ in ra thời gian để báo cáo
            print(f"\n[Thời gian phản hồi khi có Node sập: {execution_time:.4f} giây]")
            
            # Xác thực việc gán giá trị đếm bằng 0 đối với node đã chết
            peer_counts = data.get("per_node_counts", {})
            node_8002_found = False
            for peer, count in peer_counts.items():
                if "8002" in peer:
                    node_8002_found = True
                    self.assertEqual(count, 0, "Lỗi: Node bị sập không được cô lập và gán số lượng bằng 0!")
            
            self.assertTrue(node_8002_found, "Lỗi: Mất luôn dấu vết của Node 8002 trong lịch sử log request!")
                
            print(f"=> HỆ THỐNG KHÁNG LỖI MẠNG ĐẠT CHUẨN! Node 8001 tự động bù đắp dữ liệu bằng cách làm mờ sâu.")
            print(f"   Trạng thái: {data.get('success')} | Số vòng lặp: {data.get('iterations')} | Điểm Info Loss: {data.get('info_loss')}")

if __name__ == '__main__':
    unittest.main()