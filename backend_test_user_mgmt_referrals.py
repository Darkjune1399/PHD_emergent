#!/usr/bin/env python3
"""
Backend Test Suite for SIAP User Management & Referrals
Tests admin endpoints for user management (suspend, reset password) and referrals CRUD
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://mental-health-hub-234.preview.emergentagent.com/api"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_setup_normal_user():
    """Setup: Register a fresh normal user and add 1 member + 1 assessment"""
    log("=" * 80)
    log("SETUP: Creating normal user with member and assessment")
    log("=" * 80)
    
    # Register normal user with unique email
    timestamp = int(time.time())
    email = f"normaluser{timestamp}@example.com"
    password = "oldpass123"
    
    log(f"1. Registering normal user: {email}")
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Normal User",
        "email": email,
        "password": password
    })
    
    try:
        assert resp.status_code == 200, f"Register failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "token" in data, "No token in response"
        assert data["user"]["role"] == "user", f"Expected role 'user', got {data['user']['role']}"
        
        user_token = data["token"]
        user_id = data["user"]["id"]
        log(f"✅ Normal user registered: {email}, role={data['user']['role']}, id={user_id}")
        print(f"TEST RESULT: User registration - PASS")
    except AssertionError as e:
        print(f"TEST RESULT: User registration - FAIL: {e}")
        raise
    
    # Add 1 member
    headers = {"Authorization": f"Bearer {user_token}"}
    
    log("2. Adding member age ~30 (dob: 1995-01-01)")
    resp = requests.post(f"{BASE_URL}/members", headers=headers, json={
        "fullName": "Test Member",
        "gender": "Laki-laki",
        "dob": "1995-01-01",
        "relationship": "Diri Sendiri"
    })
    
    try:
        assert resp.status_code == 200, f"Add member failed: {resp.text}"
        member = resp.json()
        member_id = member["id"]
        log(f"✅ Member added: {member['fullName']}, age={member['age']}, id={member_id}")
        print(f"TEST RESULT: Add member - PASS")
    except AssertionError as e:
        print(f"TEST RESULT: Add member - FAIL: {e}")
        raise
    
    # Submit 1 assessment (PHQ-9 with low score)
    log("3. Submitting 1 PHQ-9 assessment")
    answers = {str(i): 1 for i in range(1, 10)}
    resp = requests.post(f"{BASE_URL}/assessments", headers=headers, json={
        "memberId": member_id,
        "instrumentCode": "phq9",
        "answers": answers
    })
    
    try:
        assert resp.status_code == 200, f"Assessment failed: {resp.text}"
        assessment = resp.json()
        log(f"✅ Assessment submitted: total={assessment['result']['total']}")
        print(f"TEST RESULT: Submit assessment - PASS")
    except AssertionError as e:
        print(f"TEST RESULT: Submit assessment - FAIL: {e}")
        raise
    
    return {
        "user_token": user_token,
        "user_id": user_id,
        "email": email,
        "password": password,
        "member_id": member_id
    }

def test_admin_login():
    """Get admin token"""
    log("=" * 80)
    log("ADMIN LOGIN")
    log("=" * 80)
    
    log("1. Login as admin@siap.id with password admin123")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@siap.id",
        "password": "admin123"
    })
    
    try:
        assert resp.status_code == 200, f"Admin login failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "token" in data, "No token in response"
        assert data["user"]["role"] == "super_admin", f"Expected role 'super_admin', got {data['user']['role']}"
        
        admin_token = data["token"]
        log(f"✅ Admin login successful: email={data['user']['email']}, role={data['user']['role']}")
        print(f"TEST RESULT: Admin login - PASS")
        return admin_token
    except AssertionError as e:
        print(f"TEST RESULT: Admin login - FAIL: {e}")
        raise

def test_user_management(admin_token, setup_data):
    """Test user management endpoints"""
    log("=" * 80)
    log("TEST: USER MANAGEMENT")
    log("=" * 80)
    
    headers = {"Authorization": f"Bearer {admin_token}"}
    user_id = setup_data["user_id"]
    user_email = setup_data["email"]
    old_password = setup_data["password"]
    
    # 1. GET /admin/users
    log("1. GET /admin/users -> list users with memberCount, assessmentCount")
    resp = requests.get(f"{BASE_URL}/admin/users", headers=headers)
    
    try:
        assert resp.status_code == 200, f"GET /admin/users failed: {resp.status_code} {resp.text}"
        users = resp.json()
        assert isinstance(users, list), "Expected list of users"
        
        # Find our test user
        test_user = None
        for u in users:
            if u["id"] == user_id:
                test_user = u
                break
        
        assert test_user is not None, f"Test user {user_id} not found in users list"
        assert "status" in test_user, "Missing 'status' field"
        assert "memberCount" in test_user, "Missing 'memberCount' field"
        assert "assessmentCount" in test_user, "Missing 'assessmentCount' field"
        assert test_user["memberCount"] >= 1, f"Expected memberCount >= 1, got {test_user['memberCount']}"
        assert test_user["assessmentCount"] >= 1, f"Expected assessmentCount >= 1, got {test_user['assessmentCount']}"
        
        log(f"✅ GET /admin/users returned {len(users)} users")
        log(f"   Test user found: email={test_user['email']}, status={test_user['status']}, memberCount={test_user['memberCount']}, assessmentCount={test_user['assessmentCount']}")
        print(f"TEST RESULT: GET /admin/users - PASS (status={resp.status_code}, memberCount={test_user['memberCount']}, assessmentCount={test_user['assessmentCount']})")
    except AssertionError as e:
        print(f"TEST RESULT: GET /admin/users - FAIL: {e}")
        raise
    
    # 2. PATCH /admin/users/:id with status:'suspended'
    log("2. PATCH /admin/users/:id with status:'suspended'")
    resp = requests.patch(f"{BASE_URL}/admin/users/{user_id}", headers=headers, json={
        "status": "suspended"
    })
    
    try:
        assert resp.status_code == 200, f"PATCH suspend failed: {resp.status_code} {resp.text}"
        updated_user = resp.json()
        assert updated_user["status"] == "suspended", f"Expected status='suspended', got {updated_user['status']}"
        assert "passwordHash" not in updated_user, "passwordHash should not be in response"
        
        log(f"✅ User suspended: status={updated_user['status']}")
        print(f"TEST RESULT: PATCH suspend user - PASS (status={resp.status_code}, user.status='suspended')")
    except AssertionError as e:
        print(f"TEST RESULT: PATCH suspend user - FAIL: {e}")
        raise
    
    # 3. Verify suspended user CANNOT login (403)
    log("3. Verify suspended user CANNOT login -> expect 403")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": user_email,
        "password": old_password
    })
    
    try:
        assert resp.status_code == 403, f"Expected 403 for suspended user login, got {resp.status_code}"
        error_data = resp.json()
        assert "error" in error_data, "Expected error message"
        
        log(f"✅ Suspended user correctly denied login: {resp.status_code} {error_data['error']}")
        print(f"TEST RESULT: Suspended user login blocked - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: Suspended user login blocked - FAIL: {e}")
        raise
    
    # 4. PATCH /admin/users/:id with status:'active'
    log("4. PATCH /admin/users/:id with status:'active'")
    resp = requests.patch(f"{BASE_URL}/admin/users/{user_id}", headers=headers, json={
        "status": "active"
    })
    
    try:
        assert resp.status_code == 200, f"PATCH activate failed: {resp.status_code} {resp.text}"
        updated_user = resp.json()
        assert updated_user["status"] == "active", f"Expected status='active', got {updated_user['status']}"
        
        log(f"✅ User reactivated: status={updated_user['status']}")
        print(f"TEST RESULT: PATCH activate user - PASS (status={resp.status_code}, user.status='active')")
    except AssertionError as e:
        print(f"TEST RESULT: PATCH activate user - FAIL: {e}")
        raise
    
    # 5. Verify active user CAN login (200)
    log("5. Verify active user CAN login -> expect 200")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": user_email,
        "password": old_password
    })
    
    try:
        assert resp.status_code == 200, f"Expected 200 for active user login, got {resp.status_code} {resp.text}"
        login_data = resp.json()
        assert "token" in login_data, "Expected token in response"
        
        log(f"✅ Active user successfully logged in: {resp.status_code}")
        print(f"TEST RESULT: Active user login allowed - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: Active user login allowed - FAIL: {e}")
        raise
    
    # 6. PATCH with invalid status -> 400
    log("6. PATCH /admin/users/:id with invalid status -> expect 400")
    resp = requests.patch(f"{BASE_URL}/admin/users/{user_id}", headers=headers, json={
        "status": "invalid"
    })
    
    try:
        assert resp.status_code == 400, f"Expected 400 for invalid status, got {resp.status_code}"
        error_data = resp.json()
        assert "error" in error_data, "Expected error message"
        
        log(f"✅ Invalid status correctly rejected: {resp.status_code} {error_data['error']}")
        print(f"TEST RESULT: PATCH invalid status rejected - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: PATCH invalid status rejected - FAIL: {e}")
        raise
    
    # 7. POST /admin/users/:id/reset-password with newPassword
    log("7. POST /admin/users/:id/reset-password with newPassword:'newpass456'")
    new_password = "newpass456"
    resp = requests.post(f"{BASE_URL}/admin/users/{user_id}/reset-password", headers=headers, json={
        "newPassword": new_password
    })
    
    try:
        assert resp.status_code == 200, f"POST reset-password failed: {resp.status_code} {resp.text}"
        reset_data = resp.json()
        assert "ok" in reset_data or reset_data.get("ok") == True, "Expected ok response"
        
        log(f"✅ Password reset successful: {resp.status_code}")
        print(f"TEST RESULT: POST reset-password - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: POST reset-password - FAIL: {e}")
        raise
    
    # 8. Verify old password fails (401)
    log("8. Verify login with old password 'oldpass123' -> expect 401")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": user_email,
        "password": old_password
    })
    
    try:
        assert resp.status_code == 401, f"Expected 401 for old password, got {resp.status_code}"
        
        log(f"✅ Old password correctly rejected: {resp.status_code}")
        print(f"TEST RESULT: Old password rejected - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: Old password rejected - FAIL: {e}")
        raise
    
    # 9. Verify new password works (200)
    log("9. Verify login with new password 'newpass456' -> expect 200")
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "email": user_email,
        "password": new_password
    })
    
    try:
        assert resp.status_code == 200, f"Expected 200 for new password, got {resp.status_code} {resp.text}"
        login_data = resp.json()
        assert "token" in login_data, "Expected token in response"
        
        # Update setup_data with new password and token
        setup_data["password"] = new_password
        setup_data["user_token"] = login_data["token"]
        
        log(f"✅ New password works: {resp.status_code}")
        print(f"TEST RESULT: New password works - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: New password works - FAIL: {e}")
        raise
    
    # 10. POST reset-password with short password -> 400
    log("10. POST /admin/users/:id/reset-password with short password 'a' -> expect 400")
    resp = requests.post(f"{BASE_URL}/admin/users/{user_id}/reset-password", headers=headers, json={
        "newPassword": "a"
    })
    
    try:
        assert resp.status_code == 400, f"Expected 400 for short password, got {resp.status_code}"
        error_data = resp.json()
        assert "error" in error_data, "Expected error message"
        
        log(f"✅ Short password correctly rejected: {resp.status_code} {error_data['error']}")
        print(f"TEST RESULT: Short password rejected - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: Short password rejected - FAIL: {e}")
        raise

def test_referrals(admin_token, setup_data):
    """Test referrals endpoints"""
    log("=" * 80)
    log("TEST: REFERRALS")
    log("=" * 80)
    
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {setup_data['user_token']}"}
    
    # 1. GET /admin/referrals
    log("1. GET /admin/referrals -> list referrals")
    resp = requests.get(f"{BASE_URL}/admin/referrals", headers=admin_headers)
    
    try:
        assert resp.status_code == 200, f"GET /admin/referrals failed: {resp.status_code} {resp.text}"
        referrals_before = resp.json()
        assert isinstance(referrals_before, list), "Expected list of referrals"
        
        log(f"✅ GET /admin/referrals returned {len(referrals_before)} referrals (includes default seeded contacts)")
        print(f"TEST RESULT: GET /admin/referrals - PASS (status={resp.status_code}, count={len(referrals_before)})")
    except AssertionError as e:
        print(f"TEST RESULT: GET /admin/referrals - FAIL: {e}")
        raise
    
    # 2. POST /admin/referrals
    log("2. POST /admin/referrals with new referral")
    new_referral = {
        "name": "RSJ Test",
        "type": "Rumah Sakit Jiwa (RSJ)",
        "contact": "021-000",
        "note": "test"
    }
    resp = requests.post(f"{BASE_URL}/admin/referrals", headers=admin_headers, json=new_referral)
    
    try:
        assert resp.status_code == 200, f"POST /admin/referrals failed: {resp.status_code} {resp.text}"
        created_referral = resp.json()
        assert "id" in created_referral, "Expected 'id' in response"
        assert created_referral["name"] == new_referral["name"], f"Expected name='{new_referral['name']}', got {created_referral['name']}"
        assert created_referral["type"] == new_referral["type"], f"Expected type='{new_referral['type']}', got {created_referral['type']}"
        assert created_referral["contact"] == new_referral["contact"], f"Expected contact='{new_referral['contact']}', got {created_referral['contact']}"
        
        referral_id = created_referral["id"]
        log(f"✅ Referral created: id={referral_id}, name={created_referral['name']}")
        print(f"TEST RESULT: POST /admin/referrals - PASS (status={resp.status_code}, id={referral_id})")
    except AssertionError as e:
        print(f"TEST RESULT: POST /admin/referrals - FAIL: {e}")
        raise
    
    # 3. GET /referrals (public endpoint with normal user token)
    log("3. GET /referrals (normal user token) -> should include 'RSJ Test'")
    resp = requests.get(f"{BASE_URL}/referrals", headers=user_headers)
    
    try:
        assert resp.status_code == 200, f"GET /referrals failed: {resp.status_code} {resp.text}"
        public_referrals = resp.json()
        assert isinstance(public_referrals, list), "Expected list of referrals"
        
        # Check if 'RSJ Test' is in the list
        rsj_test_found = False
        for ref in public_referrals:
            if ref["name"] == "RSJ Test":
                rsj_test_found = True
                break
        
        assert rsj_test_found, "Expected 'RSJ Test' in public referrals list"
        
        log(f"✅ GET /referrals returned {len(public_referrals)} referrals, 'RSJ Test' found")
        print(f"TEST RESULT: GET /referrals (user token) includes new referral - PASS (status={resp.status_code}, count={len(public_referrals)})")
    except AssertionError as e:
        print(f"TEST RESULT: GET /referrals (user token) includes new referral - FAIL: {e}")
        raise
    
    # 4. DELETE /admin/referrals/:id
    log(f"4. DELETE /admin/referrals/{referral_id}")
    resp = requests.delete(f"{BASE_URL}/admin/referrals/{referral_id}", headers=admin_headers)
    
    try:
        assert resp.status_code == 200, f"DELETE /admin/referrals failed: {resp.status_code} {resp.text}"
        delete_data = resp.json()
        assert "ok" in delete_data or delete_data.get("ok") == True, "Expected ok response"
        
        log(f"✅ Referral deleted: id={referral_id}")
        print(f"TEST RESULT: DELETE /admin/referrals/:id - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: DELETE /admin/referrals/:id - FAIL: {e}")
        raise
    
    # 5. GET /admin/referrals again to confirm removal
    log("5. GET /admin/referrals again to confirm removal")
    resp = requests.get(f"{BASE_URL}/admin/referrals", headers=admin_headers)
    
    try:
        assert resp.status_code == 200, f"GET /admin/referrals failed: {resp.status_code} {resp.text}"
        referrals_after = resp.json()
        
        # Check that 'RSJ Test' is NOT in the list
        rsj_test_found = False
        for ref in referrals_after:
            if ref["name"] == "RSJ Test":
                rsj_test_found = True
                break
        
        assert not rsj_test_found, "Expected 'RSJ Test' to be removed from referrals list"
        
        log(f"✅ Referral confirmed removed: 'RSJ Test' not in list")
        print(f"TEST RESULT: Referral removal confirmed - PASS")
    except AssertionError as e:
        print(f"TEST RESULT: Referral removal confirmed - FAIL: {e}")
        raise

def test_rbac(setup_data):
    """Test RBAC: normal user should get 403 on admin endpoints"""
    log("=" * 80)
    log("TEST: RBAC (Role-Based Access Control)")
    log("=" * 80)
    
    user_headers = {"Authorization": f"Bearer {setup_data['user_token']}"}
    
    # 1. Normal user on GET /admin/users -> 403
    log("1. Normal user token on GET /admin/users -> expect 403")
    resp = requests.get(f"{BASE_URL}/admin/users", headers=user_headers)
    
    try:
        assert resp.status_code == 403, f"Expected 403 for normal user on /admin/users, got {resp.status_code}"
        error_data = resp.json()
        assert "error" in error_data, "Expected error message"
        
        log(f"✅ Normal user correctly denied: {resp.status_code} {error_data['error']}")
        print(f"TEST RESULT: RBAC /admin/users - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: RBAC /admin/users - FAIL: {e}")
        raise
    
    # 2. Normal user on GET /admin/referrals -> 403
    log("2. Normal user token on GET /admin/referrals -> expect 403")
    resp = requests.get(f"{BASE_URL}/admin/referrals", headers=user_headers)
    
    try:
        assert resp.status_code == 403, f"Expected 403 for normal user on /admin/referrals, got {resp.status_code}"
        error_data = resp.json()
        assert "error" in error_data, "Expected error message"
        
        log(f"✅ Normal user correctly denied: {resp.status_code} {error_data['error']}")
        print(f"TEST RESULT: RBAC /admin/referrals - PASS (status={resp.status_code})")
    except AssertionError as e:
        print(f"TEST RESULT: RBAC /admin/referrals - FAIL: {e}")
        raise

def main():
    """Run all tests"""
    try:
        log("🚀 Starting SIAP User Management & Referrals Backend Tests")
        log("")
        
        # Setup
        setup_data = test_setup_normal_user()
        
        # Admin login
        admin_token = test_admin_login()
        
        # User Management tests
        test_user_management(admin_token, setup_data)
        
        # Referrals tests
        test_referrals(admin_token, setup_data)
        
        # RBAC tests
        test_rbac(setup_data)
        
        log("")
        log("=" * 80)
        log("🎉 ALL TESTS PASSED!")
        log("=" * 80)
        log("")
        log("SUMMARY:")
        log("✅ Setup: Normal user registration, member creation, assessment submission")
        log("✅ Admin login (admin@siap.id)")
        log("✅ GET /admin/users with memberCount and assessmentCount")
        log("✅ PATCH /admin/users/:id suspend user")
        log("✅ Suspended user login blocked (403)")
        log("✅ PATCH /admin/users/:id activate user")
        log("✅ Active user login allowed (200)")
        log("✅ PATCH /admin/users/:id invalid status rejected (400)")
        log("✅ POST /admin/users/:id/reset-password")
        log("✅ Old password rejected (401)")
        log("✅ New password works (200)")
        log("✅ POST reset-password short password rejected (400)")
        log("✅ GET /admin/referrals")
        log("✅ POST /admin/referrals creates new referral")
        log("✅ GET /referrals (user token) includes new referral")
        log("✅ DELETE /admin/referrals/:id removes referral")
        log("✅ RBAC: Normal user gets 403 on /admin/users")
        log("✅ RBAC: Normal user gets 403 on /admin/referrals")
        
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
