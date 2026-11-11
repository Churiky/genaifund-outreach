# GenAI Fund — 3–5 Minute End-to-End Demo Video Script

**Target Duration:** 3:30 – 4:30 minutes  
**Tone:** Practical, engineering-focused, candid about platform limitations.

---

### Scene 1: Introduction & Context (0:00 – 0:35)
- **Visual:** Open browser at `http://localhost:8000`. Show the clean GenAI Fund prototype interface.
- **Narrator Voiceover:**  
  *"Hi everyone, this is the working prototype built for GenAI Fund's FDE take-home assignment. Our objective is to find high-signal AI and robotics builders across Southeast Asia, draft warm and evidence-backed DMs, review them before sending, and manage conversations without ever double-messaging anyone or violating platform limits."*

---

### Scene 2: Setup & Credentials (0:35 – 1:15)
- **Visual:** Click on the **⚙ Cấu hình** (Settings) screen.
- **Narrator Voiceover:**  
  *"The tool can be set up in under 15 minutes. It uses official X API v2 and Anthropic Claude for drafting. We don't store secrets in repository code; users can supply their own keys via the `.env` file or directly in this connection screen for runtime use.*  
  *Notice our real-time status indicators confirming which keys are connected. If Claude keys aren't provided immediately, the system gracefully falls back to an evidence-based template so evaluation is never blocked."*

---

### Scene 3: Seed-Based Discovery & Fit Scoring (1:15 – 2:10)
- **Visual:** Navigate to **1. Tìm ứng viên**. Show the seed accounts list (`@0xCodila`, `@karpathy`, `@le_robot_ai`). Click **"Quét tìm ứng viên từ Seeds"**.
- **Narrator Voiceover:**  
  *"We give the system seed accounts that represent AI and robotics nodes. The engine queries the X graph, retrieves profiles and recent posts, and computes an objective fit score.*  
  *Look at the candidate table: each person has a transparent fit score and a concrete reason explaining why they fit—combining domain keywords like embodied AI, devtools, or LLMs with Southeast Asian geographic signals. Nothing is black-box guesswork."*

---

### Scene 4: Evidence-Based Personalisation & Review (2:10 – 3:00)
- **Visual:** Click **"Soạn DM"** or **"✨ Soạn nháp cho tất cả ứng viên"**, then navigate to **2. Nháp & Phê duyệt**.
- **Narrator Voiceover:**  
  *"Now we generate personalized DMs. Claude drafts each message using strictly real evidence from their bio and posts. Notice that we display the exact public evidence used right below each draft.*  
  *Crucially, no message ever sends automatically. Here in the review interface, we can:*  
  *1. Click **Chỉnh sửa** to tweak the text inline and save it.*  
  *2. Click **Phê duyệt** to approve high-fit prospects.*  
  *3. Or click **Từ chối** to discard candidates."*

---

### Scene 5: Safe Sending & Duplicate Prevention (3:00 – 3:45)
- **Visual:** Click **"🚀 Gửi tin nhắn đã duyệt"** or navigate to **3. Đã gửi & Trả lời**. Show the sending log table.
- **Narrator Voiceover:**  
  *"When we trigger sending, the sender module enforces strict guardrails:*  
  *- It checks our database to ensure we **never double-message** someone, even across multiple campaigns.*  
  *- It respects daily caps and applies polite cooldown periods between sends to stay within X's limits.*  
  *- If connected to an X Free tier without automated DM permissions, the tool logs the exact limitation and provides a 1-click 'Sao chép DM' button so our team can send manually without losing any work."*

---

### Scene 6: Reply Tracking & Wrap-Up (3:45 – 4:30)
- **Visual:** Show the **Hộp thư phản hồi (Cần chú ý)** section. Click **"🔄 Kiểm tra tin nhắn phản hồi"**.
- **Narrator Voiceover:**  
  *"Once outreach is underway, our inbound tracker polls for incoming DMs, correlates replies with our prospect list, and flags active threads with a 'Cần trả lời' badge.*  
  *Everything is traceable: what was sent, who responded, and what needs immediate attention.*  
  *To recap: this is a production-grade, API-compliant prototype ready for GenAI Fund to deploy and start warm conversations today. Thank you!"*

