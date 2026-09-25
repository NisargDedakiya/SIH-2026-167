import urllib.request
import json
import sys

BASE_URL = "http://localhost:3000"

def run_post(endpoint, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{endpoint}",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}
    except Exception as e:
        return 0, {"error": str(e)}

def run_get(endpoint):
    req = urllib.request.Request(f"{BASE_URL}{endpoint}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"raw": body}
    except Exception as e:
        return 0, {"error": str(e)}

print("=== SATQUERY END-TO-END DEMO TEST SUITE ===")

# Discover images
st, images = run_get("/api/v1/images")
print(f"1. Discovered {len(images)} images in catalog (status {st})")

grounding_img = next((img for img in images if "grounding" in img.get("filename", "").lower()), images[0])
print(f"   Grounding Target Image: {grounding_img['id']} ({grounding_img['filename']})")

# Discover temporal pairs
st, t_pairs = run_get("/api/v1/temporal/pairs")
valid_t_pair = next((p for p in t_pairs if p.get("validation", {}).get("status_code") != "INVALID_STORAGE"), t_pairs[0] if t_pairs else None)
print(f"2. Temporal Pairs: {len(t_pairs)} registered. Picked: {valid_t_pair.get('pair_id')} (valid={valid_t_pair.get('validation', {}).get('valid')})")

# Discover cross-modal pairs
st, cm_pairs = run_get("/api/v1/cross-modal/pairs")
valid_cm_pair = next((p for p in cm_pairs if p.get("validation", {}).get("status_code") != "INVALID_STORAGE"), cm_pairs[0] if cm_pairs else None)
print(f"3. Cross-Modal Pairs: {len(cm_pairs)} registered. Picked: {valid_cm_pair.get('id')} (valid={valid_cm_pair.get('validation', {}).get('valid')})")

# --- DEMO 1: VQA ---
print("\n--- RUNNING DEMO 1 (VQA) ---")
payload_d1 = {
    "image_ids": [grounding_img["id"]],
    "query": "What is the dominant land cover class in this satellite image?"
}
st1, res1 = run_post("/api/v1/agent/analyze", payload_d1)
print(f"Demo 1 Status: {st1}")
if st1 == 200:
    print(f"Demo 1 Answer: {res1.get('answer', '')[:120]}...")
    print(f"Demo 1 Task: {res1.get('task')}, Confidence: {res1.get('confidence', {}).get('score')}")
else:
    print(f"Demo 1 Error: {res1}")

# --- DEMO 2: GROUNDING ---
print("\n--- RUNNING DEMO 2 (Spatial Grounding) ---")
payload_d2 = {
    "image_ids": [grounding_img["id"]],
    "query": "Highlight the buildings in this image."
}
st2, res2 = run_post("/api/v1/agent/analyze", payload_d2)
print(f"Demo 2 Status: {st2}")
if st2 == 200:
    print(f"Demo 2 Answer: {res2.get('answer', '')[:120]}...")
    print(f"Demo 2 Task: {res2.get('task')}")
    print(f"Demo 2 Evidence count: {len(res2.get('evidence', []))}")
    if res2.get('evidence'):
        ev0 = res2['evidence'][0]
        print(f"   First region: bbox={ev0.get('bbox')}, label={ev0.get('label')}, confidence={ev0.get('confidence')}")
else:
    print(f"Demo 2 Error: {res2}")

# --- DEMO 3: BI-TEMPORAL CHANGE DETECTION ---
print("\n--- RUNNING DEMO 3 (Bi-Temporal Change Detection) ---")
payload_d3 = {
    "image_ids": [valid_t_pair["image_t1"]["id"], valid_t_pair["image_t2"]["id"]],
    "pair_id": valid_t_pair["pair_id"],
    "query": "What changed between these images?"
}
st3, res3 = run_post("/api/v1/agent/analyze", payload_d3)
print(f"Demo 3 Status: {st3}")
if st3 == 200:
    print(f"Demo 3 Answer: {res3.get('answer', '')[:120]}...")
    print(f"Demo 3 Task: {res3.get('task')}")
    print(f"Demo 3 Evidence count: {len(res3.get('evidence', []))}")
else:
    print(f"Demo 3 Error: {res3}")

# --- DEMO 4: OPTICAL + SAR FUSION ---
print("\n--- RUNNING DEMO 4 (Optical + SAR Cross-Modal Fusion) ---")
payload_d4 = {
    "image_ids": [valid_cm_pair["optical_image"]["id"], valid_cm_pair["sar_image"]["id"]],
    "pair_id": valid_cm_pair["id"],
    "query": "Compare optical and SAR imagery."
}
st4, res4 = run_post("/api/v1/agent/analyze", payload_d4)
print(f"Demo 4 Status: {st4}")
if st4 == 200:
    print(f"Demo 4 Answer: {res4.get('answer', '')[:120]}...")
    print(f"Demo 4 Task: {res4.get('task')}")
    print(f"Demo 4 Evidence count: {len(res4.get('evidence', []))}")
else:
    print(f"Demo 4 Error: {res4}")

# --- DEMO MISSING STORAGE VALIDATION (409 CONFLICT) ---
print("\n--- TESTING STORAGE OBJECT MISSING (HTTP 409) ---")
broken_img_id = "0639d84b-a990-4c00-80cf-be78e99a2577"
payload_missing = {
    "image_ids": [broken_img_id],
    "query": "What is in this image?"
}
st_m, res_m = run_post("/api/v1/agent/analyze", payload_missing)
print(f"Missing Storage Test Status: {st_m}")
print(f"Missing Storage Error Code: {res_m.get('error', {}).get('code')}")
print(f"Missing Storage Message: {res_m.get('error', {}).get('message')}")
print(f"Missing Storage Details: {res_m.get('error', {}).get('details')}")

print("\n=== LIVE TEST SUITE SUMMARY ===")
print(f"Demo 1: {'PASSED' if st1 == 200 else 'FAILED'}")
print(f"Demo 2: {'PASSED' if st2 == 200 else 'FAILED'}")
print(f"Demo 3: {'PASSED' if st3 == 200 else 'FAILED'}")
print(f"Demo 4: {'PASSED' if st4 == 200 else 'FAILED'}")
print(f"Storage 409 Validation: {'PASSED' if st_m == 409 and res_m.get('error', {}).get('code') == 'IMAGE_OBJECT_MISSING' else 'FAILED'}")
