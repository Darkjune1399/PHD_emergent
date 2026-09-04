#!/usr/bin/env python3
"""
Backend Test Suite for PHD App - UPDATE 7: Address Fields + Regional Admin Roles
Tests registration with address fields, alert denormalization, regional admin roles,
data scoping, and RBAC.
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

def test_registration_with_address_fields():
    """Test (A): Registration with required address fields"""
    print("\n" + "="*80)
    print("TEST SECTION A: REGISTRATION WITH ADDRESS FIELDS")
    print("="*80)
    
    # Test 1: Register with all required fields including address
    timestamp = int(datetime.now().timestamp())
    user1_data = {
        "name": "User Semarang",
        "username": f"user_semarang_{timestamp}",
        "password": "pass123",
        "kota": "Kota Semarang",
        "kecamatan": "Tembalang",
        "alamat": "Jl. Test No. 123"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json=user1_data, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            if "token" in data and "user" in data:
                user = data["user"]
                if (user.get("kota") == "Kota Semarang" and 
                    user.get("kecamatan") == "Tembalang" and 
                    user.get("alamat") == "Jl. Test No. 123"):
                    log_test("Register with address fields", True, 
                            f"User created with kota={user.get('kota')}, kecamatan={user.get('kecamatan')}")
                    return {"user1": user1_data, "token1": data["token"], "user1_obj": user}
                else:
                    log_test("Register with address fields", False, 
                            f"Address fields missing in response: {user}")
                    return None
            else:
                log_test("Register with address fields", False, 
                        f"Missing token or user in response: {data}")
                return None
        else:
            log_test("Register with address fields", False, 
                    f"Status {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        log_test("Register with address fields", False, f"Exception: {e}")
        return None

def test_registration_validation():
    """Test registration validation for missing address fields"""
    print("\n--- Registration Validation Tests ---")
    
    timestamp = int(datetime.now().timestamp())
    
    # Test: Missing kota
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "username": f"test_{timestamp}_1",
            "password": "pass123",
            "kecamatan": "Tembalang",
            "alamat": "Jl. Test"
        }, timeout=10)
        if resp.status_code == 400 and "kota" in resp.text.lower():
            log_test("Register missing kota returns 400", True, resp.json().get("error", ""))
        else:
            log_test("Register missing kota returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Register missing kota returns 400", False, f"Exception: {e}")
    
    # Test: Missing kecamatan
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "username": f"test_{timestamp}_2",
            "password": "pass123",
            "kota": "Kota Semarang",
            "alamat": "Jl. Test"
        }, timeout=10)
        if resp.status_code == 400 and "kecamatan" in resp.text.lower():
            log_test("Register missing kecamatan returns 400", True, resp.json().get("error", ""))
        else:
            log_test("Register missing kecamatan returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Register missing kecamatan returns 400", False, f"Exception: {e}")
    
    # Test: Missing alamat
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "username": f"test_{timestamp}_3",
            "password": "pass123",
            "kota": "Kota Semarang",
            "kecamatan": "Tembalang"
        }, timeout=10)
        if resp.status_code == 400 and "alamat" in resp.text.lower():
            log_test("Register missing alamat returns 400", True, resp.json().get("error", ""))
        else:
            log_test("Register missing alamat returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Register missing alamat returns 400", False, f"Exception: {e}")
    
    # Test: Duplicate username
    try:
        resp = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Test User",
            "username": SUPER_ADMIN_USERNAME,  # admin already exists
            "password": "pass123",
            "kota": "Kota Semarang",
            "kecamatan": "Tembalang",
            "alamat": "Jl. Test"
        }, timeout=10)
        if resp.status_code == 400 and "username" in resp.text.lower():
            log_test("Register duplicate username returns 400", True, resp.json().get("error", ""))
        else:
            log_test("Register duplicate username returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Register duplicate username returns 400", False, f"Exception: {e}")

def test_auth_me_includes_address(token):
    """Test that GET /auth/me returns address fields"""
    print("\n--- Auth Me Test ---")
    
    try:
        resp = requests.get(f"{BASE_URL}/auth/me", 
                           headers={"Authorization": f"Bearer {token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            user = data.get("user", {})
            if "kota" in user and "kecamatan" in user and "alamat" in user:
                log_test("GET /auth/me includes address fields", True, 
                        f"kota={user.get('kota')}, kecamatan={user.get('kecamatan')}")
            else:
                log_test("GET /auth/me includes address fields", False, 
                        f"Missing address fields: {user}")
        else:
            log_test("GET /auth/me includes address fields", False, 
                    f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /auth/me includes address fields", False, f"Exception: {e}")

def test_alert_denormalization(user_token, user_kota, user_kecamatan):
    """Test (B): Assessment/Alert denormalization with kota/kecamatan"""
    print("\n" + "="*80)
    print("TEST SECTION B: ASSESSMENT/ALERT DENORMALIZATION")
    print("="*80)
    
    # Step 1: Add a member (adult for PHQ-9)
    dob = (datetime.now() - timedelta(days=30*365)).strftime("%Y-%m-%d")  # ~30 years old
    member_data = {
        "fullName": "Test Member Adult",
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
        
        # Step 3: Login as super_admin and check alert has kota/kecamatan
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
            if our_alert.get("kota") == user_kota and our_alert.get("kecamatan") == user_kecamatan:
                log_test("Alert has denormalized kota/kecamatan", True, 
                        f"Alert kota={our_alert.get('kota')}, kecamatan={our_alert.get('kecamatan')}")
                return admin_token
            else:
                log_test("Alert has denormalized kota/kecamatan", False, 
                        f"Expected kota={user_kota}, kecamatan={user_kecamatan}, got kota={our_alert.get('kota')}, kecamatan={our_alert.get('kecamatan')}")
                return admin_token
        else:
            log_test("Alert has denormalized kota/kecamatan", False, 
                    "Alert not found for assessment")
            return admin_token
            
    except Exception as e:
        log_test("Alert denormalization test", False, f"Exception: {e}")
        return None

def test_regional_admin_crud(admin_token):
    """Test (C): Regional admin roles + /admin/admins CRUD"""
    print("\n" + "="*80)
    print("TEST SECTION C: REGIONAL ADMIN ROLES + /admin/admins CRUD")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    # Test 1: Create admin_kua with scopeKecamatan
    admin_kua_data = {
        "name": "Admin KUA Test",
        "username": f"admin_kua_{timestamp}",
        "password": "pass123",
        "role": "admin_kua",
        "scopeKecamatan": "Tembalang"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json=admin_kua_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp.status_code == 200:
            admin_kua = resp.json()
            if (admin_kua.get("role") == "admin_kua" and 
                admin_kua.get("scopeKecamatan") == "Tembalang" and
                "passwordHash" not in admin_kua):
                log_test("Create admin_kua with scopeKecamatan", True, 
                        f"Admin ID: {admin_kua.get('id')}, scopeKecamatan={admin_kua.get('scopeKecamatan')}")
                admin_kua_id = admin_kua.get("id")
                admin_kua_username = admin_kua.get("username")
            else:
                log_test("Create admin_kua with scopeKecamatan", False, 
                        f"Invalid response: {admin_kua}")
                admin_kua_id = None
                admin_kua_username = None
        else:
            log_test("Create admin_kua with scopeKecamatan", False, 
                    f"Status {resp.status_code}: {resp.text}")
            admin_kua_id = None
            admin_kua_username = None
    except Exception as e:
        log_test("Create admin_kua with scopeKecamatan", False, f"Exception: {e}")
        admin_kua_id = None
        admin_kua_username = None
    
    # Test 2: Create admin_pa with scopeKota
    admin_pa_data = {
        "name": "Admin PA Test",
        "username": f"admin_pa_{timestamp}",
        "password": "pass123",
        "role": "admin_pa",
        "scopeKota": "Kota Semarang"
    }
    
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json=admin_pa_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp.status_code == 200:
            admin_pa = resp.json()
            if (admin_pa.get("role") == "admin_pa" and 
                admin_pa.get("scopeKota") == "Kota Semarang" and
                "passwordHash" not in admin_pa):
                log_test("Create admin_pa with scopeKota", True, 
                        f"Admin ID: {admin_pa.get('id')}, scopeKota={admin_pa.get('scopeKota')}")
                admin_pa_id = admin_pa.get("id")
                admin_pa_username = admin_pa.get("username")
            else:
                log_test("Create admin_pa with scopeKota", False, 
                        f"Invalid response: {admin_pa}")
                admin_pa_id = None
                admin_pa_username = None
        else:
            log_test("Create admin_pa with scopeKota", False, 
                    f"Status {resp.status_code}: {resp.text}")
            admin_pa_id = None
            admin_pa_username = None
    except Exception as e:
        log_test("Create admin_pa with scopeKota", False, f"Exception: {e}")
        admin_pa_id = None
        admin_pa_username = None
    
    # Test 3: Invalid role
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json={
                                "name": "Invalid Admin",
                                "username": f"invalid_{timestamp}",
                                "password": "pass123",
                                "role": "admin_medis"
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
    
    # Test 4: admin_kua without scopeKecamatan
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json={
                                "name": "KUA No Scope",
                                "username": f"kua_noscope_{timestamp}",
                                "password": "pass123",
                                "role": "admin_kua"
                            },
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp.status_code == 400 and "kecamatan" in resp.text.lower():
            log_test("Create admin_kua without scopeKecamatan returns 400", True, resp.json().get("error", ""))
        else:
            log_test("Create admin_kua without scopeKecamatan returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Create admin_kua without scopeKecamatan returns 400", False, f"Exception: {e}")
    
    # Test 5: admin_pa without scopeKota
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json={
                                "name": "PA No Scope",
                                "username": f"pa_noscope_{timestamp}",
                                "password": "pass123",
                                "role": "admin_pa"
                            },
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp.status_code == 400 and "kota" in resp.text.lower():
            log_test("Create admin_pa without scopeKota returns 400", True, resp.json().get("error", ""))
        else:
            log_test("Create admin_pa without scopeKota returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Create admin_pa without scopeKota returns 400", False, f"Exception: {e}")
    
    # Test 6: Duplicate username
    try:
        resp = requests.post(f"{BASE_URL}/admin/admins", 
                            json={
                                "name": "Duplicate Admin",
                                "username": SUPER_ADMIN_USERNAME,
                                "password": "pass123",
                                "role": "admin_kua",
                                "scopeKecamatan": "Test"
                            },
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp.status_code == 400 and "username" in resp.text.lower():
            log_test("Create admin with duplicate username returns 400", True, resp.json().get("error", ""))
        else:
            log_test("Create admin with duplicate username returns 400", False, 
                    f"Expected 400, got {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("Create admin with duplicate username returns 400", False, f"Exception: {e}")
    
    # Test 7: GET /admin/admins lists admins
    try:
        resp = requests.get(f"{BASE_URL}/admin/admins", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            admins = resp.json()
            has_super_admin = any(a.get("role") == "super_admin" for a in admins)
            has_kua = any(a.get("role") == "admin_kua" for a in admins)
            has_pa = any(a.get("role") == "admin_pa" for a in admins)
            if has_super_admin and has_kua and has_pa:
                log_test("GET /admin/admins lists all admin types", True, 
                        f"Found {len(admins)} admins including super_admin, admin_kua, admin_pa")
            else:
                log_test("GET /admin/admins lists all admin types", False, 
                        f"Missing admin types: super_admin={has_super_admin}, admin_kua={has_kua}, admin_pa={has_pa}")
        else:
            log_test("GET /admin/admins lists all admin types", False, 
                    f"Status {resp.status_code}: {resp.text}")
    except Exception as e:
        log_test("GET /admin/admins lists all admin types", False, f"Exception: {e}")
    
    # Test 8: DELETE scoped admin
    if admin_kua_id:
        try:
            resp = requests.delete(f"{BASE_URL}/admin/admins/{admin_kua_id}", 
                                  headers={"Authorization": f"Bearer {admin_token}"}, 
                                  timeout=10)
            if resp.status_code == 200 and resp.json().get("ok"):
                log_test("DELETE scoped admin (admin_kua)", True, f"Deleted admin ID: {admin_kua_id}")
            else:
                log_test("DELETE scoped admin (admin_kua)", False, 
                        f"Status {resp.status_code}: {resp.text}")
        except Exception as e:
            log_test("DELETE scoped admin (admin_kua)", False, f"Exception: {e}")
    
    # Test 9: Attempt to DELETE super_admin (should fail)
    try:
        # First get super_admin ID
        resp = requests.get(f"{BASE_URL}/admin/admins", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            admins = resp.json()
            super_admin = next((a for a in admins if a.get("role") == "super_admin"), None)
            if super_admin:
                super_admin_id = super_admin.get("id")
                resp = requests.delete(f"{BASE_URL}/admin/admins/{super_admin_id}", 
                                      headers={"Authorization": f"Bearer {admin_token}"}, 
                                      timeout=10)
                if resp.status_code == 400:
                    log_test("DELETE super_admin returns 400", True, resp.json().get("error", ""))
                else:
                    log_test("DELETE super_admin returns 400", False, 
                            f"Expected 400, got {resp.status_code}: {resp.text}")
            else:
                log_test("DELETE super_admin returns 400", False, "Super admin not found")
        else:
            log_test("DELETE super_admin returns 400", False, "Could not get admin list")
    except Exception as e:
        log_test("DELETE super_admin returns 400", False, f"Exception: {e}")
    
    return {
        "admin_pa_username": admin_pa_username,
        "admin_pa_password": "pass123"
    }

def test_data_scoping(admin_token):
    """Test (D): Data scoping for admin_kua and admin_pa"""
    print("\n" + "="*80)
    print("TEST SECTION D: DATA SCOPING")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    # Step 1: Register 2 users in different regions
    user1_data = {
        "name": "User Tembalang",
        "username": f"user_tembalang_{timestamp}",
        "password": "pass123",
        "kota": "Kota Semarang",
        "kecamatan": "Tembalang",
        "alamat": "Jl. Tembalang 1"
    }
    
    user2_data = {
        "name": "User Jebres",
        "username": f"user_jebres_{timestamp}",
        "password": "pass123",
        "kota": "Kota Solo",
        "kecamatan": "Jebres",
        "alamat": "Jl. Jebres 1"
    }
    
    try:
        # Register user 1
        resp1 = requests.post(f"{BASE_URL}/auth/register", json=user1_data, timeout=10)
        if resp1.status_code != 200:
            log_test("Register user in Tembalang", False, f"Status {resp1.status_code}: {resp1.text}")
            return
        user1_token = resp1.json().get("token")
        log_test("Register user in Tembalang", True, f"Username: {user1_data['username']}")
        
        # Register user 2
        resp2 = requests.post(f"{BASE_URL}/auth/register", json=user2_data, timeout=10)
        if resp2.status_code != 200:
            log_test("Register user in Jebres", False, f"Status {resp2.status_code}: {resp2.text}")
            return
        user2_token = resp2.json().get("token")
        log_test("Register user in Jebres", True, f"Username: {user2_data['username']}")
        
        # Step 2: Add adult members and submit red-flag assessments for both users
        for user_token, user_name, user_kota, user_kec in [
            (user1_token, "User Tembalang", "Kota Semarang", "Tembalang"),
            (user2_token, "User Jebres", "Kota Solo", "Jebres")
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
        
        # Step 3: Create scoped admins
        admin_kua_data = {
            "name": "Admin KUA Tembalang",
            "username": f"admin_kua_tembalang_{timestamp}",
            "password": "pass123",
            "role": "admin_kua",
            "scopeKecamatan": "Tembalang"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_kua_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_kua for Tembalang", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_kua for Tembalang", True)
        
        admin_pa_data = {
            "name": "Admin PA Semarang",
            "username": f"admin_pa_semarang_{timestamp}",
            "password": "pass123",
            "role": "admin_pa",
            "scopeKota": "Kota Semarang"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_pa_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_pa for Kota Semarang", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_pa for Kota Semarang", True)
        
        # Step 4: Login as admin_kua and check scoping
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_kua_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_kua", False, f"Status {resp.status_code}")
            return
        admin_kua_token = resp.json().get("token")
        log_test("Login as admin_kua", True)
        
        # Check stats scoping
        resp = requests.get(f"{BASE_URL}/admin/stats", 
                           headers={"Authorization": f"Bearer {admin_kua_token}"}, timeout=10)
        if resp.status_code == 200:
            stats = resp.json()
            if "scope" in stats and "regionComparison" in stats and "filters" in stats:
                log_test("GET /admin/stats as admin_kua includes scope/regionComparison/filters", True,
                        f"scope={stats.get('scope')}")
                # Note: We can't easily verify the count is correct without knowing existing data
            else:
                log_test("GET /admin/stats as admin_kua includes scope/regionComparison/filters", False,
                        f"Missing fields in response")
        else:
            log_test("GET /admin/stats as admin_kua", False, f"Status {resp.status_code}")
        
        # Check alerts scoping
        resp = requests.get(f"{BASE_URL}/admin/alerts", 
                           headers={"Authorization": f"Bearer {admin_kua_token}"}, timeout=10)
        if resp.status_code == 200:
            alerts = resp.json()
            # All alerts should be from Tembalang
            non_tembalang = [a for a in alerts if a.get("kecamatan") != "Tembalang"]
            if len(non_tembalang) == 0:
                log_test("GET /admin/alerts as admin_kua scoped to Tembalang", True,
                        f"All {len(alerts)} alerts are from Tembalang")
            else:
                log_test("GET /admin/alerts as admin_kua scoped to Tembalang", False,
                        f"Found {len(non_tembalang)} alerts not from Tembalang")
        else:
            log_test("GET /admin/alerts as admin_kua", False, f"Status {resp.status_code}")
        
        # Step 5: Login as admin_pa and check scoping
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_pa_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_pa", False, f"Status {resp.status_code}")
            return
        admin_pa_token = resp.json().get("token")
        log_test("Login as admin_pa", True)
        
        # Check stats scoping
        resp = requests.get(f"{BASE_URL}/admin/stats", 
                           headers={"Authorization": f"Bearer {admin_pa_token}"}, timeout=10)
        if resp.status_code == 200:
            stats = resp.json()
            if "scope" in stats:
                log_test("GET /admin/stats as admin_pa includes scope", True,
                        f"scope={stats.get('scope')}")
            else:
                log_test("GET /admin/stats as admin_pa includes scope", False)
        else:
            log_test("GET /admin/stats as admin_pa", False, f"Status {resp.status_code}")
        
        # Check alerts scoping
        resp = requests.get(f"{BASE_URL}/admin/alerts", 
                           headers={"Authorization": f"Bearer {admin_pa_token}"}, timeout=10)
        if resp.status_code == 200:
            alerts = resp.json()
            # All alerts should be from Kota Semarang
            non_semarang = [a for a in alerts if a.get("kota") != "Kota Semarang"]
            if len(non_semarang) == 0:
                log_test("GET /admin/alerts as admin_pa scoped to Kota Semarang", True,
                        f"All {len(alerts)} alerts are from Kota Semarang")
            else:
                log_test("GET /admin/alerts as admin_pa scoped to Kota Semarang", False,
                        f"Found {len(non_semarang)} alerts not from Kota Semarang")
        else:
            log_test("GET /admin/alerts as admin_pa", False, f"Status {resp.status_code}")
        
        # Step 6: Test super_admin filtering
        # Test with kota filter
        resp = requests.get(f"{BASE_URL}/admin/stats?kota=Kota%20Solo", 
                           headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            stats = resp.json()
            if "filters" in stats and "kotaList" in stats["filters"]:
                kota_list = stats["filters"]["kotaList"]
                if "Kota Semarang" in kota_list or "Kota Solo" in kota_list:
                    log_test("GET /admin/stats as super_admin with kota filter includes kotaList", True,
                            f"kotaList={kota_list}")
                else:
                    log_test("GET /admin/stats as super_admin with kota filter includes kotaList", False,
                            f"kotaList missing expected values: {kota_list}")
            else:
                log_test("GET /admin/stats as super_admin with kota filter includes kotaList", False,
                        "Missing filters.kotaList")
        else:
            log_test("GET /admin/stats as super_admin with kota filter", False, 
                    f"Status {resp.status_code}")
        
        # Test alerts with kecamatan filter
        resp = requests.get(f"{BASE_URL}/admin/alerts?kecamatan=Jebres", 
                           headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code == 200:
            alerts = resp.json()
            non_jebres = [a for a in alerts if a.get("kecamatan") != "Jebres"]
            if len(non_jebres) == 0:
                log_test("GET /admin/alerts as super_admin with kecamatan filter", True,
                        f"Filtered to {len(alerts)} Jebres alerts")
            else:
                log_test("GET /admin/alerts as super_admin with kecamatan filter", False,
                        f"Found {len(non_jebres)} non-Jebres alerts")
        else:
            log_test("GET /admin/alerts as super_admin with kecamatan filter", False,
                    f"Status {resp.status_code}")
        
    except Exception as e:
        log_test("Data scoping test", False, f"Exception: {e}")

def test_rbac():
    """Test (E): RBAC for scoped admins and normal users"""
    print("\n" + "="*80)
    print("TEST SECTION E: RBAC")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    # Create a scoped admin for testing
    try:
        # Login as super_admin
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": SUPER_ADMIN_USERNAME, "password": SUPER_ADMIN_PASSWORD},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as super_admin for RBAC test", False, f"Status {resp.status_code}")
            return
        admin_token = resp.json().get("token")
        
        # Create admin_kua
        admin_kua_data = {
            "name": "Admin KUA RBAC Test",
            "username": f"admin_kua_rbac_{timestamp}",
            "password": "pass123",
            "role": "admin_kua",
            "scopeKecamatan": "Test Kec"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_kua_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_kua for RBAC test", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_kua for RBAC test", True)
        
        # Login as admin_kua
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_kua_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_kua for RBAC test", False, f"Status {resp.status_code}")
            return
        admin_kua_token = resp.json().get("token")
        log_test("Login as admin_kua for RBAC test", True)
        
        # Test forbidden routes for scoped admin
        forbidden_routes = [
            ("GET", "/admin/users", "GET /admin/users"),
            ("GET", "/admin/admins", "GET /admin/admins"),
            ("GET", "/admin/instruments", "GET /admin/instruments")
        ]
        
        for method, route, name in forbidden_routes:
            try:
                if method == "GET":
                    resp = requests.get(f"{BASE_URL}{route}", 
                                       headers={"Authorization": f"Bearer {admin_kua_token}"}, 
                                       timeout=10)
                if resp.status_code == 403 and "luar wilayah" in resp.text.lower():
                    log_test(f"Scoped admin {name} returns 403", True, resp.json().get("error", ""))
                else:
                    log_test(f"Scoped admin {name} returns 403", False,
                            f"Expected 403, got {resp.status_code}: {resp.text}")
            except Exception as e:
                log_test(f"Scoped admin {name} returns 403", False, f"Exception: {e}")
        
        # Test allowed routes for scoped admin
        allowed_routes = [
            ("GET", "/admin/stats", "GET /admin/stats"),
            ("GET", "/admin/alerts", "GET /admin/alerts")
        ]
        
        for method, route, name in allowed_routes:
            try:
                if method == "GET":
                    resp = requests.get(f"{BASE_URL}{route}", 
                                       headers={"Authorization": f"Bearer {admin_kua_token}"}, 
                                       timeout=10)
                if resp.status_code == 200:
                    log_test(f"Scoped admin {name} returns 200", True)
                else:
                    log_test(f"Scoped admin {name} returns 200", False,
                            f"Expected 200, got {resp.status_code}: {resp.text}")
            except Exception as e:
                log_test(f"Scoped admin {name} returns 200", False, f"Exception: {e}")
        
        # Test normal user RBAC
        user_data = {
            "name": "Normal User RBAC",
            "username": f"user_rbac_{timestamp}",
            "password": "pass123",
            "kota": "Test Kota",
            "kecamatan": "Test Kec",
            "alamat": "Test Alamat"
        }
        resp = requests.post(f"{BASE_URL}/auth/register", json=user_data, timeout=10)
        if resp.status_code != 200:
            log_test("Register normal user for RBAC test", False, f"Status {resp.status_code}")
            return
        user_token = resp.json().get("token")
        log_test("Register normal user for RBAC test", True)
        
        # Test forbidden routes for normal user
        user_forbidden_routes = [
            ("GET", "/admin/stats", "GET /admin/stats"),
            ("POST", "/admin/admins", "POST /admin/admins")
        ]
        
        for method, route, name in user_forbidden_routes:
            try:
                if method == "GET":
                    resp = requests.get(f"{BASE_URL}{route}", 
                                       headers={"Authorization": f"Bearer {user_token}"}, 
                                       timeout=10)
                elif method == "POST":
                    resp = requests.post(f"{BASE_URL}{route}", 
                                        json={},
                                        headers={"Authorization": f"Bearer {user_token}"}, 
                                        timeout=10)
                if resp.status_code == 403:
                    log_test(f"Normal user {name} returns 403", True, resp.json().get("error", ""))
                else:
                    log_test(f"Normal user {name} returns 403", False,
                            f"Expected 403, got {resp.status_code}: {resp.text}")
            except Exception as e:
                log_test(f"Normal user {name} returns 403", False, f"Exception: {e}")
        
    except Exception as e:
        log_test("RBAC test", False, f"Exception: {e}")

def test_sdq_regression():
    """Test SDQ scoring regression - confirm no regression"""
    print("\n" + "="*80)
    print("TEST SECTION: SDQ SCORING REGRESSION")
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
            else:
                log_test(f"SDQ subscale {key} score", True, f"Score={actual_val}")
        
        actual_total = result.get("totalDifficulties")
        if actual_total != expected_total:
            log_test("SDQ Total Difficulties score", False,
                    f"Expected {expected_total}, got {actual_total}")
        else:
            log_test("SDQ Total Difficulties score", True, f"Total={actual_total}")
        
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
    print("PHD BACKEND TEST SUITE - UPDATE 7: ADDRESS FIELDS + REGIONAL ADMIN ROLES")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Super Admin: {SUPER_ADMIN_USERNAME} / {SUPER_ADMIN_PASSWORD}")
    print("="*80)
    
    # Section A: Registration with address fields
    user_data = test_registration_with_address_fields()
    if user_data:
        test_registration_validation()
        test_auth_me_includes_address(user_data["token1"])
        
        # Section B: Alert denormalization
        admin_token = test_alert_denormalization(
            user_data["token1"], 
            user_data["user1"]["kota"], 
            user_data["user1"]["kecamatan"]
        )
        
        if admin_token:
            # Section C: Regional admin CRUD
            test_regional_admin_crud(admin_token)
            
            # Section D: Data scoping
            test_data_scoping(admin_token)
    
    # Section E: RBAC
    test_rbac()
    
    # Regression test: SDQ scoring
    test_sdq_regression()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {tests_passed + tests_failed}")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"Success Rate: {tests_passed / (tests_passed + tests_failed) * 100:.1f}%")
    print("="*80)
    
    # Exit with appropriate code
    sys.exit(0 if tests_failed == 0 else 1)

if __name__ == "__main__":
    main()
