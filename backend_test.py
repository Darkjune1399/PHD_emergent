#!/usr/bin/env python3
"""
Backend Test Suite for PHD App - UPDATE 8: KELURAHAN/DESA + ADMIN MUDIN
Tests registration with kelurahan field, alert denormalization with kelurahan,
admin_mudin role with scopeKelurahan, kelurahan scoping, and RBAC.
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:3000/api"
SUPER_ADMIN_USERNAME = "admin"
SUPER_ADMIN_PASSWORD = "admin123"

# Test results tracking
tests_passed = 0
tests_failed = 0
test_results = []

def log_test(name, passed, message=""):
    global tests_passed, tests_failed
    if passed:
        tests_passed += 1
        status = "✅ PASS"
    else:
        tests_failed += 1
        status = "❌ FAIL"
    result = f"{status}: {name}"
    if message:
        result += f" - {message}"
    print(result)
    test_results.append({"name": name, "passed": passed, "message": message})

def test_registration_with_kelurahan():
    """Test (A): Registration now REQUIRES kelurahan in addition to kota, kecamatan, alamat"""
    print("\n" + "="*80)
    print("TEST SECTION A: REGISTRATION WITH KELURAHAN FIELD")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    # Test 1: Register with all required fields including kelurahan
    user1_data = {
        "name": "User Antirogo",
        "username": f"user_antirogo_{timestamp}",
        "password": "pass123",
        "kota": "Kabupaten Jember",
        "kecamatan": "Sumbersari",
        "kelurahan": "Antirogo",
        "alamat": "Jl. Test 1"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json=user1_data, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if "token" in data and "user" in data:
                user = data["user"]
                if (user.get("kota") == "Kabupaten Jember" and 
                    user.get("kecamatan") == "Sumbersari" and 
                    user.get("kelurahan") == "Antirogo" and
                    user.get("alamat") == "Jl. Test 1"):
                    log_test("Register with kelurahan field", True, 
                            f"User created with kelurahan={user.get('kelurahan')}")
                    return {"user1": user1_data, "token1": data["token"], "user1_obj": user}
                else:
                    log_test("Register with kelurahan field", False, 
                            f"Address fields incorrect in response: {user}")
                    return None
            else:
                log_test("Register with kelurahan field", False, 
                        f"Missing token or user in response: {data}")
                return None
        else:
            log_test("Register with kelurahan field", False, 
                    f"Status {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        log_test("Register with kelurahan field", False, f"Exception: {e}")
        return None

def test_registration_validation():
    """Test registration validation for missing kelurahan and other address fields"""
    print("\n--- Registration Validation Tests ---")
    
    timestamp = int(datetime.now().timestamp())
    
    # Test: Missing kelurahan
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "username": f"test_{timestamp}_1",
            "password": "pass123",
            "kota": "Kabupaten Jember",
            "kecamatan": "Sumbersari",
            "alamat": "Jl. Test"
        }, timeout=10)
        error_msg = resp.json().get("error", "") if resp.status_code == 400 else ""
        if resp.status_code == 400 and "kelurahan" in error_msg.lower():
            log_test("Register missing kelurahan returns 400", True, error_msg)
        else:
            log_test("Register missing kelurahan returns 400", False, 
                    f"Expected 400 with kelurahan error, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Register missing kelurahan returns 400", False, f"Exception: {e}")
    
    # Test: Missing kota
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "username": f"test_{timestamp}_2",
            "password": "pass123",
            "kecamatan": "Sumbersari",
            "kelurahan": "Antirogo",
            "alamat": "Jl. Test"
        }, timeout=10)
        error_msg = resp.json().get("error", "") if resp.status_code == 400 else ""
        if resp.status_code == 400 and ("kota" in error_msg.lower() or "kelurahan" in error_msg.lower()):
            log_test("Register missing kota returns 400", True, error_msg)
        else:
            log_test("Register missing kota returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Register missing kota returns 400", False, f"Exception: {e}")
    
    # Test: Missing kecamatan
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "username": f"test_{timestamp}_3",
            "password": "pass123",
            "kota": "Kabupaten Jember",
            "kelurahan": "Antirogo",
            "alamat": "Jl. Test"
        }, timeout=10)
        error_msg = resp.json().get("error", "") if resp.status_code == 400 else ""
        if resp.status_code == 400 and ("kecamatan" in error_msg.lower() or "kelurahan" in error_msg.lower()):
            log_test("Register missing kecamatan returns 400", True, error_msg)
        else:
            log_test("Register missing kecamatan returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Register missing kecamatan returns 400", False, f"Exception: {e}")
    
    # Test: Missing alamat
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "username": f"test_{timestamp}_4",
            "password": "pass123",
            "kota": "Kabupaten Jember",
            "kecamatan": "Sumbersari",
            "kelurahan": "Antirogo"
        }, timeout=10)
        error_msg = resp.json().get("error", "") if resp.status_code == 400 else ""
        if resp.status_code == 400 and ("alamat" in error_msg.lower() or "kelurahan" in error_msg.lower()):
            log_test("Register missing alamat returns 400", True, error_msg)
        else:
            log_test("Register missing alamat returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Register missing alamat returns 400", False, f"Exception: {e}")

def test_auth_me_includes_kelurahan(token):
    """Test that GET /auth/me returns kelurahan field"""
    print("\n--- Auth Me Test ---")
    
    try:
        resp = requests.get(f"{BASE_URL}/auth/me", 
                           headers={"Authorization": f"Bearer {token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            user = data.get("user", {})
            if "kelurahan" in user and user.get("kelurahan") == "Antirogo":
                log_test("GET /auth/me includes kelurahan field", True, 
                        f"kelurahan={user.get('kelurahan')}")
            else:
                log_test("GET /auth/me includes kelurahan field", False, 
                        f"Missing or incorrect kelurahan field: {user}")
        else:
            log_test("GET /auth/me includes kelurahan field", False, 
                    f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /auth/me includes kelurahan field", False, f"Exception: {e}")

def test_alert_denormalization_with_kelurahan(user_token, user_kota, user_kecamatan, user_kelurahan):
    """Test (B): Assessment/Alert denormalization includes kelurahan"""
    print("\n" + "="*80)
    print("TEST SECTION B: ASSESSMENT/ALERT DENORMALIZATION WITH KELURAHAN")
    print("="*80)
    
    # Step 1: Add a member (adult for PHQ-9)
    dob = (datetime.now() - timedelta(days=30*365)).strftime("%Y-%m-%d")  # ~30 years old
    member_data = {
        "fullName": "Test Member Adult Antirogo",
        "gender": "Laki-laki",
        "dob": dob,
        "relationship": "Diri Sendiri"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/members", 
                            json=member_data,
                            headers={"Authorization": f"Bearer {user_token}"}, 
                            timeout=10)
        if resp.status_code != 200:
            log_test("Add adult member for alert test", False, 
                    f"Status {resp.status_code}: {resp.text}")
            return None
        
        member = resp.json()
        member_id = member.get("id")
        log_test("Add adult member for alert test", True, f"Member ID: {member_id}")
        
        # Step 2: Submit PHQ-9 assessment with item 9 > 0 (triggers red flag)
        phq9_answers = {str(i): 0 for i in range(1, 10)}
        phq9_answers["9"] = 2  # Suicide risk item
        
        assessment_data = {
            "memberId": member_id,
            "instrumentCode": "phq9",
            "answers": phq9_answers
        }
        
        resp = requests.post(f"{BASE_URL}/assessments", 
                            json=assessment_data,
                            headers={"Authorization": f"Bearer {user_token}"}, 
                            timeout=10)
        if resp.status_code != 200:
            log_test("Submit PHQ-9 with suicide risk", False, 
                    f"Status {resp.status_code}: {resp.text}")
            return None
        
        assessment = resp.json()
        if assessment.get("result", {}).get("suicideRisk") and assessment.get("result", {}).get("redFlag"):
            log_test("Submit PHQ-9 with suicide risk", True, 
                    f"Assessment ID: {assessment.get('id')}, redFlag=True, suicideRisk=True")
        else:
            log_test("Submit PHQ-9 with suicide risk", False, 
                    f"Expected redFlag and suicideRisk to be True: {assessment.get('result')}")
            return None
        
        # Step 3: Login as super_admin and check alert has kota/kecamatan/kelurahan
        admin_resp = requests.post(f"{BASE_URL}/auth/login", 
                                   json={"username": SUPER_ADMIN_USERNAME, "password": SUPER_ADMIN_PASSWORD},
                                   timeout=10)
        if admin_resp.status_code != 200:
            log_test("Admin login for alert check", False, 
                    f"Status {admin_resp.status_code}: {admin_resp.text}")
            return None
        
        admin_token = admin_resp.json().get("token")
        log_test("Admin login for alert check", True)
        
        # Get alerts
        alerts_resp = requests.get(f"{BASE_URL}/admin/alerts", 
                                  headers={"Authorization": f"Bearer {admin_token}"}, 
                                  timeout=10)
        if alerts_resp.status_code != 200:
            log_test("GET /admin/alerts", False, 
                    f"Status {alerts_resp.status_code}: {alerts_resp.text}")
            return None
        
        alerts = alerts_resp.json()
        # Find the alert for our assessment
        our_alert = None
        for alert in alerts:
            if alert.get("assessmentId") == assessment.get("id"):
                our_alert = alert
                break
        
        if our_alert:
            if (our_alert.get("kota") == user_kota and 
                our_alert.get("kecamatan") == user_kecamatan and
                our_alert.get("kelurahan") == user_kelurahan):
                log_test("Alert has denormalized kelurahan", True, 
                        f"Alert kelurahan={our_alert.get('kelurahan')}, kecamatan={our_alert.get('kecamatan')}, kota={our_alert.get('kota')}")
                return admin_token
            else:
                log_test("Alert has denormalized kelurahan", False, 
                        f"Expected kelurahan={user_kelurahan}, kecamatan={user_kecamatan}, kota={user_kota}, got kelurahan={our_alert.get('kelurahan')}, kecamatan={our_alert.get('kecamatan')}, kota={our_alert.get('kota')}")
                return admin_token
        else:
            log_test("Alert has denormalized kelurahan", False, 
                    "Alert not found for assessment")
            return admin_token
            
    except Exception as e:
        log_test("Alert denormalization test", False, f"Exception: {e}")
        return None

def test_admin_mudin_crud(admin_token):
    """Test (C): /admin/admins supports admin_mudin role"""
    print("\n" + "="*80)
    print("TEST SECTION C: ADMIN_MUDIN ROLE + /admin/admins CRUD")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    # Test 1: Create admin_mudin with scopeKelurahan
    admin_mudin_data = {
        "name": "Admin Mudin Test",
        "username": f"admin_mudin_{timestamp}",
        "password": "pass123",
        "role": "admin_mudin",
        "scopeKelurahan": "Antirogo"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json=admin_mudin_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp.status_code == 200:
            admin_mudin = resp.json()
            if (admin_mudin.get("role") == "admin_mudin" and 
                admin_mudin.get("scopeKelurahan") == "Antirogo" and
                "passwordHash" not in admin_mudin):
                log_test("Create admin_mudin with scopeKelurahan", True, 
                        f"Admin ID: {admin_mudin.get('id')}, scopeKelurahan={admin_mudin.get('scopeKelurahan')}")
                admin_mudin_username = admin_mudin.get("username")
                admin_mudin_id = admin_mudin.get("id")
            else:
                log_test("Create admin_mudin with scopeKelurahan", False, 
                        f"Invalid response: {admin_mudin}")
                admin_mudin_username = None
                admin_mudin_id = None
        else:
            log_test("Create admin_mudin with scopeKelurahan", False, 
                    f"Status {resp.status_code}: {resp.text}")
            admin_mudin_username = None
            admin_mudin_id = None
    except Exception as e:
        log_test("Create admin_mudin with scopeKelurahan", False, f"Exception: {e}")
        admin_mudin_username = None
        admin_mudin_id = None
    
    # Test 2: admin_mudin without scopeKelurahan should fail
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json={
                                "name": "Mudin No Scope",
                                "username": f"mudin_noscope_{timestamp}",
                                "password": "pass123",
                                "role": "admin_mudin"
                            },
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        error_msg = resp.json().get("error", "") if resp.status_code == 400 else ""
        if resp.status_code == 400 and "mudin" in error_msg.lower() and "kelurahan" in error_msg.lower():
            log_test("Create admin_mudin without scopeKelurahan returns 400", True, error_msg)
        else:
            log_test("Create admin_mudin without scopeKelurahan returns 400", False, 
                    f"Expected 400 with mudin/kelurahan error, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Create admin_mudin without scopeKelurahan returns 400", False, f"Exception: {e}")
    
    # Test 3: Still supports admin_kua with scopeKecamatan
    admin_kua_data = {
        "name": "Admin KUA Test",
        "username": f"admin_kua_{timestamp}",
        "password": "pass123",
        "role": "admin_kua",
        "scopeKecamatan": "Sumbersari"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json=admin_kua_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp.status_code == 200:
            admin_kua = resp.json()
            if admin_kua.get("role") == "admin_kua" and admin_kua.get("scopeKecamatan") == "Sumbersari":
                log_test("Still supports admin_kua with scopeKecamatan", True, 
                        f"Admin ID: {admin_kua.get('id')}")
                admin_kua_username = admin_kua.get("username")
            else:
                log_test("Still supports admin_kua with scopeKecamatan", False, 
                        f"Invalid response: {admin_kua}")
                admin_kua_username = None
        else:
            log_test("Still supports admin_kua with scopeKecamatan", False, 
                    f"Status {resp.status_code}: {resp.text}")
            admin_kua_username = None
    except Exception as e:
        log_test("Still supports admin_kua with scopeKecamatan", False, f"Exception: {e}")
        admin_kua_username = None
    
    # Test 4: Still supports admin_pa with scopeKota
    admin_pa_data = {
        "name": "Admin PA Test",
        "username": f"admin_pa_{timestamp}",
        "password": "pass123",
        "role": "admin_pa",
        "scopeKota": "Kabupaten Jember"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json=admin_pa_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp.status_code == 200:
            admin_pa = resp.json()
            if admin_pa.get("role") == "admin_pa" and admin_pa.get("scopeKota") == "Kabupaten Jember":
                log_test("Still supports admin_pa with scopeKota", True, 
                        f"Admin ID: {admin_pa.get('id')}")
            else:
                log_test("Still supports admin_pa with scopeKota", False, 
                        f"Invalid response: {admin_pa}")
        else:
            log_test("Still supports admin_pa with scopeKota", False, 
                    f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Still supports admin_pa with scopeKota", False, f"Exception: {e}")
    
    # Test 5: Invalid role should fail
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json={
                                "name": "Invalid Admin",
                                "username": f"invalid_{timestamp}",
                                "password": "pass123",
                                "role": "admin_x"
                            },
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp.status_code == 400:
            log_test("Create admin with invalid role returns 400", True, resp.json().get("error", ""))
        else:
            log_test("Create admin with invalid role returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Create admin with invalid role returns 400", False, f"Exception: {e}")
    
    # Test 6: GET /admin/admins lists admins including admin_mudin
    try:
        resp = requests.get(f"{BASE_URL}/admin/admins", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            admins = resp.json()
            has_mudin = any(a.get("role") == "admin_mudin" for a in admins)
            if has_mudin:
                log_test("GET /admin/admins lists admin_mudin", True, 
                        f"Found {len(admins)} admins including admin_mudin")
            else:
                log_test("GET /admin/admins lists admin_mudin", False, 
                        "admin_mudin not found in list")
        else:
            log_test("GET /admin/admins lists admin_mudin", False, 
                    f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /admin/admins lists admin_mudin", False, f"Exception: {e}")
    
    # Test 7: DELETE admin_mudin
    if admin_mudin_id:
        try:
            resp = requests.delete(f"{BASE_URL}/admin/admins/{admin_mudin_id}", 
                                  headers={"Authorization": f"Bearer {admin_token}"}, 
                                  timeout=10)
            if resp.status_code == 200 and resp.json().get("ok"):
                log_test("DELETE admin_mudin", True, f"Deleted admin ID: {admin_mudin_id}")
            else:
                log_test("DELETE admin_mudin", False, 
                        f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            log_test("DELETE admin_mudin", False, f"Exception: {e}")
    
    return {
        "admin_mudin_username": admin_mudin_username,
        "admin_kua_username": admin_kua_username
    }

def test_kelurahan_scoping(admin_token):
    """Test (D): Kelurahan scoping for admin_mudin"""
    print("\n" + "="*80)
    print("TEST SECTION D: KELURAHAN SCOPING")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    # Step 1: Register 2 users in different kelurahan (same kecamatan)
    user1_data = {
        "name": "User Antirogo",
        "username": f"user_antirogo_scope_{timestamp}",
        "password": "pass123",
        "kota": "Kabupaten Jember",
        "kecamatan": "Sumbersari",
        "kelurahan": "Antirogo",
        "alamat": "Jl. Antirogo 1"
    }
    
    user2_data = {
        "name": "User Kebonsari",
        "username": f"user_kebonsari_{timestamp}",
        "password": "pass123",
        "kota": "Kabupaten Jember",
        "kecamatan": "Sumbersari",
        "kelurahan": "Kebonsari",
        "alamat": "Jl. Kebonsari 1"
    }
    
    try:
        # Register user 1 (Antirogo)
        resp1 = requests.post(f"{BASE_URL}/auth/register", json=user1_data, timeout=10)
        if resp1.status_code != 200:
            log_test("Register user in Antirogo", False, f"Status {resp1.status_code}: {resp1.text}")
            return
        user1_token = resp1.json().get("token")
        log_test("Register user in Antirogo", True, f"Username: {user1_data['username']}")
        
        # Register user 2 (Kebonsari)
        resp2 = requests.post(f"{BASE_URL}/auth/register", json=user2_data, timeout=10)
        if resp2.status_code != 200:
            log_test("Register user in Kebonsari", False, f"Status {resp2.status_code}: {resp2.text}")
            return
        user2_token = resp2.json().get("token")
        log_test("Register user in Kebonsari", True, f"Username: {user2_data['username']}")
        
        # Step 2: Add adult members and submit red-flag assessments for both users
        for user_token, user_name, kelurahan in [
            (user1_token, "User Antirogo", "Antirogo"),
            (user2_token, "User Kebonsari", "Kebonsari")
        ]:
            # Add member
            dob = (datetime.now() - timedelta(days=30*365)).strftime("%Y-%m-%d")
            member_data = {
                "fullName": f"Member {user_name}",
                "gender": "Laki-laki",
                "dob": dob,
                "relationship": "Diri Sendiri"
            }
            resp = requests.post(f"{BASE_URL}/members", json=member_data,
                                headers={"Authorization": f"Bearer {user_token}"}, timeout=10)
            if resp.status_code != 200:
                log_test(f"Add member for {user_name}", False, f"Status {resp.status_code}")
                continue
            member_id = resp.json().get("id")
            log_test(f"Add member for {user_name}", True, f"Member ID: {member_id}")
            
            # Submit PHQ-9 with item 9 > 0
            phq9_answers = {str(i): 0 for i in range(1, 10)}
            phq9_answers["9"] = 2
            assessment_data = {
                "memberId": member_id,
                "instrumentCode": "phq9",
                "answers": phq9_answers
            }
            resp = requests.post(f"{BASE_URL}/assessments", json=assessment_data,
                                headers={"Authorization": f"Bearer {user_token}"}, timeout=10)
            if resp.status_code == 200:
                log_test(f"Submit red-flag assessment for {user_name}", True, 
                        f"Assessment ID: {resp.json().get('id')}")
            else:
                log_test(f"Submit red-flag assessment for {user_name}", False, 
                        f"Status {resp.status_code}")
        
        # Step 3: Create admin_mudin for Antirogo
        admin_mudin_data = {
            "name": "Admin Mudin Antirogo",
            "username": f"admin_mudin_antirogo_{timestamp}",
            "password": "pass123",
            "role": "admin_mudin",
            "scopeKelurahan": "Antirogo"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_mudin_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_mudin for Antirogo", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_mudin for Antirogo", True)
        
        # Step 4: Login as admin_mudin and check scoping
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_mudin_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_mudin", False, f"Status {resp.status_code}")
            return
        admin_mudin_token = resp.json().get("token")
        log_test("Login as admin_mudin", True)
        
        # Check stats scoping - should only count Antirogo assessments
        resp = requests.get(f"{BASE_URL}/admin/stats", 
                           headers={"Authorization": f"Bearer {admin_mudin_token}"}, timeout=10)
        if resp.status_code == 200:
            stats = resp.json()
            if "scope" in stats and stats["scope"].get("scopeKelurahan") == "Antirogo":
                log_test("GET /admin/stats as admin_mudin includes scope with scopeKelurahan", True,
                        f"scope={stats.get('scope')}")
            else:
                log_test("GET /admin/stats as admin_mudin includes scope with scopeKelurahan", False,
                        f"Missing or incorrect scope: {stats.get('scope')}")
            
            # Check regionComparison
            if "regionComparison" in stats:
                log_test("GET /admin/stats as admin_mudin includes regionComparison", True)
            else:
                log_test("GET /admin/stats as admin_mudin includes regionComparison", False)
            
            # Check filters
            if "filters" in stats:
                log_test("GET /admin/stats as admin_mudin includes filters", True)
            else:
                log_test("GET /admin/stats as admin_mudin includes filters", False)
        else:
            log_test("GET /admin/stats as admin_mudin", False, f"Status {resp.status_code}")
        
        # Check alerts scoping - should only show Antirogo alerts
        resp = requests.get(f"{BASE_URL}/admin/alerts", 
                           headers={"Authorization": f"Bearer {admin_mudin_token}"}, timeout=10)
        if resp.status_code == 200:
            alerts = resp.json()
            # All alerts should be from Antirogo
            non_antirogo = [a for a in alerts if a.get("kelurahan") != "Antirogo"]
            if len(non_antirogo) == 0:
                log_test("GET /admin/alerts as admin_mudin scoped to Antirogo", True,
                        f"All {len(alerts)} alerts are from Antirogo (should NOT include Kebonsari)")
            else:
                log_test("GET /admin/alerts as admin_mudin scoped to Antirogo", False,
                        f"Found {len(non_antirogo)} alerts not from Antirogo")
        else:
            log_test("GET /admin/alerts as admin_mudin", False, f"Status {resp.status_code}")
        
        # Step 5: Test super_admin filtering with kelurahan
        # Test with kelurahan filter
        resp = requests.get(f"{BASE_URL}/admin/stats?kelurahan=Antirogo", 
                           headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            stats = resp.json()
            if "filters" in stats and "kelurahanList" in stats["filters"]:
                kelurahan_list = stats["filters"]["kelurahanList"]
                if "Antirogo" in kelurahan_list or "Kebonsari" in kelurahan_list:
                    log_test("GET /admin/stats as super_admin filters.kelurahanList includes Antirogo/Kebonsari", True,
                            f"kelurahanList={kelurahan_list}")
                else:
                    log_test("GET /admin/stats as super_admin filters.kelurahanList includes Antirogo/Kebonsari", False,
                            f"kelurahanList missing expected values: {kelurahan_list}")
            else:
                log_test("GET /admin/stats as super_admin filters.kelurahanList exists", False,
                        "Missing filters.kelurahanList")
            
            # Check regionComparison.byKelurahan
            if "regionComparison" in stats and "byKelurahan" in stats["regionComparison"]:
                by_kelurahan = stats["regionComparison"]["byKelurahan"]
                if isinstance(by_kelurahan, list) and len(by_kelurahan) > 0:
                    log_test("GET /admin/stats as super_admin regionComparison.byKelurahan is non-empty array", True,
                            f"byKelurahan has {len(by_kelurahan)} entries")
                else:
                    log_test("GET /admin/stats as super_admin regionComparison.byKelurahan is non-empty array", False,
                            f"byKelurahan is empty or not array: {by_kelurahan}")
            else:
                log_test("GET /admin/stats as super_admin regionComparison.byKelurahan exists", False,
                        "Missing regionComparison.byKelurahan")
        else:
            log_test("GET /admin/stats as super_admin with kelurahan filter", False, 
                    f"Status {resp.status_code}")
        
        # Test alerts with kelurahan filter
        resp = requests.get(f"{BASE_URL}/admin/alerts?kelurahan=Kebonsari", 
                           headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            alerts = resp.json()
            non_kebonsari = [a for a in alerts if a.get("kelurahan") != "Kebonsari"]
            if len(non_kebonsari) == 0:
                log_test("GET /admin/alerts as super_admin with kelurahan filter", True,
                        f"Filtered to {len(alerts)} Kebonsari alerts only")
            else:
                log_test("GET /admin/alerts as super_admin with kelurahan filter", False,
                        f"Found {len(non_kebonsari)} non-Kebonsari alerts")
        else:
            log_test("GET /admin/alerts as super_admin with kelurahan filter", False,
                    f"Status {resp.status_code}")
        
    except Exception as e:
        log_test("Kelurahan scoping test", False, f"Exception: {e}")

def test_rbac_admin_mudin():
    """Test (E): RBAC for admin_mudin"""
    print("\n" + "="*80)
    print("TEST SECTION E: RBAC FOR ADMIN_MUDIN")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    try:
        # Login as super_admin
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": SUPER_ADMIN_USERNAME, "password": SUPER_ADMIN_PASSWORD},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as super_admin for RBAC test", False, f"Status {resp.status_code}")
            return
        admin_token = resp.json().get("token")
        
        # Create admin_mudin
        admin_mudin_data = {
            "name": "Admin Mudin RBAC Test",
            "username": f"admin_mudin_rbac_{timestamp}",
            "password": "pass123",
            "role": "admin_mudin",
            "scopeKelurahan": "Test Kelurahan"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_mudin_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_mudin for RBAC test", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_mudin for RBAC test", True)
        
        # Login as admin_mudin
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_mudin_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_mudin for RBAC test", False, f"Status {resp.status_code}")
            return
        admin_mudin_token = resp.json().get("token")
        log_test("Login as admin_mudin for RBAC test", True)
        
        # Test allowed routes for admin_mudin (should return 200)
        allowed_routes = [
            ("GET", "/admin/stats", "GET /admin/stats"),
            ("GET", "/admin/alerts", "GET /admin/alerts")
        ]
        
        for method, route, name in allowed_routes:
            try:
                if method == "GET":
                    resp = requests.get(f"{BASE_URL}{route}", 
                                       headers={"Authorization": f"Bearer {admin_mudin_token}"}, 
                                       timeout=10)
                if resp.status_code == 200:
                    log_test(f"admin_mudin {name} returns 200", True)
                else:
                    log_test(f"admin_mudin {name} returns 200", False,
                            f"Expected 200, got {resp.status_code}: {resp.text}")
            except Exception as e:
                log_test(f"admin_mudin {name} returns 200", False, f"Exception: {e}")
        
        # Test forbidden routes for admin_mudin (should return 403)
        forbidden_routes = [
            ("GET", "/admin/users", "GET /admin/users"),
            ("GET", "/admin/admins", "GET /admin/admins"),
            ("GET", "/admin/instruments", "GET /admin/instruments")
        ]
        
        for method, route, name in forbidden_routes:
            try:
                if method == "GET":
                    resp = requests.get(f"{BASE_URL}{route}", 
                                       headers={"Authorization": f"Bearer {admin_mudin_token}"}, 
                                       timeout=10)
                if resp.status_code == 403:
                    log_test(f"admin_mudin {name} returns 403", True, resp.json().get("error", ""))
                else:
                    log_test(f"admin_mudin {name} returns 403", False,
                            f"Expected 403, got {resp.status_code}: {resp.text}")
            except Exception as e:
                log_test(f"admin_mudin {name} returns 403", False, f"Exception: {e}")
        
    except Exception as e:
        log_test("RBAC admin_mudin test", False, f"Exception: {e}")

def test_regression_admin_kua_scoping():
    """Regression test: admin_kua scoping by kecamatan still works"""
    print("\n" + "="*80)
    print("REGRESSION TEST: ADMIN_KUA SCOPING (BY KECAMATAN)")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    try:
        # Login as super_admin
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": SUPER_ADMIN_USERNAME, "password": SUPER_ADMIN_PASSWORD},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as super_admin for admin_kua regression", False, f"Status {resp.status_code}")
            return
        admin_token = resp.json().get("token")
        
        # Create admin_kua
        admin_kua_data = {
            "name": "Admin KUA Regression",
            "username": f"admin_kua_regr_{timestamp}",
            "password": "pass123",
            "role": "admin_kua",
            "scopeKecamatan": "Sumbersari"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_kua_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_kua for regression test", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_kua for regression test", True)
        
        # Login as admin_kua
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_kua_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_kua for regression", False, f"Status {resp.status_code}")
            return
        admin_kua_token = resp.json().get("token")
        log_test("Login as admin_kua for regression", True)
        
        # Check stats scoping
        resp = requests.get(f"{BASE_URL}/admin/stats", 
                           headers={"Authorization": f"Bearer {admin_kua_token}"}, timeout=10)
        if resp.status_code == 200:
            stats = resp.json()
            if "scope" in stats and stats["scope"].get("scopeKecamatan") == "Sumbersari":
                log_test("admin_kua scoping by kecamatan still works", True,
                        f"scope={stats.get('scope')}")
            else:
                log_test("admin_kua scoping by kecamatan still works", False,
                        f"Missing or incorrect scope: {stats.get('scope')}")
        else:
            log_test("admin_kua scoping by kecamatan", False, f"Status {resp.status_code}")
        
    except Exception as e:
        log_test("admin_kua regression test", False, f"Exception: {e}")

def test_regression_admin_pa_scoping():
    """Regression test: admin_pa scoping by kota still works"""
    print("\n" + "="*80)
    print("REGRESSION TEST: ADMIN_PA SCOPING (BY KOTA)")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    try:
        # Login as super_admin
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": SUPER_ADMIN_USERNAME, "password": SUPER_ADMIN_PASSWORD},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as super_admin for admin_pa regression", False, f"Status {resp.status_code}")
            return
        admin_token = resp.json().get("token")
        
        # Create admin_pa
        admin_pa_data = {
            "name": "Admin PA Regression",
            "username": f"admin_pa_regr_{timestamp}",
            "password": "pass123",
            "role": "admin_pa",
            "scopeKota": "Kabupaten Jember"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_pa_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_pa for regression test", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_pa for regression test", True)
        
        # Login as admin_pa
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_pa_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_pa for regression", False, f"Status {resp.status_code}")
            return
        admin_pa_token = resp.json().get("token")
        log_test("Login as admin_pa for regression", True)
        
        # Check stats scoping
        resp = requests.get(f"{BASE_URL}/admin/stats", 
                           headers={"Authorization": f"Bearer {admin_pa_token}"}, timeout=10)
        if resp.status_code == 200:
            stats = resp.json()
            if "scope" in stats and stats["scope"].get("scopeKota") == "Kabupaten Jember":
                log_test("admin_pa scoping by kota still works", True,
                        f"scope={stats.get('scope')}")
            else:
                log_test("admin_pa scoping by kota still works", False,
                        f"Missing or incorrect scope: {stats.get('scope')}")
        else:
            log_test("admin_pa scoping by kota", False, f"Status {resp.status_code}")
        
    except Exception as e:
        log_test("admin_pa regression test", False, f"Exception: {e}")

def test_sdq_regression():
    """Regression test: SDQ scoring still accurate (all answers=0 -> E=0,C=2,H=4,P=4,Pr=0,Total=10)"""
    print("\n" + "="*80)
    print("REGRESSION TEST: SDQ SCORING ACCURACY")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    try:
        # Register a user
        user_data = {
            "name": "SDQ Test User",
            "username": f"sdq_test_{timestamp}",
            "password": "pass123",
            "kota": "Test Kota",
            "kecamatan": "Test Kec",
            "kelurahan": "Test Kel",
            "alamat": "Test Alamat"
        }
        resp = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
        if resp.status_code != 200:
            log_test("Register user for SDQ test", False, f"Status {resp.status_code}")
            return
        user_token = resp.json().get("token")
        log_test("Register user for SDQ test", True)
        
        # Add a child member (age ~6)
        dob = (datetime.now() - timedelta(days=6*365)).strftime("%Y-%m-%d")
        member_data = {
            "fullName": "Child SDQ Test",
            "gender": "Laki-laki",
            "dob": dob,
            "relationship": "Anak"
        }
        resp = requests.post(f"{BASE_URL}/members", json=member_data,
                            headers={"Authorization": f"Bearer {user_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Add child member for SDQ test", False, f"Status {resp.status_code}")
            return
        member_id = resp.json().get("id")
        log_test("Add child member for SDQ test", True, f"Member ID: {member_id}")
        
        # Submit SDQ with all answers = 0
        sdq_answers = {str(i): 0 for i in range(1, 26)}
        assessment_data = {
            "memberId": member_id,
            "instrumentCode": "sdq_parent",
            "answers": sdq_answers
        }
        resp = requests.post(f"{BASE_URL}/assessments", json=assessment_data,
                            headers={"Authorization": f"Bearer {user_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Submit SDQ with all answers=0", False, f"Status {resp.status_code}")
            return
        
        assessment = resp.json()
        result = assessment.get("result", {})
        subscales = result.get("subscales", {})
        
        # Expected: E=0, C=2, H=4, P=4, Pr=0, Total=10
        expected = {"E": 0, "C": 2, "H": 4, "P": 4, "Pr": 0}
        expected_total = 10
        
        all_correct = True
        for key, expected_val in expected.items():
            actual_val = subscales.get(key)
            if actual_val != expected_val:
                all_correct = False
                log_test(f"SDQ subscale {key} score", False, 
                        f"Expected {expected_val}, got {actual_val}")
        
        actual_total = result.get("totalDifficulties")
        if actual_total != expected_total:
            all_correct = False
            log_test("SDQ Total Difficulties score", False,
                    f"Expected {expected_total}, got {actual_total}")
        
        if all_correct and actual_total == expected_total:
            log_test("SDQ scoring regression test", True, 
                    "All scores match expected values (E=0,C=2,H=4,P=4,Pr=0,Total=10)")
        else:
            log_test("SDQ scoring regression test", False, 
                    "Some scores do not match expected values")
        
    except Exception as e:
        log_test("SDQ scoring regression test", False, f"Exception: {e}")

def main():
    print("="*80)
    print("PHD BACKEND TEST SUITE - UPDATE 8: KELURAHAN/DESA + ADMIN MUDIN")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Super Admin: {SUPER_ADMIN_USERNAME} / {SUPER_ADMIN_PASSWORD}")
    print("="*80)
    
    # Section A: Registration with kelurahan field
    user_data = test_registration_with_kelurahan()
    if user_data:
        test_registration_validation()
        test_auth_me_includes_kelurahan(user_data["token1"])
        
        # Section B: Alert denormalization with kelurahan
        admin_token = test_alert_denormalization_with_kelurahan(
            user_data["token1"], 
            user_data["user1"]["kota"], 
            user_data["user1"]["kecamatan"],
            user_data["user1"]["kelurahan"]
        )
        
        if admin_token:
            # Section C: Admin mudin CRUD
            test_admin_mudin_crud(admin_token)
            
            # Section D: Kelurahan scoping
            test_kelurahan_scoping(admin_token)
    
    # Section E: RBAC for admin_mudin
    test_rbac_admin_mudin()
    
    # Regression tests
    test_regression_admin_kua_scoping()
    test_regression_admin_pa_scoping()
    test_sdq_regression()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    if tests_passed + tests_failed > 0:
        print(f"Success Rate: {tests_passed / (tests_passed + tests_failed) * 100:.1f}%")
    print("="*80)
    
    # Exit with appropriate code
    sys.exit(0 if tests_failed == 0 else 1)

if __name__ == "__main__":
    main()
