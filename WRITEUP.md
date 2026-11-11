# GenAI Fund — FDE Take-Home Assignment: Architecture & Strategy Write-Up

## 1. Approach & System Architecture
We built a lightweight, reliable, single-tenant outreach system designed to start genuine conversations with AI and robotics builders, founders, and researchers in Southeast Asia. 

```
[ Seed Accounts ] ──► [ X API v2 Graph Expansion ] ──► [ Evidence Extractor ]
                                                              │
[ Never-Duplicate DB ] ◄── [ Human Review & Edit ] ◄── [ Claude Drafter ]
          │
[ Rate-Limited Sender ] ──► [ X Inbound Poller & Reply Tracker ] ──► [ Needs Attention Inbox ]
```

### Key Components:
- **Targeting Engine (`scorer.py`)**: Uses deterministic scoring based on real evidence (bios and recent posts). Matches AI/robotics domains (models, embodied AI, robotics, infra, devtools), founder/researcher roles, and Southeast Asian geographic signals (Singapore, Vietnam, Indonesia, Malaysia, Thailand, Philippines).
- **Evidence-First Personalisation (`drafter.py`)**: Prompts Claude 3.5 Sonnet to draft concise, low-pressure DMs (<240 chars) derived strictly from public evidence. Includes a deterministic rule-based fallback if LLM credentials are temporarily unavailable.
- **Strict Human-in-the-Loop Review (`Drafts.tsx`)**: No message ever leaves the account automatically. The user can view the exact evidence cited, edit the copy, approve, or reject.
- **Safety & Platform Compliance (`sender.py`)**: Enforces three layers of protection:
  1. *Global cross-campaign deduplication*: Checks past successful sends to prevent double-messaging.
  2. *Daily send caps* (e.g. 100/day) and *per-run limits* (e.g. 25/run).
  3. *Polite cooldown delays* (90s default) between API dispatches to stay well within platform limits.
- **Closed-Loop Conversation Tracking (`tracker.py`)**: Ingests inbound Direct Message events from X API v2, correlates them with known prospects, and surfaces incoming messages in a dedicated "Needs Attention" inbox.

---

## 2. Key Trade-offs & Decisions
1. **Official X API v2 vs. Unofficial Scraping/Headless Browsers**:
   - *Choice*: 100% official X API v2 endpoints.
   - *Rationale*: Scraping violates X Terms of Service and risks immediate account suspension. For GenAI Fund's official brand reputation, an API-compliant tool is non-negotiable.
2. **Explicit Human Approval vs. Full Automation**:
   - *Choice*: Require manual review before dispatching any DM.
   - *Rationale*: Generic outreach at scale burns credibility. Personal review guarantees that every message reflects the fund's warm, high-signal ethos.
3. **Graceful Free/Basic Tier Fallback vs. Hard Dependency**:
   - *Choice*: Provide one-click "Copy DM" fallback and clear diagnostics if the connected X token lacks automated DM write permissions (e.g., Free tier).
   - *Rationale*: Enables immediate end-to-end evaluation without requiring paid X Developer tiers up front.

---

## 3. What Comes Next (Roadmap)
- **Multi-Tenant OAuth 2.0 PKCE**: Direct 1-click "Connect with X" button replacing manual token entry.
- **CRM & Slack Bi-Directional Sync**: Instant Slack alerts when a prospect replies, with two-way sync into HubSpot or Notion.
- **Smart Reply Classification**: Using lightweight embeddings to classify replies into "Warm Lead", "Referral", "Not Now", or "Unsubscribe".
- **Dynamic Follow-Up Scheduling**: Gentle, single follow-up nudge (e.g. after 5 business days) with automatic cancellation upon reply.

---

## 4. Cost Breakdown & Operating Economics
| Component | Tier / Provider | Estimated Monthly Cost | Notes |
| :--- | :--- | :--- | :--- |
| **X API v2** | Basic / Pro Tier | \$0 (Free/manual mode) – \$100/mo (Basic) | Free tier supports candidate search & manual outreach; Basic permits automated DM sending. |
| **LLM Personalisation** | Anthropic Claude 3.5 Sonnet | \$1 – \$5 / month | ~\$0.003 per generated draft. 1,000 drafts cost under \$3.00. |
| **Backend & DB** | Render / Railway (Free / Starter) | \$0 – \$7 / month | Free tier is sufficient for hundreds of prospects with SQLite/Postgres. |
| **Frontend Static** | Vercel / Cloudflare Pages / Render | \$0 / month | Free unlimited static hosting. |
| **Total Operating Cost** | | **~\$1 – \$112 / month** | Extremely lean; scalable on demand. |

---

## 5. How AI Tools Were Used & Verified
- **Assisted Drafting**: Claude 3.5 Sonnet generates hyper-personalized opening DMs using extracted profile signals.
- **System Prompt Safeguards**: The prompt explicitly forbids inventing mutual connections, praising nonexistent projects, or hallucinating familiarity.
- **Output Verification Protocol**:
  1. *Prompt Guardrails*: Required output format is pure message text under 240 characters.
  2. *Evidence Attachment*: Every draft in the database is tagged with the exact `evidence_summary` used to create it.
  3. *Human Review Gate*: Operators verify the evidence snippet against the copy in the UI before approving.

