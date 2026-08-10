#!/usr/bin/env python3
"""
Backend Test Suite for NEW Features (UPDATE 3)
Tests:
1. Dashboard trend range filter (daily/weekly/monthly)
2. Forgot/Reset password flow (demo mode with MOCKED email)
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://mental-health-hub-234.preview.emergentagent.com/api"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_dashboard_trend_range():
    """Test GET /admin/stats?range=daily/weekly/monthly"""
    log("=" * 80)
    log("TEST A: Dashboard Trend Range Filter")
    log("=" * 80)
    
    # Login as admin
    log("1. Login as admin@siap.id")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@siap.id",
        "password": "admin123"
    })
    assert resp.status_code == 200, f"Admin login failed: {resp.status_code} {resp.text}"
    admin_token = resp.json()["token"]
    log(f"✅ Admin login successful")
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Test 1: range=daily (default, should return 14 items)
    log("2. GET /admin/stats?range=daily -> expect trend length 14")
    resp = requests.get(f"{BASE_URL}/admin/stats?range=daily", headers=headers)
    assert resp.status_code == 200, f"Stats failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "trend" in data, "Missing 'trend' field"
    assert isinstance(data["trend"], list), "trend should be a list"
    assert len(data["trend"]) == 14, f"Expected trend length 14 for daily, got {len(data['trend'])}"
    
    # Verify each trend item has {date, count}
    for item in data["trend"]:
        assert "date" in item, "Trend item missing 'date'"
        assert "count" in item, "Trend item missing 'count'"
    
    log(f"✅ PASS: range=daily -> trend length = {len(data['trend'])}")
    log(f"   Sample trend items: {data['trend'][:3]}")
    
    # Test 2: range=weekly (should return 8 items)
    log("3. GET /admin/stats?range=weekly -> expect trend length 8")
    resp = requests.get(f"{BASE_URL}/admin/stats?range=weekly", headers=headers)
    assert resp.status_code == 200, f"Stats failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "trend" in data, "Missing 'trend' field"
    assert isinstance(data["trend"], list), "trend should be a list"
    assert len(data["trend"]) == 8, f"Expected trend length 8 for weekly, got {len(data['trend'])}"
    
    for item in data["trend"]:
        assert "date" in item, "Trend item missing 'date'"
        assert "count" in item, "Trend item missing 'count'"
    
    log(f"✅ PASS: range=weekly -> trend length = {len(data['trend'])}")
    log(f"   Sample trend items: {data['trend'][:3]}")
    
    # Test 3: range=monthly (should return 6 items)
    log("4. GET /admin/stats?range=monthly -> expect trend length 6")
    resp = requests.get(f"{BASE_URL}/admin/stats?range=monthly", headers=headers)
    assert resp.status_code == 200, f"Stats failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "trend" in data, "Missing 'trend' field"
    assert isinstance(data["trend"], list), "trend should be a list"
    assert len(data["trend"]) == 6, f"Expected trend length 6 for monthly, got {len(data['trend'])}"
    
    for item in data["trend"]:
        assert "date" in item, "Trend item missing 'date'"
        assert "count" in item, "Trend item missing 'count'"
    
    log(f"✅ PASS: range=monthly -> trend length = {len(data['trend'])}")
    log(f"   Sample trend items: {data['trend'][:3]}")
    
    # Test 4: no range parameter (should default to daily, 14 items)
    log("5. GET /admin/stats (no range) -> expect default to daily (length 14)")
    resp = requests.get(f"{BASE_URL}/admin/stats", headers=headers)
    assert resp.status_code == 200, f"Stats failed: {resp.status_code} {resp.text}"
    data = resp.json()
    assert "trend" in data, "Missing 'trend' field"
    assert len(data["trend"]) == 14, f"Expected trend length 14 for default (daily), got {len(data['trend'])}"
    log(f"✅ PASS: no range parameter -> defaults to daily (trend length = {len(data['trend'])})")
    
    # Verify other stat fields are still present
    log("6. Verify other stat fields still present")
    required_fields = ["total", "distribution", "alertStatus", "newAlerts", "totalUsers", "totalMembers"]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"
    log(f"✅ PASS: All other stat fields present: {required_fields}")
    
    log("")
    log("=" * 80)
    log("✅ TEST A COMPLETE: Dashboard Trend Range Filter - ALL TESTS PASSED")
    log("=" * 80)
    
    return True

def test_forgot_reset_password():
    """Test forgot/reset password flow (demo mode with MOCKED email)"""
    log("")
    log("=" * 80)
    log("TEST B: Forgot/Reset Password Flow (Demo Mode)")
    log("=" * 80)
    
    # Step 1: Register a fresh normal user
    timestamp = int(time.time())
    email = f"resettest{timestamp}@example.com"
    original_password = "origpass1"
    
    log(f"1. Register fresh user: {email} with password '{original_password}'")
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Reset Test User",
        "email": email,
        "password": original_password
    })
    assert resp.status_code == 200, f"Register failed: {resp.status_code} {resp.text}"
    user_data = resp.json()
    assert "token" in user_data, "No token in response"
    log(f"✅ User registered: {email}")
    
    # Step 2: POST /auth/forgot-password with existing email -> should return token
    log(f"2. POST /auth/forgot-password with email '{email}' -> expect 200 with token")
    resp = requests.post(f"{BASE_URL}/auth/forgot-password", json={
        "email": email
    })
    assert resp.status_code == 200, f"Forgot password failed: {resp.status_code} {resp.text}"
    forgot_data = resp.json()
    assert forgot_data.get("ok") == True, f"Expected ok=true, got {forgot_data.get('ok')}"
    assert forgot_data.get("demo") == True, f"Expected demo=true, got {forgot_data.get('demo')}"
    assert "token" in forgot_data, "Missing token in response"
    assert len(forgot_data["token"]) > 0, "Token should be non-empty string"
    
    reset_token = forgot_data["token"]
    log(f"✅ PASS: forgot-password returned {{ok:true, demo:true, token:'{reset_token[:20]}...'}}")
    
    # Step 3: POST /auth/forgot-password with non-existent email -> should return 404
    log(f"3. POST /auth/forgot-password with non-existent email -> expect 404")
    nonexistent_email = f"nonexistent-{timestamp}@x.com"
    resp = requests.post(f"{BASE_URL}/auth/forgot-password", json={
        "email": nonexistent_email
    })
    assert resp.status_code == 404, f"Expected 404 for non-existent email, got {resp.status_code}"
    log(f"✅ PASS: non-existent email correctly returns 404")
    
    # Step 4: POST /auth/reset-password with invalid token -> should return 400
    log(f"4. POST /auth/reset-password with invalid token -> expect 400")
    resp = requests.post(f"{BASE_URL}/auth/reset-password", json={
        "token": "invalidtoken123",
        "newPassword": "whatever"
    })
    assert resp.status_code == 400, f"Expected 400 for invalid token, got {resp.status_code}"
    log(f"✅ PASS: invalid token correctly returns 400")
    
    # Step 5: POST /auth/reset-password with valid token but password too short -> should return 400
    log(f"5. POST /auth/reset-password with valid token but newPassword='x' (too short) -> expect 400")
    resp = requests.post(f"{BASE_URL}/auth/reset-password", json={
        "token": reset_token,
        "newPassword": "x"
    })
    assert resp.status_code == 400, f"Expected 400 for short password, got {resp.status_code}"
    log(f"✅ PASS: password too short correctly returns 400")
    
    # Step 6: POST /auth/reset-password with valid token and valid password -> should return 200
    new_password = "newpass99"
    log(f"6. POST /auth/reset-password with valid token and newPassword='{new_password}' -> expect 200")
    resp = requests.post(f"{BASE_URL}/auth/reset-password", json={
        "token": reset_token,
        "newPassword": new_password
    })
    assert resp.status_code == 200, f"Reset password failed: {resp.status_code} {resp.text}"
    reset_data = resp.json()
    assert reset_data.get("ok") == True, f"Expected ok=true, got {reset_data.get('ok')}"
    log(f"✅ PASS: reset-password successful {{ok:true}}")
    
    # Step 7: Verify login with OLD password fails (401)
    log(f"7. Verify login with OLD password '{original_password}' -> expect 401")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": original_password
    })
    assert resp.status_code == 401, f"Expected 401 for old password, got {resp.status_code}"
    log(f"✅ PASS: old password no longer works (401)")
    
    # Step 8: Verify login with NEW password succeeds (200)
    log(f"8. Verify login with NEW password '{new_password}' -> expect 200 with token")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": new_password
    })
    assert resp.status_code == 200, f"Login with new password failed: {resp.status_code} {resp.text}"
    login_data = resp.json()
    assert "token" in login_data, "No token in login response"
    log(f"✅ PASS: new password works correctly (200 with token)")
    
    # Step 9: Verify token is single-use (try to use same token again -> should return 400)
    log(f"9. Verify token single-use: POST /auth/reset-password with SAME token again -> expect 400")
    resp = requests.post(f"{BASE_URL}/auth/reset-password", json={
        "token": reset_token,
        "newPassword": "anotherpass"
    })
    assert resp.status_code == 400, f"Expected 400 for already-used token, got {resp.status_code}"
    log(f"✅ PASS: token is single-use (already consumed/deleted, returns 400)")
    
    log("")
    log("=" * 80)
    log("✅ TEST B COMPLETE: Forgot/Reset Password Flow - ALL TESTS PASSED")
    log("=" * 80)
    
    return True

def main():
    """Run all tests"""
    try:
        log("🚀 Starting NEW FEATURES Backend Tests (UPDATE 3)")
        log("")
        
        # Test A: Dashboard trend range filter
        test_dashboard_trend_range()
        
        # Test B: Forgot/Reset password
        test_forgot_reset_password()
        
        log("")
        log("=" * 80)
        log("🎉 ALL NEW FEATURES TESTS PASSED!")
        log("=" * 80)
        log("")
        log("SUMMARY:")
        log("✅ TEST A: Dashboard Trend Range Filter")
        log("   - GET /admin/stats?range=daily -> trend length 14 ✅")
        log("   - GET /admin/stats?range=weekly -> trend length 8 ✅")
        log("   - GET /admin/stats?range=monthly -> trend length 6 ✅")
        log("   - GET /admin/stats (no range) -> defaults to daily (length 14) ✅")
        log("   - All other stat fields still present ✅")
        log("")
        log("✅ TEST B: Forgot/Reset Password Flow (Demo Mode)")
        log("   - POST /auth/forgot-password with existing email -> 200 {ok:true, demo:true, token} ✅")
        log("   - POST /auth/forgot-password with non-existent email -> 404 ✅")
        log("   - POST /auth/reset-password with invalid token -> 400 ✅")
        log("   - POST /auth/reset-password with short password -> 400 ✅")
        log("   - POST /auth/reset-password with valid token & password -> 200 {ok:true} ✅")
        log("   - Login with old password -> 401 (no longer works) ✅")
        log("   - Login with new password -> 200 with token ✅")
        log("   - Token single-use verification -> 400 (already consumed) ✅")
        
        return 0
        
    except AssertionError as e:
        log("")
        log("=" * 80)
        log(f"❌ TEST FAILED: {str(e)}")
        log("=" * 80)
        return 1
    except Exception as e:
        log("")
        log("=" * 80)
        log(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        log("=" * 80)
        return 1

if __name__ == "__main__":
    exit(main())
