# GenAI Fund FDE Take-Home — X AI & Robotics Outreach Prototype

Một công cụ hoàn chỉnh, chạy được thực tế để GenAI Fund tìm kiếm nhân tài AI và Robotics tại Đông Nam Á trên X, soạn DM cá nhân hóa dựa trên bằng chứng thực, phê duyệt và gửi từ tài khoản đã kết nối — **100% tuân thủ chính sách X, không gửi trùng, và theo dõi hội thoại đầy đủ**.

---

## 📦 Bộ tài liệu & Sản phẩm nộp bài (Deliverables)
1. **Working Prototype (Mã nguồn & Hệ thống chạy được)**:
   - Backend: FastAPI (Python 3.10+) + SQLAlchemy + SQLite / PostgreSQL
   - Frontend: React 18 + Vite + Tailwind CSS (đã build sẵn trong `ui/dist`, phục vụ trực tiếp qua FastAPI)
   - Platform: X API v2 (Official, không scraping) + Anthropic Claude 3.5 Sonnet
2. **One-Page Write-Up**: Đầy đủ trong file [`WRITEUP.md`](./WRITEUP.md) (Approach, Trade-offs, What comes next, Costs, AI Tools & Output Verification).
3. **Demo Video Script (3–5 phút)**: Kịch bản quay video demo trọn vẹn trong file [`DEMO_SCRIPT.md`](./DEMO_SCRIPT.md).

---

## ⚡ Hướng dẫn cài đặt nhanh dưới 15 phút

### 1. Cài đặt phụ thuộc
```bash
# Di chuyển vào thư mục dự án
cd D:\PV

# Cài đặt backend dependencies
pip install -r requirements.txt

# (Tùy chọn nếu build lại giao diện)
cd ui && npm install && npm run build && cd ..
```

### 2. Cấu hình môi trường
Tạo file `.env` từ `.env.example`:
```bash
copy .env.example .env
```
Điền các giá trị của bạn:
- `X_BEARER_TOKEN`: Bearer token từ X Developer Portal (quyền đọc user / tweets).
- `X_USER_ACCESS_TOKEN`: OAuth User Access Token với scope `dm.write`, `dm.read`, `tweet.read`, `users.read`.
- `ANTHROPIC_API_KEY`: API key Claude từ Anthropic (tùy chọn; nếu chưa có, hệ thống tự động kích hoạt bộ soạn nháp theo bằng chứng thực).
- `DATABASE_URL`: Mặc định `sqlite:///./scribbling.db` (hoặc PostgreSQL URL khi deploy).

*(Lưu ý: Bạn cũng có thể nhập API keys trực tiếp trên giao diện web tại trang **⚙ Cấu hình**).*

### 3. Khởi tạo cơ sở dữ liệu
```bash
python -c "from app.db import init_db; init_db()"
python -c "from app.auth import ensure_default_user; ensure_default_user()"
```

### 4. Khởi chạy ứng dụng
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Mở trình duyệt truy cập: **`http://localhost:8000`**

---

## 🎯 Luồng sử dụng thực tế (End-to-End Workflow)

1. **Đăng nhập & Kết nối (`/`)**:
   - Đăng nhập tài khoản quản trị: `admin` / `admin`.
   - Xem trạng thái kết nối các API (X Bearer Token, User Access Token, Anthropic Key).
   - Đặt tên chiến dịch (VD: *AI & Robotics SEA Outreach*) và bấm **Bắt đầu Chiến dịch**.
2. **1. Tìm ứng viên (Discovery & Fit Scoring)**:
   - Nhập tài khoản hạt giống (Seed Accounts) đại diện cho cộng đồng AI/Robotics (ví dụ: `0xCodila`, `karpathy`, `le_robot_ai`).
   - Bấm **"🔍 Quét tìm ứng viên từ Seeds"**: Hệ thống quét mạng lưới followers/following, trích xuất bio & bài viết gần đây, chấm điểm phù hợp (Fit Score 0–100) và nêu rõ lý do tại sao người này phù hợp với GenAI Fund.
   - Bấm **"Soạn DM"** cho từng ứng viên hoặc **"✨ Soạn nháp cho tất cả ứng viên"**.
3. **2. Nháp & Phê duyệt (Personalisation & Review)**:
   - Xem trước văn bản DM cá nhân hóa được tạo dựa trên bằng chứng thực (hiển thị rõ bằng chứng trích xuất bên dưới).
   - **Chỉnh sửa (Edit)**: Bấm **✎ Chỉnh sửa** để điều chỉnh văn bản trực tiếp trên giao diện và bấm **Lưu nội dung**.
   - **Phê duyệt (Approve)** hoặc **Từ chối (Reject)**: Chỉ các tin nhắn được bấm **✓ Phê duyệt** mới đủ điều kiện gửi đi.
4. **3. Đã gửi & Trả lời (Safe Dispatch & Conversation Tracking)**:
   - Bấm **"🚀 Gửi tin nhắn đã duyệt"**: Hệ thống gửi lần lượt, áp dụng khoảng cách an toàn (cooldown delay), giới hạn số lượng ngày/lượt chạy, và **tuyệt đối không gửi trùng** cho bất kỳ ai đã từng được nhắn trước đó.
   - Nếu tài khoản X thuộc gói Free Tier không có quyền gửi DM tự động qua API, hệ thống ghi nhận rõ ràng và cung cấp nút **"Sao chép DM"** để gửi thủ công qua app X mà không mất nội dung đã duyệt.
   - Bấm **"🔄 Kiểm tra tin nhắn phản hồi"**: Hệ thống kéo các sự kiện tin nhắn đến từ X, khớp với ứng viên và đưa vào mục **"Hộp thư phản hồi & Cần chú ý"** kèm nhãn **◐ CẦN TRẢ LỜI**.

---

## 🔒 Tuân thủ quy định & Bảo mật (Ground Rules)
- **Không gửi thư rác (Anti-Spam)**: Kiểm tra chéo ID và Username trên toàn bộ cơ sở dữ liệu trước khi gửi; chặn 100% việc double-messaging.
- **Không Scraping cấm**: 100% sử dụng X API v2 chính thức.
- **Bảo mật tuyệt đối**: Không bao giờ commit file `.env` hay credentials vào Git; `.env` đã được thêm vào `.gitignore`.

---

## 💰 Ước tính chi phí vận hành
- **Claude 3.5 Sonnet**: ~\$0.003 / nháp DM. Tạo 1,000 bản nháp chỉ tốn dưới \$3.00.
- **X API v2**: Miễn phí với chế độ tìm kiếm & soạn nháp; gói Basic \$100/tháng nếu muốn tự động hóa gửi DM API.
- **Hosting & Database**: \$0 – \$7/tháng trên Render / Supabase / Vercel.
