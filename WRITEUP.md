# GENAI FUND — FOUNDER DISCOVERY ENGINEER (FDE)
## Technical Architecture, Strategy & Operating Write-Up

**Candidate Project:** AI & Robotics Builder Outreach Engine (Southeast Asia)  
**Live Hosted Prototype:** [DÁN_LINK_RENDER_CỦA_BẠN_VÀO_ĐÂY (ví dụ: https://genaifund-outreach.onrender.com)]  
**GitHub Repository:** https://github.com/Churiky/genaifund-outreach  
**Demo Video (3–4 mins):** [DÁN_LINK_VIDEO_GOOGLE_DRIVE_HOẶC_YOUTUBE_VÀO_ĐÂY]  
**Submission Date:** November 2026  

---

### 1. Executive Summary

GenAI Fund is building AI ecosystems across Southeast Asia, targeting high-caliber builders, founders, and researchers in foundation models, developer tools, infrastructure, and embodied AI/robotics. Mass-scale generic outreach destroys credibility; manual 1-on-1 searching does not scale.

This project delivers a **working, production-ready outreach engine** that bridges this gap:
1. **Targeted Discovery & Transparent Scoring:** Identifies relevant individuals from ecosystem seed accounts and computes an explainable Fit Score (0–100) based on domain keywords and regional signals.
2. **Evidence-First Personalization:** Generates hyper-personalized DMs (< 240 characters) via Claude 3.5 Sonnet strictly derived from verified public evidence (bios and recent posts), never hallucinating familiarity.
3. **Strict Human-in-the-Loop Review:** No message ever leaves the account automatically; operators can review cited evidence, edit copy inline, approve, or reject.
4. **Safety & Zero-Duplicate Guarantee:** Enforces cross-campaign deduplication by handle and user ID, daily volume limits, and respectful cooldown delays.
5. **Closed-Loop Tracking:** Automatically ingests inbound direct messages, correlates replies with prospects, and highlights active conversations in a dedicated "Needs Attention" inbox.

The application is deployed live on **Render** (FastAPI backend serving pre-built React frontend) for immediate cloud evaluation with zero local setup required.

---

### 2. Platform Realities & Dual-Mode Strategy

X has recently transitioned to an all-new **Consumption-Based Pay-Per-Use Developer Model**, moving away from rigid Basic ($100–$200/mo) and Pro ($5,000/mo) subscriptions. Under this model, developers pay strictly per resource consumed:
* **DM Creation (`DM Interaction: Create`):** $0.015 per message sent
* **User Profile Lookup (`User: Read`):** $0.010 per profile fetched
* **DM Event Tracking (`DM Event: Read`):** $0.010 per event
* **Post / Tweet Lookup (`Posts: Read`):** $0.005 per resource

While this dramatically lowers the operational cost of outreach, **an account on an uncredited Free tier cannot dispatch automated DMs or query full follower graphs without active developer tier access (Pay-Per-Use credits or Basic/Pro tier)**.

To demonstrate engineering judgment and enable frictionless evaluation, the system features a **Dual-Mode Architecture**:

* **Mode 1: Interactive Cloud Demo (Instant Zero-Friction Evaluation):**  
  Accessible via the 1-click *"⚡ Vào Demo Ngay"* button on the live Render app. It seeds realistic Southeast Asian personas (robotics researchers in Hanoi, devtools founders in Singapore, speech AI engineers in Bandung). Evaluators can experience the full end-to-end pipeline—discovery scoring, Claude drafting, human review, simulated delivery, and reply inbox management—without needing upfront X developer credit top-ups or paid tier access.

* **Mode 2: Live X API Production (Ready to Deploy):**  
  Operators simply supply their authorized X API tokens (Pay-Per-Use or Basic/Pro tier with `dm.write`, `dm.read`, `tweet.read`, `users.read` scopes) and Anthropic Claude keys via the runtime modal or `.env` file. The backend is 100% compliant with official X API v2 endpoints (`/2/dm_conversations/with/:id/messages`, `/2/users/by/username`). Once connected, the live workflow runs with identical behavior.

---

### 3. Key Architectural Decisions & Trade-offs

1. **Official X API v2 vs. Unofficial Web Scraping / Puppeteer Bots**  
   * *Decision:* 100% official X API v2 compliance.  
   * *Rationale:* Unofficial headless browser scraping violates X’s Terms of Service and carries an immediate risk of permanent account suspension. For an institutional investment fund, brand safety, legal compliance, and account integrity are non-negotiable.

2. **Mandatory Human-in-the-Loop Review vs. Autonomous Dispatch**  
   * *Decision:* Require explicit operator approval before any message is sent.  
   * *Rationale:* Fully autonomous outreach agents frequently produce tone-deaf or subtly incorrect messages at scale. Human review ensures every interaction feels authentic, respectful, and reflective of GenAI Fund's high-signal ethos.

3. **Global Cross-Campaign Deduplication (Anti-Spam Engine)**  
   * *Decision:* Enforce database-level uniqueness across campaigns using both recipient X User ID and lowercase username.  
   * *Rationale:* In institutional outreach, double-messaging a founder across different team campaigns looks unprofessional. The system automatically skips previously messaged candidates and flags them as protected dispatches.

4. **Graceful Fail-Safe Architecture vs. Hard Dependencies**  
   * *Decision:* Provide rule-based evidence templates if LLM keys are absent, and 1-click clipboard copy if connected to an X Free tier.  
   * *Rationale:* Production tools must degrade gracefully under API quota exhaustion or network hiccups rather than crashing.

---

### 4. Operating Economics & Cost Breakdown

With X's new pay-per-use credit consumption model, outreach unit economics become exceptionally lean. There are **zero fixed monthly minimums**—the fund only pays for successful interactions:

| Infrastructure Component | Pricing Model & Unit Rates | Estimated Cost (500 Prospects) | Operational Rationale |
| :--- | :--- | :--- | :--- |
| **X Developer API** | Pay-Per-Use: $0.015/DM, $0.010/user lookup, $0.005/tweet read | ~$22.50 total | Zero monthly commitment; costs scale strictly with sourcing volume. |
| **LLM Personalization** | Anthropic Claude 3.5 Sonnet: ~$0.003 / generated DM | ~$1.50 total | Hyper-personalized, evidence-backed opening copy under 240 chars. |
| **Cloud Hosting & DB** | Render.com: Web Service + PostgreSQL | $0 (Free Tier) – $7 / month | Single-container architecture serving FastAPI + compiled React static assets. |
| **Total Campaign Cost** | | **~$24.00 – $31.00** | Under **$0.06 per engaged founder**; massive ROI for venture deal-sourcing. |

*Detailed X API cost breakdown for a 500-founder campaign:*
* 500 Direct Messages dispatched ($0.015/DM) = $7.50
* 500 Candidate Profile lookups ($0.010/read) = $5.00
* 1,000 Recent technical posts analyzed ($0.005/read) = $5.00
* 500 Inbound reply status checks ($0.010/read) = $5.00
* **Total X Platform Investment:** $22.50 (vs. $200–$5,000 under the old subscription tiers).

---

### 5. How AI Tools Were Leveraged & Verified

1. **Prompt Guardrails:** Claude 3.5 Sonnet is constrained by strict negative boundaries:
   * Must remain under 240 characters.
   * Strictly forbidden from hallucinating mutual connections, fake compliments, or non-existent projects.
   * Must ground the hook strictly in verified bio statements or recent technical tweets.
2. **Visual Evidence Coupling:** On the review screen, the exact snippet of public evidence used to generate each draft is displayed directly beneath the message text. Reviewers can verify truthfulness in under 3 seconds before clicking "Phê duyệt".
3. **Deterministic Fallback:** A regex-based keyword extractor identifies core sub-disciplines (Embodied AI, LLMs, Devtools, Infra) to generate structured outreach copy if Claude API quotas are exhausted.

---

### 6. Roadmap: What Comes Next

If expanded into an enterprise-grade platform for GenAI Fund's deal-sourcing team, the following enhancements are prioritized:
* **OAuth 2.0 PKCE 1-Click Authentication:** Allowing fund team members to connect their individual X accounts with a single click.
* **Bi-Directional CRM & Slack Sync:** Pushing newly discovered warm leads directly into Notion / HubSpot, and sending real-time Slack alerts when a founder replies to outreach.
* **Semantic Reply Classification:** Using lightweight embeddings to categorize incoming founder responses into *"Warm / Raising Round"*, *"Referral"*, *"Not Now"*, or *"Unsubscribe"*.
* **Smart Follow-Up Cadence:** Scheduling a single polite follow-up nudge (e.g., after 5 business days), automatically cancelled the moment an inbound reply is detected.
