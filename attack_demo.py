import json
import requests
import time

def print_header(title):
    print(f"\n{'='*75}")
    print(f" {title} ".center(75, '='))
    print(f"{'='*75}\n")

def attack_raw_data(target_age, target_zip, filepath='data.json'):
    print("[-] Đang quét trực tiếp vào cơ sở dữ liệu y tế thô (data.json)...")
    time.sleep(1.5)
    
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Tìm kiếm những người khớp chính xác 100% với thông tin nhập vào
        matches = []
        for row in data:
            age = str(row.get('Age', row.get('age', '')))
            zipcode = str(row.get('ZipCode', row.get('zipcode', '')))
            if age == target_age and zipcode == target_zip:
                matches.append(row)
                
        if len(matches) == 1:
            disease = matches[0].get('Disease', matches[0].get('disease', ''))
            print("[🚨 LỖ HỔNG CHÍ MẠNG] HACKER ĐÃ TÌM TRÚNG ĐÍCH DANH 1 NGƯỜI DUY NHẤT!")
            print(f"    => Căn bệnh nhạy cảm bị phơi bày: {disease}\n")
        elif len(matches) == 0:
            print("[!] Dữ liệu thô không có hồ sơ nào khớp với thông tin này.\n")
        else:
            diseases = [m.get('Disease', m.get('disease', '')) for m in matches]
            print(f"[!] Tìm thấy {len(matches)} người. Chưa định danh được 1 cá nhân, nhưng biết nhóm này mắc các bệnh: {', '.join(diseases)}\n")
            
    except Exception as e:
        print(f"[LỖI] Không thể đọc file dữ liệu gốc: {e}\n")

def attack_k_anonymity(target_age, target_zip):
    print("[-] Đang gửi truy vấn để mò dữ liệu qua mạng lưới phân tán P2P (Node 8001)...")
    time.sleep(1.5)
    
    try:
        res = requests.get("http://127.0.0.1:8001/anonymize", params={"age": target_age, "zip_code": target_zip})
        if res.status_code == 200:
            result = res.json()
            gen_data = result.get('generalized_data', {})
            age_result = gen_data.get('age', gen_data.get('Age', '[Lỗi lấy Tuổi]'))
            zip_result = gen_data.get('zip_code', gen_data.get('ZipCode', '[Lỗi lấy Zip]'))
            print("[🛡️ AN TOÀN] HỆ THỐNG ĐÃ KÍCH HOẠT LÀM MỜ & CHẶN ĐỨNG CUỘC TẤN CÔNG!")
            print(f"    -> Kết quả trả về đã bị làm mờ thành: Tuổi {age_result}, Mã vùng {zip_result}")
            print(f"    -> Hacker nhận về một đám đông gồm {result.get('total_count')} người (đạt chuẩn k >= 3).")
            print(f"    -> Kẻ tấn công HOÀN TOÀN BẤT LỰC, không thể chốt được mục tiêu là ai!")
            print(f"    -> (Thông số kỹ thuật: Lặp {result.get('iterations')} vòng, Điểm phạt Info Loss = {result.get('info_loss')})\n")
        else:
            print(f"[LỖI API] Trạng thái: {res.status_code} - Vui lòng kiểm tra Node 8001.\n")
    except Exception as e:
        print("[!] Không kết nối được API. Hãy đảm bảo chạy lệnh python app.py --port 8001 ...\n")

def run_interactive():
    print_header("TERMINAL HACKER: TẤN CÔNG ĐỊNH DANH NGƯỢC (RE-IDENTIFICATION)")
    print("Giả lập: Bạn đang nắm trong tay thông tin tình báo của một nạn nhân.")
    
    # Cho phép người dùng nhập trực tiếp từ bàn phím
    target_age = input(">> Nhập số Tuổi (Age) của nạn nhân: ").strip()
    target_zip = input(">> Nhập Mã bưu điện (ZipCode) của nạn nhân: ").strip()
    
    print("\n" + "-"*50)
    print(">>> KỊCH BẢN 1: HỆ THỐNG KHÔNG BẢO MẬT (RAW DATA)")
    attack_raw_data(target_age, target_zip)
    
    print("-"*50)
    print(">>> KỊCH BẢN 2: HỆ THỐNG DISTRIBUTED K-ANONYMITY")
    attack_k_anonymity(target_age, target_zip)

if __name__ == "__main__":
    run_interactive()