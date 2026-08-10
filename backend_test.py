#!/usr/bin/env python3
"""
Backend Test Suite for USERNAME AUTH + FEEDBACK Feature
Tests username-based authentication (replaced email) and new feedback system
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://mental-health-hub-234.preview.emergentagent.com/api"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_username_auth_register():
    """Test registration with username (not email)"""
    log("=" * 80)
    log("TEST 1: USERNAME AUTH - REGISTER")
    log("=" * 80)
    
    timestamp = int(time.time())
    username = f"user_{timestamp}"
    
    # Test 1: Register with username
    log(f"1.1. Register with username: {username}")
    resp = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Test User",
        "username": username,
        "password": "pass1234"
    })
    
    try:
        assert resp.status_code == 200, f"❌ Register failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "token" in data, "❌ No token in response"
        assert "user" in data, "❌ No user in response"
        assert "username" in data["user"], "❌ Response user missing 'username' field"
        assert "email" not in data["user"], "❌ Response should NOT have 'email' field (replaced by username)"
        assert data["user"]["username"] == username, f"❌ Expected username '{username}', got '{data['user']['username']}'"
        assert data["user"]["role"] == "user", f"❌ Expected role 'user', got '{data['user']['role']}'"
        
        user_token = data["token"]
        user_username = data["user"]["username"]
        user_id = data["user"]["id"]
        
        log(f"✅ PASS: Register with username returns token and user with username field")
        log(f"   username={user_username}, role={data['user']['role']}")
        
        # Test 2: Duplicate username should return 400
        log(f"1.2. Register with same username again -> expect 400")
        resp2 = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Another User",
            "username": username,
            "password": "different123"
        })
        assert resp2.status_code == 400, f"❌ Expected 400 for duplicate username, got {resp2.status_code}"
        error_msg = resp2.json().get("error", "").lower()
        assert "username" in error_msg and "digunakan" in error_msg, \
            f"❌ Expected 'Username sudah digunakan' error, got: {resp2.json().get('error')}"
        log(f"✅ PASS: Duplicate username returns 400 with 'Username sudah digunakan'")
        
        # Test 3: Missing username should return 400
        log(f"1.3. Register without username -> expect 400")
        resp3 = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "No Username User",
            "password": "pass1234"
        })
        assert resp3.status_code == 400, f"❌ Expected 400 for missing username, got {resp3.status_code}"
        log(f"✅ PASS: Missing username returns 400")
        
        return {
            "user_token": user_token,
            "username": user_username,
            "password": "pass1234",
            "user_id": user_id
        }
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_username_auth_login(user_data):
    """Test login with username"""
    log("=" * 80)
    log("TEST 2: USERNAME AUTH - LOGIN")
    log("=" * 80)
    
    try:
        # Test 1: Login with correct username and password
        log(f"2.1. Login with username '{user_data['username']}' and correct password")
        resp = requests.post(f"{BASE_URL}/auth/login", json={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        assert resp.status_code == 200, f"❌ Login failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "token" in data, "❌ No token in response"
        log(f"✅ PASS: Login with username returns token")
        
        # Test 2: Login with wrong password
        log(f"2.2. Login with wrong password -> expect 401")
        resp2 = requests.post(f"{BASE_URL}/auth/login", json={
            "username": user_data["username"],
            "password": "wrongpassword"
        })
        assert resp2.status_code == 401, f"❌ Expected 401 for wrong password, got {resp2.status_code}"
        log(f"✅ PASS: Wrong password returns 401")
        
        # Test 3: Login as admin with username 'admin'
        log(f"2.3. Login with username 'admin' password 'admin123' -> expect super_admin role")
        resp3 = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        assert resp3.status_code == 200, f"❌ Admin login failed: {resp3.status_code} {resp3.text}"
        admin_data = resp3.json()
        assert "token" in admin_data, "❌ No token in admin response"
        assert admin_data["user"]["role"] == "super_admin", \
            f"❌ Expected role 'super_admin', got '{admin_data['user']['role']}'"
        assert admin_data["user"]["username"] == "admin", \
            f"❌ Expected username 'admin', got '{admin_data['user']['username']}'"
        
        admin_token = admin_data["token"]
        log(f"✅ PASS: Admin login with username 'admin' returns super_admin role")
        
        return admin_token
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_username_auth_me(user_data):
    """Test GET /auth/me returns user with username"""
    log("=" * 80)
    log("TEST 3: USERNAME AUTH - GET /auth/me")
    log("=" * 80)
    
    try:
        log(f"3.1. GET /auth/me with user token")
        headers = {"Authorization": f"Bearer {user_data['user_token']}"}
        resp = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        assert resp.status_code == 200, f"❌ GET /auth/me failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert "user" in data, "❌ No user in response"
        assert "username" in data["user"], "❌ User object missing 'username' field"
        assert data["user"]["username"] == user_data["username"], \
            f"❌ Expected username '{user_data['username']}', got '{data['user']['username']}'"
        log(f"✅ PASS: GET /auth/me returns user with username field: {data['user']['username']}")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_username_forgot_reset_password(user_data):
    """Test forgot/reset password with username"""
    log("=" * 80)
    log("TEST 4: USERNAME AUTH - FORGOT/RESET PASSWORD")
    log("=" * 80)
    
    try:
        # Test 1: Forgot password with existing username
        log(f"4.1. POST /auth/forgot-password with username '{user_data['username']}'")
        resp = requests.post(f"{BASE_URL}/auth/forgot-password", json={
            "username": user_data["username"]
        })
        assert resp.status_code == 200, f"❌ Forgot password failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("ok") == True, "❌ Expected ok=true"
        assert "token" in data, "❌ No token in response"
        assert data["token"] != "", "❌ Token is empty"
        
        reset_token = data["token"]
        log(f"✅ PASS: Forgot password with username returns token: {reset_token[:20]}...")
        
        # Test 2: Forgot password with unknown username
        log(f"4.2. POST /auth/forgot-password with unknown username -> expect 404")
        resp2 = requests.post(f"{BASE_URL}/auth/forgot-password", json={
            "username": "unknownuser999999"
        })
        assert resp2.status_code == 404, f"❌ Expected 404 for unknown username, got {resp2.status_code}"
        log(f"✅ PASS: Unknown username returns 404")
        
        # Test 3: Reset password with token
        log(f"4.3. POST /auth/reset-password with token and new password")
        new_password = "newpass1"
        resp3 = requests.post(f"{BASE_URL}/auth/reset-password", json={
            "token": reset_token,
            "newPassword": new_password
        })
        assert resp3.status_code == 200, f"❌ Reset password failed: {resp3.status_code} {resp3.text}"
        assert resp3.json().get("ok") == True, "❌ Expected ok=true"
        log(f"✅ PASS: Reset password successful")
        
        # Test 4: Login with old password should fail
        log(f"4.4. Login with old password -> expect 401")
        resp4 = requests.post(f"{BASE_URL}/auth/login", json={
            "username": user_data["username"],
            "password": user_data["password"]
        })
        assert resp4.status_code == 401, f"❌ Expected 401 for old password, got {resp4.status_code}"
        log(f"✅ PASS: Old password no longer works (401)")
        
        # Test 5: Login with new password should work
        log(f"4.5. Login with new password -> expect 200")
        resp5 = requests.post(f"{BASE_URL}/auth/login", json={
            "username": user_data["username"],
            "password": new_password
        })
        assert resp5.status_code == 200, f"❌ Login with new password failed: {resp5.status_code} {resp5.text}"
        log(f"✅ PASS: New password works (200)")
        
        # Update user_data with new password and token
        user_data["password"] = new_password
        user_data["user_token"] = resp5.json()["token"]
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_feedback_user(user_data):
    """Test feedback endpoints for normal user"""
    log("=" * 80)
    log("TEST 5: FEEDBACK - USER ENDPOINTS")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {user_data['user_token']}"}
        
        # First, create a member and submit PHQ-9 with item9=1 to create an alert
        log(f"5.0. Setup: Create member and submit PHQ-9 with item9=1 (for alert username check)")
        
        # Create member
        resp_member = requests.post(f"{BASE_URL}/members", headers=headers, json={
            "fullName": "Test Member",
            "gender": "Laki-laki",
            "dob": "1995-01-01",
            "relationship": "Diri Sendiri"
        })
        assert resp_member.status_code == 200, f"❌ Create member failed: {resp_member.text}"
        member = resp_member.json()
        member_id = member["id"]
        log(f"   ✅ Member created: {member_id}")
        
        # Submit PHQ-9 with item9=1
        answers = {str(i): 0 for i in range(1, 10)}
        answers["9"] = 1  # Suicide risk
        resp_assessment = requests.post(f"{BASE_URL}/assessments", headers=headers, json={
            "memberId": member_id,
            "instrumentCode": "phq9",
            "answers": answers
        })
        assert resp_assessment.status_code == 200, f"❌ Submit assessment failed: {resp_assessment.text}"
        assessment = resp_assessment.json()
        assert assessment["result"]["suicideRisk"] == True, "❌ Expected suicideRisk=true"
        log(f"   ✅ PHQ-9 assessment submitted with item9=1 (alert created)")
        
        # Test 1: POST feedback with message, rating, category
        log(f"5.1. POST /feedback with message, rating, category")
        resp = requests.post(f"{BASE_URL}/feedback", headers=headers, json={
            "message": "Aplikasi bagus",
            "rating": 5,
            "category": "Pujian"
        })
        assert resp.status_code == 200, f"❌ POST feedback failed: {resp.status_code} {resp.text}"
        feedback = resp.json()
        assert "id" in feedback, "❌ No id in feedback response"
        assert feedback["message"] == "Aplikasi bagus", f"❌ Expected message 'Aplikasi bagus', got '{feedback['message']}'"
        assert feedback["rating"] == 5, f"❌ Expected rating 5, got {feedback['rating']}"
        assert feedback["category"] == "Pujian", f"❌ Expected category 'Pujian', got '{feedback['category']}'"
        assert feedback["status"] == "Baru", f"❌ Expected status 'Baru', got '{feedback['status']}'"
        assert "username" in feedback, "❌ Feedback missing 'username' field"
        assert feedback["username"] == user_data["username"], \
            f"❌ Expected username '{user_data['username']}', got '{feedback['username']}'"
        
        feedback_id = feedback["id"]
        log(f"✅ PASS: POST feedback returns feedback with status='Baru' and username='{feedback['username']}'")
        
        # Test 2: POST feedback with empty message
        log(f"5.2. POST /feedback with empty message -> expect 400")
        resp2 = requests.post(f"{BASE_URL}/feedback", headers=headers, json={
            "message": "",
            "rating": 3
        })
        assert resp2.status_code == 400, f"❌ Expected 400 for empty message, got {resp2.status_code}"
        log(f"✅ PASS: Empty message returns 400")
        
        # Test 3: GET feedback (should return only user's feedback)
        log(f"5.3. GET /feedback (user token) -> should return only this user's feedback")
        resp3 = requests.get(f"{BASE_URL}/feedback", headers=headers)
        assert resp3.status_code == 200, f"❌ GET feedback failed: {resp3.status_code} {resp3.text}"
        feedbacks = resp3.json()
        assert isinstance(feedbacks, list), "❌ Expected list of feedbacks"
        assert len(feedbacks) >= 1, "❌ Expected at least 1 feedback"
        
        # Check that the feedback we created is in the list
        found = False
        for fb in feedbacks:
            if fb["id"] == feedback_id:
                found = True
                assert fb["userId"] == user_data["user_id"], \
                    f"❌ Expected userId '{user_data['user_id']}', got '{fb['userId']}'"
                break
        assert found, f"❌ Created feedback {feedback_id} not found in user's feedback list"
        log(f"✅ PASS: GET /feedback returns user's feedback (count={len(feedbacks)})")
        
        return feedback_id
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_feedback_admin(admin_token, user_data, feedback_id):
    """Test admin feedback endpoints"""
    log("=" * 80)
    log("TEST 6: FEEDBACK - ADMIN ENDPOINTS")
    log("=" * 80)
    
    try:
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        user_headers = {"Authorization": f"Bearer {user_data['user_token']}"}
        
        # Test 1: GET /admin/feedback (should return all feedback)
        log(f"6.1. GET /admin/feedback (admin token) -> should return all feedback")
        resp = requests.get(f"{BASE_URL}/admin/feedback", headers=admin_headers)
        assert resp.status_code == 200, f"❌ GET admin feedback failed: {resp.status_code} {resp.text}"
        all_feedbacks = resp.json()
        assert isinstance(all_feedbacks, list), "❌ Expected list of feedbacks"
        
        # Check that user's feedback is in the list
        found = False
        for fb in all_feedbacks:
            if fb["id"] == feedback_id:
                found = True
                break
        assert found, f"❌ User's feedback {feedback_id} not found in admin feedback list"
        log(f"✅ PASS: GET /admin/feedback returns all feedback including user's (count={len(all_feedbacks)})")
        
        # Test 2: PATCH /admin/feedback/:id to update status and reply
        log(f"6.2. PATCH /admin/feedback/{feedback_id} with status and reply")
        resp2 = requests.patch(f"{BASE_URL}/admin/feedback/{feedback_id}", headers=admin_headers, json={
            "status": "Ditanggapi",
            "reply": "Terima kasih"
        })
        assert resp2.status_code == 200, f"❌ PATCH feedback failed: {resp2.status_code} {resp2.text}"
        updated_feedback = resp2.json()
        assert updated_feedback["status"] == "Ditanggapi", \
            f"❌ Expected status 'Ditanggapi', got '{updated_feedback['status']}'"
        assert updated_feedback["reply"] == "Terima kasih", \
            f"❌ Expected reply 'Terima kasih', got '{updated_feedback['reply']}'"
        log(f"✅ PASS: PATCH feedback updates status and reply")
        
        # Test 3: GET /feedback as user should show the reply
        log(f"6.3. GET /feedback as user -> should show reply from admin")
        resp3 = requests.get(f"{BASE_URL}/feedback", headers=user_headers)
        assert resp3.status_code == 200, f"❌ GET feedback failed: {resp3.status_code} {resp3.text}"
        user_feedbacks = resp3.json()
        found_with_reply = False
        for fb in user_feedbacks:
            if fb["id"] == feedback_id:
                assert fb["reply"] == "Terima kasih", \
                    f"❌ Expected reply 'Terima kasih', got '{fb['reply']}'"
                found_with_reply = True
                break
        assert found_with_reply, f"❌ Feedback with reply not found"
        log(f"✅ PASS: User can see admin's reply")
        
        # Test 4: Normal user token on GET /admin/feedback should return 403
        log(f"6.4. GET /admin/feedback with normal user token -> expect 403")
        resp4 = requests.get(f"{BASE_URL}/admin/feedback", headers=user_headers)
        assert resp4.status_code == 403, f"❌ Expected 403 for normal user, got {resp4.status_code}"
        log(f"✅ PASS: Normal user gets 403 on admin feedback endpoint")
        
        # Test 5: DELETE /admin/feedback/:id
        log(f"6.5. DELETE /admin/feedback/{feedback_id} (admin)")
        resp5 = requests.delete(f"{BASE_URL}/admin/feedback/{feedback_id}", headers=admin_headers)
        assert resp5.status_code == 200, f"❌ DELETE feedback failed: {resp5.status_code} {resp5.text}"
        assert resp5.json().get("ok") == True, "❌ Expected ok=true"
        log(f"✅ PASS: DELETE feedback successful")
        
        # Verify deletion
        resp6 = requests.get(f"{BASE_URL}/admin/feedback", headers=admin_headers)
        remaining_feedbacks = resp6.json()
        for fb in remaining_feedbacks:
            assert fb["id"] != feedback_id, f"❌ Deleted feedback still exists"
        log(f"✅ PASS: Feedback deleted successfully")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_admin_stats_new_feedback(admin_token):
    """Test that admin stats includes newFeedback count"""
    log("=" * 80)
    log("TEST 7: ADMIN STATS - newFeedback COUNT")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        log(f"7.1. GET /admin/stats -> should include 'newFeedback' field")
        resp = requests.get(f"{BASE_URL}/admin/stats", headers=headers)
        assert resp.status_code == 200, f"❌ GET admin stats failed: {resp.status_code} {resp.text}"
        stats = resp.json()
        
        assert "newFeedback" in stats, "❌ Stats missing 'newFeedback' field"
        assert isinstance(stats["newFeedback"], int), \
            f"❌ Expected newFeedback to be int, got {type(stats['newFeedback'])}"
        
        log(f"✅ PASS: GET /admin/stats includes newFeedback={stats['newFeedback']}")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_alert_username_field(admin_token, user_data):
    """Test that alerts have 'username' field (not userEmail)"""
    log("=" * 80)
    log("TEST 8: ALERT USERNAME FIELD CHECK")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        log(f"8.1. GET /admin/alerts -> check that alerts have 'username' field")
        resp = requests.get(f"{BASE_URL}/admin/alerts", headers=headers)
        assert resp.status_code == 200, f"❌ GET alerts failed: {resp.status_code} {resp.text}"
        alerts = resp.json()
        
        assert isinstance(alerts, list), "❌ Expected list of alerts"
        assert len(alerts) > 0, "❌ Expected at least one alert (from PHQ-9 submission)"
        
        # Find alert for our user
        user_alert = None
        for alert in alerts:
            if alert.get("username") == user_data["username"]:
                user_alert = alert
                break
        
        assert user_alert is not None, \
            f"❌ No alert found for username '{user_data['username']}'"
        
        assert "username" in user_alert, "❌ Alert missing 'username' field"
        assert "userEmail" not in user_alert, "❌ Alert should NOT have 'userEmail' field (replaced by username)"
        assert user_alert["username"] == user_data["username"], \
            f"❌ Expected username '{user_data['username']}', got '{user_alert['username']}'"
        
        log(f"✅ PASS: Alert has 'username' field (not userEmail): username='{user_alert['username']}'")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def main():
    """Run all tests"""
    log("🚀 Starting USERNAME AUTH + FEEDBACK Backend Tests")
    log("")
    
    all_passed = True
    results = []
    
    try:
        # Test 1: Register with username
        user_data = test_username_auth_register()
        results.append("✅ TEST 1: USERNAME AUTH - REGISTER")
    except Exception as e:
        results.append("❌ TEST 1: USERNAME AUTH - REGISTER")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        # Test 2: Login with username
        admin_token = test_username_auth_login(user_data)
        results.append("✅ TEST 2: USERNAME AUTH - LOGIN")
    except Exception as e:
        results.append("❌ TEST 2: USERNAME AUTH - LOGIN")
        all_passed = False
        log(f"ERROR: {str(e)}")
        return 1
    
    try:
        # Test 3: GET /auth/me
        test_username_auth_me(user_data)
        results.append("✅ TEST 3: USERNAME AUTH - GET /auth/me")
    except Exception as e:
        results.append("❌ TEST 3: USERNAME AUTH - GET /auth/me")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        # Test 4: Forgot/reset password
        test_username_forgot_reset_password(user_data)
        results.append("✅ TEST 4: USERNAME AUTH - FORGOT/RESET PASSWORD")
    except Exception as e:
        results.append("❌ TEST 4: USERNAME AUTH - FORGOT/RESET PASSWORD")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        # Test 5: Feedback user endpoints
        feedback_id = test_feedback_user(user_data)
        results.append("✅ TEST 5: FEEDBACK - USER ENDPOINTS")
    except Exception as e:
        results.append("❌ TEST 5: FEEDBACK - USER ENDPOINTS")
        all_passed = False
        log(f"ERROR: {str(e)}")
        return 1
    
    try:
        # Test 6: Feedback admin endpoints
        test_feedback_admin(admin_token, user_data, feedback_id)
        results.append("✅ TEST 6: FEEDBACK - ADMIN ENDPOINTS")
    except Exception as e:
        results.append("❌ TEST 6: FEEDBACK - ADMIN ENDPOINTS")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        # Test 7: Admin stats newFeedback
        test_admin_stats_new_feedback(admin_token)
        results.append("✅ TEST 7: ADMIN STATS - newFeedback COUNT")
    except Exception as e:
        results.append("❌ TEST 7: ADMIN STATS - newFeedback COUNT")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        # Test 8: Alert username field
        test_alert_username_field(admin_token, user_data)
        results.append("✅ TEST 8: ALERT USERNAME FIELD CHECK")
    except Exception as e:
        results.append("❌ TEST 8: ALERT USERNAME FIELD CHECK")
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
        log("✅ Register with username returns user with 'username' field (NOT email)")
        log("✅ Duplicate username returns 400 'Username sudah digunakan'")
        log("✅ Missing username returns 400")
        log("✅ Login with username and password works")
        log("✅ Login with wrong password returns 401")
        log("✅ Admin login with username 'admin' returns super_admin role")
        log("✅ GET /auth/me returns user with username field")
        log("✅ Forgot password with username returns token")
        log("✅ Forgot password with unknown username returns 404")
        log("✅ Reset password works, old password fails, new password works")
        log("✅ POST /feedback returns feedback with status='Baru' and username")
        log("✅ POST /feedback with empty message returns 400")
        log("✅ GET /feedback returns only user's feedback")
        log("✅ GET /admin/feedback returns all feedback")
        log("✅ PATCH /admin/feedback/:id updates status and reply")
        log("✅ User can see admin's reply")
        log("✅ Normal user gets 403 on admin feedback endpoint")
        log("✅ DELETE /admin/feedback/:id works")
        log("✅ GET /admin/stats includes newFeedback count")
        log("✅ Alerts have 'username' field (not userEmail)")
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())
