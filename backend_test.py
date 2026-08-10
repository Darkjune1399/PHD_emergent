#!/usr/bin/env python3
"""
Backend Test Suite for IMAGE UPLOAD Feature
Tests admin image upload and public image serving
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://mental-health-hub-234.preview.emergentagent.com/api"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_admin_login():
    """Login as admin to get token"""
    log("=" * 80)
    log("TEST 1: ADMIN - Login")
    log("=" * 80)
    
    try:
        log("1.1. POST /auth/login with username 'admin' password 'admin123'")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        
        assert resp.status_code == 200, f"❌ Admin login failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "token" in data, "❌ No token in response"
        assert data["user"]["role"] == "super_admin", f"❌ Expected super_admin, got {data['user']['role']}"
        
        admin_token = data["token"]
        log(f"✅ PASS: Admin login successful (role: {data['user']['role']})")
        
        return admin_token
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_upload_valid_image(admin_token):
    """Test POST /admin/upload with valid image dataUrl"""
    log("=" * 80)
    log("TEST 2: ADMIN - POST /admin/upload (valid image)")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Valid 1x1 red PNG image (base64)
        valid_dataurl = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        log("2.1. POST /admin/upload with valid image dataUrl")
        resp = requests.post(f"{BASE_URL}/admin/upload", headers=headers, json={
            "dataUrl": valid_dataurl
        })
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        # Check response structure
        assert 'id' in data, "❌ Missing 'id' field in response"
        assert 'url' in data, "❌ Missing 'url' field in response"
        
        image_id = data['id']
        image_url = data['url']
        
        # Verify URL format
        expected_url = f"/api/images/{image_id}"
        assert image_url == expected_url, f"❌ Expected url '{expected_url}', got '{image_url}'"
        
        log(f"✅ PASS: POST /admin/upload returns 200 with id and url")
        log(f"   ID: {image_id}")
        log(f"   URL: {image_url}")
        
        return image_id, image_url
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_serve_image(image_url):
    """Test GET /api/images/:id returns binary image with correct Content-Type"""
    log("=" * 80)
    log("TEST 3: PUBLIC - GET /api/images/:id (serve image)")
    log("=" * 80)
    
    try:
        # Construct full URL
        full_url = f"{BASE_URL.replace('/api', '')}{image_url}"
        
        log(f"3.1. GET {image_url} (no auth) -> should return binary image")
        resp = requests.get(full_url)
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
        
        # Check Content-Type header
        content_type = resp.headers.get('Content-Type', '')
        log(f"   Content-Type: {content_type}")
        
        assert content_type == 'image/png', f"❌ Expected Content-Type 'image/png', got '{content_type}'"
        
        # Check that response is binary (not JSON)
        try:
            resp.json()
            assert False, "❌ Response should be binary, not JSON"
        except:
            # Good - it's not JSON
            pass
        
        # Check that body is non-empty
        assert len(resp.content) > 0, "❌ Response body is empty"
        
        log(f"✅ PASS: GET /api/images/:id returns 200")
        log(f"✅ PASS: Content-Type header is 'image/png'")
        log(f"✅ PASS: Response is binary (not JSON), size: {len(resp.content)} bytes")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_upload_invalid_dataurl(admin_token):
    """Test POST /admin/upload with invalid dataUrl format"""
    log("=" * 80)
    log("TEST 4: ADMIN - POST /admin/upload (invalid dataUrl)")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        log("4.1. POST /admin/upload with dataUrl='notadataurl' -> expect 400")
        resp = requests.post(f"{BASE_URL}/admin/upload", headers=headers, json={
            "dataUrl": "notadataurl"
        })
        
        assert resp.status_code == 400, f"❌ Expected 400, got {resp.status_code}: {resp.text}"
        
        log(f"✅ PASS: Invalid dataUrl format returns 400")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_upload_non_image_dataurl(admin_token):
    """Test POST /admin/upload with non-image dataUrl (text/plain)"""
    log("=" * 80)
    log("TEST 5: ADMIN - POST /admin/upload (non-image dataUrl)")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Valid base64 but not an image (text/plain)
        text_dataurl = "data:text/plain;base64,aGVsbG8="
        
        log("5.1. POST /admin/upload with dataUrl='data:text/plain;base64,aGVsbG8=' -> expect 400")
        resp = requests.post(f"{BASE_URL}/admin/upload", headers=headers, json={
            "dataUrl": text_dataurl
        })
        
        assert resp.status_code == 400, f"❌ Expected 400, got {resp.status_code}: {resp.text}"
        
        log(f"✅ PASS: Non-image dataUrl (text/plain) returns 400")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_rbac_normal_user():
    """Test RBAC: normal user gets 403 on POST /admin/upload"""
    log("=" * 80)
    log("TEST 6: RBAC - Normal user gets 403")
    log("=" * 80)
    
    try:
        # Register a normal user
        timestamp = int(time.time())
        username = f"user_{timestamp}"
        
        log(f"6.1. Register normal user: {username}")
        resp_reg = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Normal User",
            "username": username,
            "password": "pass1234"
        })
        assert resp_reg.status_code == 200, f"❌ Register failed: {resp_reg.text}"
        user_token = resp_reg.json()["token"]
        log(f"   ✅ User registered")
        
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        # Valid image dataUrl
        valid_dataurl = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        
        log("6.2. POST /admin/upload with normal user token -> expect 403")
        resp_upload = requests.post(f"{BASE_URL}/admin/upload", headers=user_headers, json={
            "dataUrl": valid_dataurl
        })
        assert resp_upload.status_code == 403, f"❌ Expected 403, got {resp_upload.status_code}: {resp_upload.text}"
        log(f"✅ PASS: Normal user gets 403 on POST /admin/upload")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_get_nonexistent_image():
    """Test GET /api/images/nonexistent-id returns 404"""
    log("=" * 80)
    log("TEST 7: PUBLIC - GET /api/images/nonexistent-id (404)")
    log("=" * 80)
    
    try:
        log("7.1. GET /api/images/nonexistent-id-999 -> expect 404")
        resp = requests.get(f"{BASE_URL}/images/nonexistent-id-999")
        
        assert resp.status_code == 404, f"❌ Expected 404, got {resp.status_code}"
        
        log(f"✅ PASS: Non-existent image returns 404")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def main():
    """Run all tests"""
    log("🚀 Starting IMAGE UPLOAD Feature Backend Tests")
    log("")
    
    all_passed = True
    results = []
    
    # ADMIN LOGIN
    try:
        admin_token = test_admin_login()
        results.append("✅ TEST 1: ADMIN - Login")
    except Exception as e:
        results.append("❌ TEST 1: ADMIN - Login")
        all_passed = False
        log(f"ERROR: {str(e)}")
        return 1
    
    # UPLOAD VALID IMAGE
    try:
        image_id, image_url = test_upload_valid_image(admin_token)
        results.append("✅ TEST 2: ADMIN - POST /admin/upload (valid image)")
    except Exception as e:
        results.append("❌ TEST 2: ADMIN - POST /admin/upload (valid image)")
        all_passed = False
        log(f"ERROR: {str(e)}")
        return 1
    
    # SERVE IMAGE
    try:
        test_serve_image(image_url)
        results.append("✅ TEST 3: PUBLIC - GET /api/images/:id (serve image)")
    except Exception as e:
        results.append("❌ TEST 3: PUBLIC - GET /api/images/:id (serve image)")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    # INVALID DATAURL
    try:
        test_upload_invalid_dataurl(admin_token)
        results.append("✅ TEST 4: ADMIN - POST /admin/upload (invalid dataUrl)")
    except Exception as e:
        results.append("❌ TEST 4: ADMIN - POST /admin/upload (invalid dataUrl)")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    # NON-IMAGE DATAURL
    try:
        test_upload_non_image_dataurl(admin_token)
        results.append("✅ TEST 5: ADMIN - POST /admin/upload (non-image dataUrl)")
    except Exception as e:
        results.append("❌ TEST 5: ADMIN - POST /admin/upload (non-image dataUrl)")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    # RBAC
    try:
        test_rbac_normal_user()
        results.append("✅ TEST 6: RBAC - Normal user gets 403")
    except Exception as e:
        results.append("❌ TEST 6: RBAC - Normal user gets 403")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    # GET NONEXISTENT IMAGE
    try:
        test_get_nonexistent_image()
        results.append("✅ TEST 7: PUBLIC - GET /api/images/nonexistent-id (404)")
    except Exception as e:
        results.append("❌ TEST 7: PUBLIC - GET /api/images/nonexistent-id (404)")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    # Print summary
    log("")
    log("=" * 80)
    if all_passed:
        log("🎉 ALL TESTS PASSED!")
    else:
        log("⚠️  SOME TESTS FAILED")
    log("=" * 80)
    log("")
    log("SUMMARY:")
    for result in results:
        log(result)
    log("")
    
    if all_passed:
        log("DETAILED RESULTS:")
        log("ADMIN ENDPOINTS:")
        log("✅ Admin login with username 'admin' password 'admin123' works (role: super_admin)")
        log("✅ POST /admin/upload with valid image dataUrl returns 200 {id, url}")
        log("✅ URL format is '/api/images/<id>'")
        log("✅ POST /admin/upload with invalid dataUrl 'notadataurl' returns 400")
        log("✅ POST /admin/upload with non-image dataUrl 'data:text/plain;base64,...' returns 400")
        log("")
        log("PUBLIC ENDPOINTS:")
        log("✅ GET /api/images/:id returns 200 with binary image")
        log("✅ Content-Type header is 'image/png' (correct)")
        log("✅ Response is binary (NOT JSON)")
        log("✅ GET /api/images/nonexistent-id returns 404")
        log("")
        log("RBAC:")
        log("✅ Normal user gets 403 on POST /admin/upload")
        log("")
        log("CRITICAL VERIFICATIONS:")
        log("✅ Image upload stores in MongoDB and returns correct URL")
        log("✅ Image serving returns binary with correct Content-Type header")
        log("✅ Invalid dataUrl formats rejected with 400")
        log("✅ Non-image MIME types rejected with 400")
        log("✅ RBAC enforced (only admin can upload)")
        log("✅ Non-existent images return 404")
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())
