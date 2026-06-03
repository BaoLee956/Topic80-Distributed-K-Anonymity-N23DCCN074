import json
import random
import time
import os

DISEASES = ["Flu", "COVID-19", "Diabetes", "Hypertension", "Asthma", "Cancer", "Heart Disease"]
raw_data = []

print("\n" + "="*70)
print(" HỆ THỐNG TIỀN XỬ LÝ DỮ LIỆU Y TẾ (DATA PIPELINE) ".center(70, "="))
print("="*70)
time.sleep(0.5)

# ==========================================
# GIAI ĐOẠN 0: ĐỌC DỮ LIỆU CŨ TỪ DATA.JSON
# ==========================================
if os.path.exists('data.json'):
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            raw_data.extend(existing_data)
        print(f"[0] Đã đọc {len(existing_data)} bản ghi có sẵn từ file data.json.")
    except Exception:
        print(f"[0] Không thể đọc file data.json cũ. Tạo mới hoàn toàn.")
else:
    print("[0] Không tìm thấy data.json cũ. Tiến hành tạo mới.")

# ==========================================
# GIAI ĐOẠN 1: BƠM THÊM DỮ LIỆU MỚI (CÓ LỖI)
# ==========================================
print("\n[1] Đang bơm thêm dữ liệu mới từ các Trạm y tế...")
time.sleep(0.5)

def add_record(age, zipcode, disease=None):
    raw_data.append({
        "Age": str(age),
        "ZipCode": str(zipcode),
        "Disease": disease if disease else random.choice(DISEASES)
    })

# Kịch bản k=4
add_record(30, "70100", "Flu")
add_record(30, "70100", "Cancer")
add_record(30, "70100", "Diabetes")
add_record(30, "70100", "Asthma")

# Kịch bản outlier
add_record(115, "99999", "Rare Alien Disease")

# Bơm dữ liệu lỗi (Trùng 15 lần - tức là 1 gốc và 14 bản sao rác)
for _ in range(15):
    add_record(25, "70222", "COVID-19")

# Dữ liệu ngẫu nhiên
for _ in range(150): 
    add_record(random.randint(20, 80), f"70{random.randint(100, 999)}")

print(f"    -> Kho chứa tạm thời đang có: {len(raw_data)} bản ghi.")
time.sleep(1)

# ==========================================
# GIAI ĐOẠN 2: LÀM SẠCH VÀ KHỬ TRÙNG LẶP CHI TIẾT
# ==========================================
print("\n[2] Kích hoạt Màng lọc Băm (Hash Set Deduplication)...")
time.sleep(1)

seen_signatures = set()
duplicate_tracker = {} 
clean_data = []

# Vòng 1: Quét và gom nhóm số lượng trùng lặp
for row in raw_data:
    signature = (row["Age"], row["ZipCode"], row["Disease"])
    
    if signature not in seen_signatures:
        seen_signatures.add(signature)
        clean_data.append(row)
    else:
        if signature not in duplicate_tracker:
            duplicate_tracker[signature] = 1
        else:
            duplicate_tracker[signature] += 1

# Vòng 2: In báo cáo chi tiết (ĐÃ BỎ GIỚI HẠN)
for sig, dup_count in duplicate_tracker.items():
    print(f"    [CẢNH BÁO] Nhóm hồ sơ bị lặp: Tuổi {sig[0]} | Zip {sig[1]} | Bệnh {sig[2]} -> (Đã giữ 1, xóa {dup_count} bản sao)")

total_duplicates = sum(duplicate_tracker.values())
time.sleep(1)
print(f"    -> HOÀN TẤT: Đã phát hiện {len(duplicate_tracker)} nhóm bị trùng lặp. Đã gạt bỏ {total_duplicates} bản sao rác.")

# ==========================================
# GIAI ĐOẠN 3: XUẤT FILE DATA
# ==========================================
print("\n[3] Xuất tệp dữ liệu sạch (Data Export)...")

random.shuffle(clean_data)

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(clean_data, f, indent=4, ensure_ascii=False)

print(f"    -> Đã xuất thành công {len(clean_data)} bản ghi SẠCH 100% không giới hạn vào 'data.json'.")
print("    -> SẴN SÀNG CHO HỆ THỐNG PHÂN TÁN!\n")