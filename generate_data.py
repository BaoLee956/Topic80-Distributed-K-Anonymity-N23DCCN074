import json
import random

# Danh sách các bệnh ngẫu nhiên
DISEASES = ["Flu", "COVID-19", "Diabetes", "Hypertension", "Asthma", "Cancer", "Heart Disease"]

# Khởi tạo danh sách dữ liệu
data = []
record_id = 1

def add_record(age, zipcode, disease=None):
    global record_id
    data.append({
        "id": record_id,
        "age": age,
        "zipcode": str(zipcode),
        "disease": disease if disease else random.choice(DISEASES)
    })
    record_id += 1

# ==========================================
# 1. CẤY DỮ LIỆU CHO TEST CASE 1.1 (Hoàn hảo k >= 3)
# Mục đích: Test hệ thống có dừng ngay lập tức khi đã có đủ 3 người giống hệt nhau không.
# ==========================================
for _ in range(4): # Tạo 4 người giống hệt nhau
    add_record(30, "70100")

# ==========================================
# 2. CẤY DỮ LIỆU CHO TEST CASE 1.2 (Outlier - Cô độc)
# Mục đích: Test hệ thống có bị lặp vô hạn khi không thể gom đủ 3 người không.
# ==========================================
add_record(115, "99999", "Rare Alien Disease") # Chỉ có duy nhất 1 người này trên toàn mạng lưới

# ==========================================
# 3. CẤY DỮ LIỆU CHO TEST CASE 2.1 (Làm mờ sai thứ tự)
# Mục đích: Ép thuật toán phải che ZipCode trước (thành 1000*) để gom đủ 3 người, không được phép cộng/trừ tuổi.
# ==========================================
add_record(45, "10001")
add_record(45, "10002")
add_record(45, "10009")

# ==========================================
# 4. DỮ LIỆU RANDOM (Cho Stress Test và kiểm tra Phân mảnh Sharding)
# Mục đích: Tạo độ nhiễu và số lượng lớn để test chia Round-Robin cho 3 Node.
# ==========================================
for _ in range(150):
    random_age = random.randint(20, 80)
    # Tạo zipcode quanh khu vực 70xxx để dễ gom nhóm ngẫu nhiên
    random_zip = f"70{random.randint(100, 999)}"
    add_record(random_age, random_zip)

# Trộn ngẫu nhiên (Shuffle) dữ liệu để đảm bảo thuật toán phân mảnh Round-Robin (idx % 3)
# sẽ rải đều các trường hợp đặc biệt (như 4 người 30 tuổi) ra cả 3 Node, ép các Node phải giao tiếp với nhau.
random.shuffle(data)

# Cập nhật lại ID sau khi trộn để ID chạy tuần tự
for idx, record in enumerate(data):
    record["id"] = idx + 1

# Xuất ra file data.json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=4, ensure_ascii=False)

print(f"Đã tạo thành công data.json với {len(data)} bản ghi!")
print("Các trường hợp đặc biệt đã được cấy vào dữ liệu thành công.")