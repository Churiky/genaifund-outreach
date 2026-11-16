# GenAI Fund — 3–5 Minute End-to-End Demo Video Script

**Target Duration:** 3:30 – 4:30 minutes  
**Tone:** Engineering-focused, honest about platform constraints, showcasing production readiness.  
*(Kịch bản song ngữ Anh – Việt: Bạn có thể chọn đọc thuyết minh bằng tiếng Anh hoặc tiếng Việt).*

---

### Scene 1: Introduction & Context (0:00 – 0:40)
- **Visual:** Open browser at `http://localhost:8000` (hoặc đường link trên Render). Show the clean GenAI Fund prototype dashboard.
- **Narrator (English):**  
  *"Hi GenAI Fund team! This is the working prototype for the FDE take-home assignment. Our objective is to find high-signal AI and robotics builders, researchers, and founders across Southeast Asia, draft warm and evidence-backed DMs, review them before dispatch, and track ongoing conversations without ever double-messaging anyone or violating platform limits."*
- **Thuyết minh (Tiếng Việt):**  
  *"Xin chào team GenAI Fund! Đây là bản working prototype cho bài tập FDE. Mục tiêu của hệ thống là tìm kiếm các kỹ sư, nhà nghiên cứu và founder mảng AI & Robotics tại Đông Nam Á, soạn tin nhắn DM cá nhân hóa dựa trên bằng chứng thực tế, kiểm duyệt trước khi gửi, và theo dõi hội thoại mà không bao giờ gửi trùng tin nhắn hay vi phạm giới hạn của nền tảng X."*

---

### Scene 2: Platform Realities & Setup (0:40 – 1:30)
- **Visual:** Click on the **⚙ Cấu hình** (Settings / Runtime Credentials) modal. Show the connection status indicators. Point out the **"⚡ Vào Demo Ngay"** button.
- **Narrator (English):**  
  *"Let's address platform access right away. The official X API v2 Free tier currently restricts reading follower graphs of external accounts and automated DM sending—which now requires X Basic ($100/mo) or Pro ($5,000/mo).*  
  *To ensure you can run and evaluate this tool independently without being forced to purchase paid X developer tiers upfront, we designed a dual-mode architecture:*  
  *1. **Demo Mode**: 1-click end-to-end evaluation with realistic Southeast Asian AI and robotics personas.*  
  *2. **Live Production Mode**: Connect your X Pro/Basic tokens and Anthropic Claude keys right here. The backend is 100% compliant with official X API v2 schema, so when live keys are provided, it operates identically to what you see in the demo."*
- **Thuyết minh (Tiếng Việt):**  
  *"Tôi xin nói rõ về giới hạn của nền tảng X: Hiện tại gói X API v2 Free Tier bị X khóa tính năng quét follower và cấm gửi DM tự động qua API (yêu cầu gói Basic $100/tháng hoặc Pro $5,000/tháng).*  
  *Để team GenAI Fund có thể tự mình test trọn vẹn toàn bộ công cụ mà không cần tốn chi phí mua API X trả phí, tôi đã xây dựng kiến trúc 2 chế độ:*  
  *1. **Chế độ Demo**: Nút '⚡ Vào Demo Ngay' giúp trải nghiệm toàn bộ luồng với các hồ sơ AI & Robotics Đông Nam Á thực tế.*  
  *2. **Chế độ Live Production**: Điền trực tiếp Token X Basic/Pro và API Key Claude tại đây. Toàn bộ backend đã chuẩn hóa 100% theo schema X API v2 chính thức, nên khi có key thật, hệ thống chạy y hệt những gì hiển thị trong demo."*

---

### Scene 3: Seed-Based Discovery & Fit Scoring (1:30 – 2:20)
- **Visual:** Navigate to **1. Tìm ứng viên**. Show the seed accounts list (`@0xCodila`, `@karpathy`, `@le_robot_ai`). Show the candidate table with avatars, location tags, and fit score badges.
- **Narrator (English):**  
  *"We provide seed accounts representing high-signal nodes in the AI/robotics ecosystem. In live mode, our discovery engine queries the X graph and fetches candidate profiles, locations, and recent tweets.*  
  *Notice our deterministic scoring engine: each candidate receives an objective fit score out of 100 and an explicit reason why they fit. It checks domain keywords like embodied AI, vision-language-action models, devtools, or ROS2, matched with Southeast Asian geographic signals like Hanoi, Singapore, Bandung, or Malaysia. Everything is explainable; there is no black-box guesswork."*
- **Thuyết minh (Tiếng Việt):**  
  *"Chúng ta cung cấp các tài khoản hạt giống (Seed Accounts). Ở chế độ Live, hệ thống truy vấn đồ thị X để lấy thông tin hồ sơ, địa điểm và các bài tweet gần đây.*  
  *Mỗi ứng viên đều có Điểm phù hợp (Fit Score / 100) và Lý do giải thích cụ thể: kết hợp giữa các từ khóa chuyên môn (embodied AI, VLA models, devtools, ROS2) với tín hiệu địa lý Đông Nam Á (Hà Nội, Singapore, Bandung, Malaysia). Mọi thứ đều minh bạch và giải thích được, không hề đoán mò."*

---

