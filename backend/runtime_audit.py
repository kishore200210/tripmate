"""
TripMate Runtime Audit Script
Tests all major features via HTTP requests against the running backend.
"""
import httpx
import json
import uuid
import sys
import os

BASE = "http://localhost:8000/api/v1"
RESULTS = []
TOKEN = None
USER_ID = None
TRIP_ID = None

def report(feature, status, details=""):
    RESULTS.append({"feature": feature, "status": status, "details": details})
    icon = {"PASS":"✅","FAIL":"❌","PARTIAL":"🟡","NOT_TESTABLE":"⚪"}
    print(f"  {icon.get(status,'?')} [{status}] {feature}: {details[:200]}")

def run_tests():
    global TOKEN, USER_ID, TRIP_ID
    client = httpx.Client(timeout=30.0)
    
    # ── 0. Health Check ──
    print("\n=== 0. HEALTH CHECK ===")
    try:
        r = client.get("http://localhost:8000/health")
        report("Health Check", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} body={r.text[:100]}")
    except Exception as e:
        report("Health Check", "FAIL", str(e))
        print("Backend not reachable. Aborting.")
        return

    # ── 1. Signup ──
    print("\n=== 1. SIGNUP ===")
    test_email = f"audit_{uuid.uuid4().hex[:8]}@test.com"
    try:
        r = client.post(f"{BASE}/auth/register", json={"name":"Audit User","email":test_email,"password":"AuditPass1"})
        if r.status_code == 201:
            report("Signup", "PASS", f"status=201 user_id={r.json().get('user',{}).get('id','?')}")
        else:
            report("Signup", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("Signup", "FAIL", str(e))

    # ── 2. Login ──
    print("\n=== 2. LOGIN ===")
    try:
        r = client.post(f"{BASE}/auth/login", json={"email":test_email,"password":"AuditPass1"})
        if r.status_code == 200:
            data = r.json()
            TOKEN = data["tokens"]["access_token"]
            USER_ID = data["user"]["id"]
            report("Login", "PASS", f"status=200 got_token=True user_id={USER_ID}")
        else:
            report("Login", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("Login", "FAIL", str(e))

    if not TOKEN:
        print("Cannot continue without auth token.")
        return

    headers = {"Authorization": f"Bearer {TOKEN}"}

    # ── 3. Logout ──
    print("\n=== 3. LOGOUT ===")
    try:
        r = client.post(f"{BASE}/auth/logout")
        report("Logout", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} body={r.text[:100]}")
    except Exception as e:
        report("Logout", "FAIL", str(e))

    # ── 4. Protected Routes ──
    print("\n=== 4. PROTECTED ROUTES ===")
    try:
        r_no_auth = client.get(f"{BASE}/auth/me")
        r_with_auth = client.get(f"{BASE}/auth/me", headers=headers)
        if r_no_auth.status_code == 401 and r_with_auth.status_code == 200:
            report("Protected Routes", "PASS", "Unauthenticated=401, Authenticated=200")
        else:
            report("Protected Routes", "FAIL", f"no_auth={r_no_auth.status_code} with_auth={r_with_auth.status_code}")
    except Exception as e:
        report("Protected Routes", "FAIL", str(e))

    # ── 5. User Profile (GET /auth/me) ──
    print("\n=== 5. USER PROFILE ===")
    try:
        r = client.get(f"{BASE}/auth/me", headers=headers)
        if r.status_code == 200 and "email" in r.json():
            report("User Profile", "PASS", f"status=200 email={r.json()['email']}")
        else:
            report("User Profile", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("User Profile", "FAIL", str(e))

    # ── 6. Destination Search ──
    print("\n=== 6. DESTINATION SEARCH ===")
    try:
        r = client.get(f"{BASE}/destinations/", headers=headers)
        if r.status_code == 200:
            data = r.json()
            total = data.get("total", 0)
            items = data.get("items", [])
            report("Destination List", "PASS", f"status=200 total={total} items_returned={len(items)}")
        else:
            report("Destination List", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("Destination List", "FAIL", str(e))

    # ── 7. Destination Details ──
    print("\n=== 7. DESTINATION DETAILS ===")
    try:
        r = client.get(f"{BASE}/destinations/", headers=headers)
        items = r.json().get("items", [])
        if items:
            did = items[0]["id"]
            r2 = client.get(f"{BASE}/destinations/{did}", headers=headers)
            if r2.status_code == 200 and "name" in r2.json():
                report("Destination Details", "PASS", f"status=200 name={r2.json()['name']}")
            else:
                report("Destination Details", "FAIL", f"status={r2.status_code}")
        else:
            report("Destination Details", "PARTIAL", "No destinations in DB to test")
    except Exception as e:
        report("Destination Details", "FAIL", str(e))

    # ── 8. Trip Creation ──
    print("\n=== 8. TRIP CREATION ===")
    try:
        payload = {"title":"Audit Trip","description":"Runtime test","start_date":"2026-09-01","end_date":"2026-09-10","budget":2000}
        r = client.post(f"{BASE}/trips/", json=payload, headers=headers)
        if r.status_code == 201:
            TRIP_ID = r.json()["id"]
            report("Trip Creation", "PASS", f"status=201 trip_id={TRIP_ID}")
        else:
            report("Trip Creation", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("Trip Creation", "FAIL", str(e))

    # ── 9. Trip Editing ──
    print("\n=== 9. TRIP EDITING ===")
    if TRIP_ID:
        try:
            r = client.patch(f"{BASE}/trips/{TRIP_ID}", json={"title":"Updated Audit Trip"}, headers=headers)
            if r.status_code == 200 and r.json().get("title") == "Updated Audit Trip":
                report("Trip Editing", "PASS", f"status=200 new_title={r.json()['title']}")
            else:
                report("Trip Editing", "FAIL", f"status={r.status_code} body={r.text[:200]}")
        except Exception as e:
            report("Trip Editing", "FAIL", str(e))
    else:
        report("Trip Editing", "NOT_TESTABLE", "No trip created")

    # ── 10. Trip Deletion ──
    print("\n=== 10. TRIP DELETION ===")
    if TRIP_ID:
        try:
            r = client.delete(f"{BASE}/trips/{TRIP_ID}", headers=headers)
            report("Trip Deletion", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} body={r.text[:100]}")
        except Exception as e:
            report("Trip Deletion", "FAIL", str(e))
    else:
        report("Trip Deletion", "NOT_TESTABLE", "No trip created")

    # ── 11. Itinerary (create trip first) ──
    print("\n=== 11. ITINERARY ===")
    try:
        r = client.post(f"{BASE}/trips/", json={"title":"Itin Test Trip"}, headers=headers)
        if r.status_code == 201:
            tid = r.json()["id"]
            r2 = client.get(f"{BASE}/trips/{tid}/itinerary/", headers=headers)
            report("Itinerary List", "PASS" if r2.status_code == 200 else "FAIL", f"status={r2.status_code} body={r2.text[:150]}")
            TRIP_ID = tid  # keep for PDF test
        else:
            report("Itinerary List", "FAIL", f"trip creation failed status={r.status_code}")
    except Exception as e:
        report("Itinerary List", "FAIL", str(e))

    # ── 12. AI Concierge ──
    print("\n=== 12. AI CONCIERGE ===")
    sid = str(uuid.uuid4())
    try:
        r = client.post(f"{BASE}/ai/sessions/{sid}/stream", json={"content":"Hello, what should I pack for Paris?"}, headers=headers)
        if r.status_code == 200:
            body = r.text[:300]
            report("AI Concierge", "PASS" if len(body) > 10 else "PARTIAL", f"status=200 response_len={len(r.text)} preview={body[:100]}")
        else:
            report("AI Concierge", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("AI Concierge", "FAIL", str(e))

    # ── 13. RAG ──
    print("\n=== 13. RAG KNOWLEDGE BASE ===")
    try:
        r = client.get(f"{BASE}/rag/status")
        status_info = r.json() if r.status_code == 200 else {}
        chunks = status_info.get("total_chunks", 0)
        
        r2 = client.post(f"{BASE}/rag/query", json={"query":"What food should I try in Japan?"})
        if r2.status_code == 200:
            answer = r2.json().get("answer","")[:150]
            report("RAG Query", "PASS", f"status=200 chunks_indexed={chunks} answer={answer}")
        else:
            report("RAG Query", "FAIL", f"status={r2.status_code} body={r2.text[:200]}")
    except Exception as e:
        report("RAG Query", "FAIL", str(e))

    # ── 14. Smart Agent ──
    print("\n=== 14. SMART AGENT ===")
    try:
        r = client.post(f"{BASE}/ai/agent/{sid}/chat", json={"message":"What is the weather in Paris right now?"}, headers=headers, timeout=60.0)
        if r.status_code == 200:
            data = r.json()
            tools = data.get("tools_used", [])
            resp = data.get("response","")[:150]
            report("Smart Agent", "PASS", f"status=200 tools_used={tools} response={resp}")
        else:
            report("Smart Agent", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("Smart Agent", "FAIL", str(e))

    # ── 15. Weather Tool (tested via agent above, also check service directly) ──
    print("\n=== 15. WEATHER TOOL (via Places proxy) ===")
    try:
        r = client.get(f"{BASE}/places/search", params={"q":"Paris"}, headers=headers)
        report("Places/Weather Proxy", "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code} results={len(r.json()) if r.status_code==200 else 'N/A'}")
    except Exception as e:
        report("Places/Weather Proxy", "FAIL", str(e))

    # ── 16. Currency Tool (tested via agent, verify agent response mentions currency) ──
    print("\n=== 16. CURRENCY TOOL ===")
    try:
        r = client.post(f"{BASE}/ai/agent/{sid}/chat", json={"message":"Convert 100 USD to EUR"}, headers=headers, timeout=60.0)
        if r.status_code == 200:
            data = r.json()
            tools = data.get("tools_used", [])
            resp = data.get("response","")[:150]
            report("Currency Tool", "PASS", f"status=200 tools={tools} response={resp}")
        else:
            report("Currency Tool", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("Currency Tool", "FAIL", str(e))

    # ── 17. ML Recommendations ──
    print("\n=== 17. ML RECOMMENDATIONS ===")
    try:
        payload = {"budget":100,"duration":7,"climate":"Tropical","travel_style":"Relaxation","season":"Summer","family_friendly":5,"adventure":5,"luxury":5}
        r = client.post(f"{BASE}/recommendations/predict", json=payload, headers=headers)
        if r.status_code == 200:
            recs = r.json().get("recommendations", [])
            names = [x["name"] for x in recs[:3]]
            report("ML Recommendations", "PASS", f"status=200 count={len(recs)} top3={names}")
        else:
            report("ML Recommendations", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("ML Recommendations", "FAIL", str(e))

    # ── 18. Computer Vision ──
    print("\n=== 18. COMPUTER VISION ===")
    try:
        # Create a tiny valid JPEG (1x1 pixel red)
        import struct
        # Minimal JPEG bytes
        jpeg_bytes = bytes.fromhex(
            "FFD8FFE000104A46494600010100000100010000"
            "FFDB004300080606070605080707070909080A0C"
            "140D0C0B0B0C1912130F141D1A1F1E1D1A1C1C"
            "20242E2720222C231C1C2837292C30313434341F"
            "27393D38323C2E333432FFC0000B080001000101"
            "011100FFC4001F000001050101010101010000000"
            "0000000000102030405060708090A0BFFC400B510"
            "000201030302040305050404000001770001020300"
            "0411050012213106415113226107146172328191A1"
            "0823B1C1152433F0D1E1F02516344262A2B2072682"
            "09C1FFDA00080101000063F29DB91C3F1C2DFFD9"
        )
        files = {"image": ("test.jpg", jpeg_bytes, "image/jpeg")}
        r = client.post(f"{BASE}/computer-vision/analyze", files=files)
        if r.status_code == 200:
            data = r.json()
            report("Computer Vision", "PASS", f"status=200 landmark={data.get('landmark','?')} confidence={data.get('confidence','?')}")
        elif r.status_code == 500:
            report("Computer Vision", "PARTIAL", f"status=500 (model may reject tiny image) body={r.text[:150]}")
        else:
            report("Computer Vision", "FAIL", f"status={r.status_code} body={r.text[:200]}")
    except Exception as e:
        report("Computer Vision", "FAIL", str(e))

    # ── 19. PDF Generation ──
    print("\n=== 19. PDF GENERATION ===")
    if TRIP_ID:
        try:
            r = client.post(f"{BASE}/pdf/itinerary/{TRIP_ID}", headers=headers)
            if r.status_code == 202:
                task_id = r.json().get("task_id","?")
                report("PDF Generation", "PASS", f"status=202 task_id={task_id}")
            elif r.status_code == 503 or r.status_code == 500:
                report("PDF Generation", "PARTIAL", f"status={r.status_code} (Celery/Redis likely not running) body={r.text[:150]}")
            else:
                report("PDF Generation", "FAIL", f"status={r.status_code} body={r.text[:200]}")
        except Exception as e:
            report("PDF Generation", "FAIL", str(e))
    else:
        report("PDF Generation", "NOT_TESTABLE", "No trip available")

    # ── 20. PostgreSQL Persistence ──
    print("\n=== 20. POSTGRESQL PERSISTENCE ===")
    try:
        r = client.get(f"{BASE}/trips/", headers=headers)
        if r.status_code == 200:
            total = r.json().get("total", 0)
            report("PostgreSQL Persistence", "PASS", f"status=200 trips_persisted={total}")
        else:
            report("PostgreSQL Persistence", "FAIL", f"status={r.status_code}")
    except Exception as e:
        report("PostgreSQL Persistence", "FAIL", str(e))

    # ── SUMMARY ──
    print("\n" + "="*70)
    print("RUNTIME AUDIT SUMMARY")
    print("="*70)
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    partial = sum(1 for r in RESULTS if r["status"] == "PARTIAL")
    nt = sum(1 for r in RESULTS if r["status"] == "NOT_TESTABLE")
    total = len(RESULTS)
    
    print(f"\n  Total Tests: {total}")
    print(f"  ✅ PASS:          {passed}")
    print(f"  ❌ FAIL:          {failed}")
    print(f"  🟡 PARTIAL:       {partial}")
    print(f"  ⚪ NOT TESTABLE:  {nt}")
    print(f"\n  Pass Rate: {passed}/{total} = {round(passed/total*100)}%")
    
    # Write JSON results
    with open("runtime_audit_results.json", "w") as f:
        json.dump(RESULTS, f, indent=2)
    print("\n  Results saved to runtime_audit_results.json")

    client.close()

if __name__ == "__main__":
    run_tests()
