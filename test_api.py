import json
import sys
import httpx

BASE = "http://localhost:8000"
results = []


def step(name: str, ok: bool, detail: str = ""):
    status = "PASS" if ok else "FAIL"
    results.append((name, ok, detail))
    print(f"[{status}] {name} {detail}")


# 1. Login
token = None
try:
    r = httpx.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin"}, timeout=10.0)
    if r.status_code == 200:
        token = r.json()["access_token"]
        step("Login", True, f"token={token[:20]}...")
    else:
        step("Login", False, f"status={r.status_code} body={r.text}")
except Exception as e:
    step("Login", False, str(e))

headers = {"Authorization": f"Bearer {token}"} if token else {}

# 2. Check credentials status
try:
    r = httpx.get(f"{BASE}/config/credentials/status", headers=headers, timeout=10.0)
    if r.status_code == 200:
        step("Credentials status", True, str(r.json()))
    else:
        step("Credentials status", False, f"status={r.status_code} body={r.text}")
except Exception as e:
    step("Credentials status", False, str(e))

# 3. Create campaign
campaign_id = None
try:
    r = httpx.post(
        f"{BASE}/campaigns",
        json={
            "name": "AI & Robotics SEA Test Campaign",
            "segment_description": "AI/robotics founders and builders test",
            "max_sends_per_run": 5,
            "max_sends_per_day": 10,
            "cooldown_seconds": 5,
        },
        headers=headers,
        timeout=10.0,
    )
    if r.status_code in (200, 201):
        campaign_id = r.json()["id"]
        step("Create campaign", True, f"id={campaign_id}")
    else:
        step("Create campaign", False, f"status={r.status_code} body={r.text}")
except Exception as e:
    step("Create campaign", False, str(e))

# 4. Add seed
if campaign_id:
    try:
        r = httpx.post(
            f"{BASE}/campaigns/{campaign_id}/seeds",
            json={"username": "0xCodila"},
            headers=headers,
            timeout=10.0,
        )
        if r.status_code in (200, 201):
            step("Add seed", True, f"seed={r.json()['username']}")
        else:
            step("Add seed", False, f"status={r.status_code} body={r.text}")
    except Exception as e:
        step("Add seed", False, str(e))

# 5. Find prospects
if campaign_id:
    try:
        r = httpx.post(
            f"{BASE}/campaigns/{campaign_id}/find", headers=headers, timeout=60.0
        )
        if r.status_code == 200:
            data = r.json()
            step("Find prospects", True, f"created={data.get('created')}")
        else:
            step("Find prospects", False, f"status={r.status_code} body={r.text}")
    except Exception as e:
        step("Find prospects", False, str(e))

# 6. List prospects
prospect_id = None
draft_id = None
if campaign_id:
    try:
        r = httpx.get(
            f"{BASE}/campaigns/{campaign_id}/prospects", headers=headers, timeout=10.0
        )
        if r.status_code == 200:
            prospects = r.json()
            step("List prospects", True, f"count={len(prospects)}")
            if prospects:
                prospect_id = prospects[0]["id"]
                draft_id = prospects[0].get("draft_id")
        else:
            step("List prospects", False, f"status={r.status_code} body={r.text}")
    except Exception as e:
        step("List prospects", False, str(e))

# 7. Create draft for prospect
if prospect_id:
    try:
        r = httpx.post(
            f"{BASE}/prospects/{prospect_id}/draft",
            headers=headers,
            timeout=30.0,
        )
        if r.status_code in (200, 201):
            draft_data = r.json()
            draft_id = draft_data.get("id")
            step("Create draft", True, f"draft_id={draft_id}")
        else:
            step("Create draft", False, f"status={r.status_code} body={r.text}")
    except Exception as e:
        step("Create draft", False, str(e))

# 8. Edit / Update draft text
if draft_id:
    try:
        r = httpx.patch(
            f"{BASE}/drafts/{draft_id}",
            json={"dm_text": "Hi, love your robotics research at SEA. Let's connect!"},
            headers=headers,
            timeout=10.0,
        )
        if r.status_code == 200:
            step("Edit draft text", True, f"draft_id={draft_id}")
        else:
            step("Edit draft text", False, f"status={r.status_code} body={r.text}")
    except Exception as e:
        step("Edit draft text", False, str(e))

# 9. Approve draft
if draft_id:
    try:
        r = httpx.patch(
            f"{BASE}/drafts/{draft_id}/approve?approved_by=admin",
            headers=headers,
            timeout=10.0,
        )
        if r.status_code == 200:
            step("Approve draft", True, f"draft_id={draft_id}")
        else:
            step("Approve draft", False, f"status={r.status_code} body={r.text}")
    except Exception as e:
        step("Approve draft", False, str(e))

# 10. Send campaign
if campaign_id:
    try:
        r = httpx.post(
            f"{BASE}/campaigns/{campaign_id}/send",
            headers=headers,
            timeout=60.0,
        )
        if r.status_code == 200:
            step("Send campaign", True, str(r.json()))
        else:
            step("Send campaign", False, f"status={r.status_code} body={r.text}")
    except Exception as e:
        step("Send campaign", False, str(e))

# 11. Sync replies
if campaign_id:
    try:
        r = httpx.post(
            f"{BASE}/campaigns/{campaign_id}/sync-replies",
            headers=headers,
            timeout=15.0,
        )
        if r.status_code == 200:
            step("Sync replies", True, str(r.json()))
        else:
            step("Sync replies", False, f"status={r.status_code} body={r.text}")
    except Exception as e:
        step("Sync replies", False, str(e))

# 12. Stats
if campaign_id:
    try:
        r = httpx.get(
            f"{BASE}/campaigns/{campaign_id}/stats", headers=headers, timeout=10.0
        )
        if r.status_code == 200:
            step("Stats", True, str(r.json()))
        else:
            step("Stats", False, f"status={r.status_code} body={r.text}")
    except Exception as e:
        step("Stats", False, str(e))

# Summary
print("\n=== TEST SUMMARY ===")
all_pass = True
for name, ok, detail in results:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name} {detail}")
    if not ok:
        all_pass = False

print()
print("Overall:", "ALL PASS" if all_pass else "SOME FAILED")
sys.exit(0 if all_pass else 1)