### Scene 4: Evidence-Based Personalisation & Review (2:20 – 3:15)
- **Visual:** Click **"Soạn DM"** or **"✨ Soạn nháp cho tất cả"**, then navigate to **2. Nháp & Phê duyệt**. Show the evidence box below each draft. Click **✎ Chỉnh sửa** on a draft, edit a word, click **Lưu nội dung**, then click **✓ Phê duyệt**.
- **Narrator (English):**  
  *"Now let's look at personalization. Our integration with Claude 3.5 Sonnet drafts concise, warm DMs under 240 characters using strictly real evidence from the candidate's bio and posts. Look right here below the text: we display the exact public evidence used.*  
  *Crucially, no message ever leaves the account automatically. GenAI Fund operators retain complete control:*  
  *1. We can click **Chỉnh sửa** to tweak the copy inline.*  
  *2. Click **Phê duyệt** to approve ready-to-send drafts.*  
  *3. Or click **Từ chối** to discard ill-fitting messages. If Claude keys are omitted, a deterministic evidence-based fallback guarantees the pipeline never stalls."*
- **Thuyết minh (Tiếng Việt):**  
  *"Về phần cá nhân hóa: Hệ thống kết nối Claude 3.5 Sonnet để soạn các tin nhắn ngắn gọn dưới 240 ký tự, dựa trên bằng chứng thực tế từ bio và bài viết của ứng viên. Ngay dưới mỗi nháp đều hiển thị rõ trích dẫn bằng chứng công khai được sử dụng.*  
  *Đặc biệt, không có tin nhắn nào tự động bắn đi. Người điều hành GenAI Fund có toàn quyền kiểm duyệt:*  
  *1. Bấm **Chỉnh sửa** để sửa câu từ trực tiếp.*  
  *2. Bấm **Phê duyệt** cho các bản nháp đạt chuẩn.*  
  *3. Bấm **Từ chối** nếu không phù hợp. Nếu không có key Claude, hệ thống có sẵn bộ fallback rule-based để không bao giờ bị nghẽn."*

---

### Scene 5: Safe Sending & Strict Deduplication (3:15 – 4:00)
- **Visual:** In the Drafts tab or navigating to **3. Đã gửi & Trả lời**. Show both send buttons: **⚡ Gửi mô phỏng (Demo)** and **🚀 Gửi qua X API**. Click **⚡ Gửi mô phỏng**. Show drafts turning into blue **ĐÃ GỬI** badge.
- **Narrator (English):**  
  *"Now we dispatch approved drafts. We provide two distinct actions:*  
  *- **⚡ Gửi mô phỏng (Demo)**: Safely simulates the delivery flow for testing without requiring paid X API tokens.*  
  *- **🚀 Gửi qua X API**: Calls the official `/2/dm_conversations/with/:id/messages` endpoint when connected to an authorized X account with DM write scope.*  
  *Crucially, our sender enforces strict anti-spam rules:*  
  *1. **Global Deduplication**: Checks past dispatches across all campaigns by recipient ID and username. It is mathematically impossible to double-message anyone.*  
  *2. **Safety Caps & Cooldown**: Respects daily limits and inserts respectful pauses between sends to protect our account from being flagged."*
- **Thuyết minh (Tiếng Việt):**  
  *"Khi gửi tin nhắn, giao diện cung cấp 2 nút rõ ràng:*  
  *- **⚡ Gửi mô phỏng (Demo)**: Giúp chạy thử nghiệm toàn bộ luồng mà không cần gói X trả phí.*  
  *- **🚀 Gửi qua X API**: Gọi trực tiếp endpoint chính thức của X khi kết nối tài khoản có quyền gửi DM.*  
  *Hệ thống kiểm soát cực kỳ chặt chẽ:*  
  *1. **Chống gửi trùng tuyệt đối**: Kiểm tra chéo toàn bộ database theo cả ID và Username; không bao giờ có chuyện gửi 2 lần cho cùng một người.*  
  *2. **Giới hạn an toàn & Cooldown**: Giới hạn số lượng gửi mỗi ngày và giãn cách thời gian giữa các tin nhắn để bảo vệ uy tín tài khoản X."*

---

### Scene 6: Reply Tracking, Needs Attention & Wrap-Up (4:00 – 4:30)
- **Visual:** Show the **Hộp thư phản hồi & Cần chú ý** section. Click **"⚡ Mô phỏng phản hồi (Demo)"** (hoặc **"🔄 Kiểm tra tin nhắn X"**). Show the yellow **◐ CẦN TRẢ LỜI** badges. Show stats grid.
- **Narrator (English):**  
  *"Finally, the conversation tracker. The inbound poller monitors for incoming DMs, matches sender IDs to our prospects, and flags active threads with a prominent 'Cần trả lời' badge in our dedicated inbox.*  
  *Everything is traceable in the stats dashboard: total prospects, approved drafts, sent, failed, responded, and conversations needing attention.*  
  *In summary: this is a production-ready, rule-compliant prototype that GenAI Fund can run independently today. Thank you!"*
- **Thuyết minh (Tiếng Việt):**  
  *"Cuối cùng là phần theo dõi hội thoại: Bộ tracker liên tục kiểm tra tin nhắn đến, khớp ID người gửi với danh sách ứng viên, và đẩy ngay vào Hộp thư 'Cần chú ý' với nhãn nổi bật 'Cần trả lời'.*  
  *Bảng điều khiển hiển thị đầy đủ 6 chỉ số: Tổng ứng viên, Đã duyệt, Đã gửi, Thất bại, Đã trả lời và Số cuộc hội thoại cần phản hồi.*  
  *Tóm lại, đây là một công cụ hoàn chỉnh, đúng luật nền tảng và sẵn sàng để GenAI Fund tự vận hành ngay hôm nay. Cảm ơn team GenAI Fund!"*
