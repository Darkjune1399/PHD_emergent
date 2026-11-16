#!/usr/bin/env python3
"""
Backend Test Suite for NEW Assessment Management Endpoints
Tests GET /api/admin/assessments, GET /api/admin/assessments/:id, GET /api/admin/assessment-accounts
with filters, pagination, RBAC, scoping, and concurrency.
"""

import requests
import json
import sys
import time
import concurrent.futures
from datetime import datetime, timedelta

BASE_URL = "https://4ae477a3-9b75-4abf-b321-86d624dd8d0e.preview.emergentagent.com/api"
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

def setup_test_data():
    """Setup test data: register 2 users in different regions, add members, submit assessments"""
    print("\n" + "="*80)
    print("SETUP: Creating Test Data")
    print("="*80)
    
    timestamp = int(datetime.now().timestamp())
    
    # User A in Kabupaten Jember, Ajung, Ajung
    userA_data = {
        "name": "Budi Santoso",
        "username": f"budi_jember_{timestamp}",
        "password": "pass123",
        "kota": "Kabupaten Jember",
        "kecamatan": "Ajung",
        "kelurahan": "Ajung",
        "alamat": "Jl. Mawar No. 15, Ajung"
    }
    
    # User B in Kabupaten Banyuwangi, Genteng, Genteng Kulon
    userB_data = {
        "name": "Siti Rahayu",
        "username": f"siti_banyuwangi_{timestamp}",
        "password": "pass123",
        "kota": "Kabupaten Banyuwangi",
        "kecamatan": "Genteng",
        "kelurahan": "Genteng Kulon",
        "alamat": "Jl. Melati No. 22, Genteng"
    }
    
    try:
        # Register User A
        resp = requests.post(f"{BASE_URL}/auth/register", json=userA_data, timeout=30)
        if resp.status_code != 200:
            log_test("Register User A (Jember)", False, f"Status {resp.status_code}: {resp.text}")
            return None
        userA_token = resp.json().get("token")
        userA_id = resp.json().get("user", {}).get("id")
        log_test("Register User A (Jember)", True, f"Username: {userA_data['username']}")
        
        # Register User B
        resp = requests.post(f"{BASE_URL}/auth/register", json=userB_data, timeout=30)
        if resp.status_code != 200:
            log_test("Register User B (Banyuwangi)", False, f"Status {resp.status_code}: {resp.text}")
            return None
        userB_token = resp.json().get("token")
        userB_id = resp.json().get("user", {}).get("id")
        log_test("Register User B (Banyuwangi)", True, f"Username: {userB_data['username']}")
        
        # Add members for User A
        # Adult member (age ~35) - gets phq9 + ghq12
        adult_dob = (datetime.now() - timedelta(days=35*365)).strftime("%Y-%m-%d")
        memberA1_data = {
            "fullName": "Budi Santoso",
            "gender": "Laki-laki",
            "dob": adult_dob,
            "relationship": "Diri Sendiri"
        }
        resp = requests.post(f"{BASE_URL}/members", json=memberA1_data,
                            headers={"Authorization": f"Bearer {userA_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Add adult member for User A", False, f"Status {resp.status_code}")
            return None
        memberA1 = resp.json()
        memberA1_id = memberA1.get("id")
        log_test("Add adult member for User A", True, f"Member: {memberA1_data['fullName']}, instruments: {[i['code'] for i in memberA1.get('instruments', [])]}")
        
        # Child member (age ~8) - gets sdq_parent
        child_dob = (datetime.now() - timedelta(days=8*365)).strftime("%Y-%m-%d")
        memberA2_data = {
            "fullName": "Andi Santoso",
            "gender": "Laki-laki",
            "dob": child_dob,
            "relationship": "Anak"
        }
        resp = requests.post(f"{BASE_URL}/members", json=memberA2_data,
                            headers={"Authorization": f"Bearer {userA_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Add child member for User A", False, f"Status {resp.status_code}")
            return None
        memberA2 = resp.json()
        memberA2_id = memberA2.get("id")
        log_test("Add child member for User A", True, f"Member: {memberA2_data['fullName']}, instruments: {[i['code'] for i in memberA2.get('instruments', [])]}")
        
        # Teen member (age ~14) - gets sdq_self
        teen_dob = (datetime.now() - timedelta(days=14*365)).strftime("%Y-%m-%d")
        memberA3_data = {
            "fullName": "Dewi Santoso",
            "gender": "Perempuan",
            "dob": teen_dob,
            "relationship": "Anak"
        }
        resp = requests.post(f"{BASE_URL}/members", json=memberA3_data,
                            headers={"Authorization": f"Bearer {userA_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Add teen member for User A", False, f"Status {resp.status_code}")
            return None
        memberA3 = resp.json()
        memberA3_id = memberA3.get("id")
        log_test("Add teen member for User A", True, f"Member: {memberA3_data['fullName']}, instruments: {[i['code'] for i in memberA3.get('instruments', [])]}")
        
        # Add members for User B
        # Adult member (age ~28)
        adult_dob_b = (datetime.now() - timedelta(days=28*365)).strftime("%Y-%m-%d")
        memberB1_data = {
            "fullName": "Siti Rahayu",
            "gender": "Perempuan",
            "dob": adult_dob_b,
            "relationship": "Diri Sendiri"
        }
        resp = requests.post(f"{BASE_URL}/members", json=memberB1_data,
                            headers={"Authorization": f"Bearer {userB_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Add adult member for User B", False, f"Status {resp.status_code}")
            return None
        memberB1 = resp.json()
        memberB1_id = memberB1.get("id")
        log_test("Add adult member for User B", True, f"Member: {memberB1_data['fullName']}")
        
        # Submit assessments for User A
        # PHQ-9 with high score (all 3s) -> Abnormal, redFlag
        phq9_answers_high = {str(i): 3 for i in range(1, 10)}
        resp = requests.post(f"{BASE_URL}/assessments", 
                            json={"memberId": memberA1_id, "instrumentCode": "phq9", "answers": phq9_answers_high},
                            headers={"Authorization": f"Bearer {userA_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Submit PHQ-9 (high score) for User A adult", False, f"Status {resp.status_code}")
            return None
        assessmentA1 = resp.json()
        log_test("Submit PHQ-9 (high score) for User A adult", True, 
                f"Assessment ID: {assessmentA1.get('id')}, redFlag: {assessmentA1.get('result', {}).get('redFlag')}")
        
        # GHQ-12 with normal score (all 0s) -> Normal
        ghq12_answers_normal = {str(i): 0 for i in range(1, 13)}
        resp = requests.post(f"{BASE_URL}/assessments", 
                            json={"memberId": memberA1_id, "instrumentCode": "ghq12", "answers": ghq12_answers_normal},
                            headers={"Authorization": f"Bearer {userA_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Submit GHQ-12 (normal) for User A adult", False, f"Status {resp.status_code}")
            return None
        assessmentA2 = resp.json()
        log_test("Submit GHQ-12 (normal) for User A adult", True, 
                f"Assessment ID: {assessmentA2.get('id')}, level: {assessmentA2.get('result', {}).get('overallCategory')}")
        
        # SDQ for child (all 0s) -> Normal
        sdq_answers_normal = {str(i): 0 for i in range(1, 26)}
        resp = requests.post(f"{BASE_URL}/assessments", 
                            json={"memberId": memberA2_id, "instrumentCode": "sdq_parent", "answers": sdq_answers_normal},
                            headers={"Authorization": f"Bearer {userA_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Submit SDQ (normal) for User A child", False, f"Status {resp.status_code}")
            return None
        assessmentA3 = resp.json()
        log_test("Submit SDQ (normal) for User A child", True, 
                f"Assessment ID: {assessmentA3.get('id')}")
        
        # Submit assessments for User B
        # PHQ-9 with suicide risk (item 9 > 0) -> redFlag
        phq9_answers_suicide = {str(i): 0 for i in range(1, 10)}
        phq9_answers_suicide["9"] = 2
        resp = requests.post(f"{BASE_URL}/assessments", 
                            json={"memberId": memberB1_id, "instrumentCode": "phq9", "answers": phq9_answers_suicide},
                            headers={"Authorization": f"Bearer {userB_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Submit PHQ-9 (suicide risk) for User B", False, f"Status {resp.status_code}")
            return None
        assessmentB1 = resp.json()
        log_test("Submit PHQ-9 (suicide risk) for User B", True, 
                f"Assessment ID: {assessmentB1.get('id')}, redFlag: {assessmentB1.get('result', {}).get('redFlag')}")
        
        # GHQ-12 with high score (all 2s) -> Abnormal, redFlag
        ghq12_answers_high = {str(i): 2 for i in range(1, 13)}
        resp = requests.post(f"{BASE_URL}/assessments", 
                            json={"memberId": memberB1_id, "instrumentCode": "ghq12", "answers": ghq12_answers_high},
                            headers={"Authorization": f"Bearer {userB_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Submit GHQ-12 (high score) for User B", False, f"Status {resp.status_code}")
            return None
        assessmentB2 = resp.json()
        log_test("Submit GHQ-12 (high score) for User B", True, 
                f"Assessment ID: {assessmentB2.get('id')}, redFlag: {assessmentB2.get('result', {}).get('redFlag')}")
        
        print(f"\n✅ Setup complete: 2 users, 4 members, 5 assessments created")
        
        return {
            "userA": {"data": userA_data, "token": userA_token, "id": userA_id, 
                     "members": [memberA1_id, memberA2_id, memberA3_id],
                     "assessments": [assessmentA1.get('id'), assessmentA2.get('id'), assessmentA3.get('id')]},
            "userB": {"data": userB_data, "token": userB_token, "id": userB_id,
                     "members": [memberB1_id],
                     "assessments": [assessmentB1.get('id'), assessmentB2.get('id')]}
        }
        
    except Exception as e:
        log_test("Setup test data", False, f"Exception: {e}")
        return None

def test_admin_assessments_list(admin_token, test_data):
    """Test 1: GET /api/admin/assessments - basic list with shape validation"""
    print("\n" + "="*80)
    print("TEST 1: GET /api/admin/assessments - Basic List & Shape")
    print("="*80)
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/assessments", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        
        if resp.status_code != 200:
            log_test("GET /api/admin/assessments returns 200", False, 
                    f"Status {resp.status_code}: {resp.text}")
            return
        
        data = resp.json()
        log_test("GET /api/admin/assessments returns 200", True)
        
        # Check shape
        required_fields = ["items", "total", "page", "pages", "limit", "summary", "filters", "instruments"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            log_test("Response has required fields", False, f"Missing: {missing_fields}")
        else:
            log_test("Response has required fields", True, 
                    f"All fields present: {', '.join(required_fields)}")
        
        # Check summary shape
        summary = data.get("summary", {})
        summary_fields = ["total", "Normal", "Ambang", "Abnormal", "redFlag"]
        missing_summary = [f for f in summary_fields if f not in summary]
        if missing_summary:
            log_test("Summary has required fields", False, f"Missing: {missing_summary}")
        else:
            log_test("Summary has required fields", True, 
                    f"total={summary['total']}, Normal={summary['Normal']}, Ambang={summary['Ambang']}, Abnormal={summary['Abnormal']}, redFlag={summary['redFlag']}")
        
        # Check filters shape
        filters = data.get("filters", {})
        filter_fields = ["kotaList", "kecamatanList", "kelurahanList"]
        missing_filters = [f for f in filter_fields if f not in filters]
        if missing_filters:
            log_test("Filters has required fields", False, f"Missing: {missing_filters}")
        else:
            log_test("Filters has required fields", True, 
                    f"kotaList count={len(filters['kotaList'])}, kecamatanList count={len(filters['kecamatanList'])}, kelurahanList count={len(filters['kelurahanList'])}")
        
        # Check instruments list
        instruments = data.get("instruments", [])
        if len(instruments) > 0:
            log_test("Instruments list present", True, f"Found {len(instruments)} instruments")
        else:
            log_test("Instruments list present", False, "Empty instruments list")
        
        # Check items structure
        items = data.get("items", [])
        if len(items) > 0:
            item = items[0]
            # Check that items contain relationship (matching member relationship)
            if "relationship" in item:
                log_test("Items contain 'relationship' field", True, f"relationship={item.get('relationship')}")
            else:
                log_test("Items contain 'relationship' field", False, "Missing relationship field")
            
            # Check that items contain account with required fields
            account = item.get("account", {})
            account_fields = ["name", "username", "alamat"]
            if all(f in account for f in account_fields):
                log_test("Items contain account with name/username/alamat", True)
            else:
                log_test("Items contain account with name/username/alamat", False, 
                        f"Account fields: {list(account.keys())}")
            
            # Check that account does NOT contain passwordHash
            if "passwordHash" not in account:
                log_test("Account does NOT contain passwordHash", True)
            else:
                log_test("Account does NOT contain passwordHash", False, "passwordHash found in account")
            
            # Check that items do NOT contain 'answers'
            if "answers" not in item:
                log_test("Items do NOT contain 'answers' field", True)
            else:
                log_test("Items do NOT contain 'answers' field", False, "answers field found in item")
            
            # Check that items contain memberName, overallCategory, level, score, scoreMax, redFlag, alert
            item_fields = ["memberName", "overallCategory", "level", "score", "scoreMax", "redFlag"]
            missing_item_fields = [f for f in item_fields if f not in item]
            if missing_item_fields:
                log_test("Items contain required fields", False, f"Missing: {missing_item_fields}")
            else:
                log_test("Items contain required fields", True, 
                        f"memberName, overallCategory, level, score, scoreMax, redFlag all present")
            
            # Check that alert is present (can be null or object)
            if "alert" in item:
                log_test("Items contain 'alert' field", True, 
                        f"alert={'non-null' if item.get('alert') else 'null'}")
            else:
                log_test("Items contain 'alert' field", False, "Missing alert field")
        else:
            log_test("Items list not empty", False, "No items in response")
        
        # Check that list includes both normal and red-flag results
        has_normal = any(item.get("redFlag") == False for item in items)
        has_redflag = any(item.get("redFlag") == True for item in items)
        if has_normal and has_redflag:
            log_test("List includes both normal and red-flag results", True, 
                    f"Normal count: {sum(1 for i in items if not i.get('redFlag'))}, RedFlag count: {sum(1 for i in items if i.get('redFlag'))}")
        else:
            log_test("List includes both normal and red-flag results", False, 
                    f"has_normal={has_normal}, has_redflag={has_redflag}")
        
        # Check sorting by createdAt desc
        if len(items) >= 2:
            dates = [item.get("createdAt") for item in items if item.get("createdAt")]
            if dates == sorted(dates, reverse=True):
                log_test("Items sorted by createdAt desc", True)
            else:
                log_test("Items sorted by createdAt desc", False, "Items not in descending order")
        
    except Exception as e:
        log_test("GET /api/admin/assessments test", False, f"Exception: {e}")

def test_filters(admin_token, test_data):
    """Test 2: Filters - level, redFlag, instrument, q, kota/kecamatan/kelurahan"""
    print("\n" + "="*80)
    print("TEST 2: Filters")
    print("="*80)
    
    try:
        # Test level=Normal filter
        resp = requests.get(f"{BASE_URL}/admin/assessments?level=Normal", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_normal = all(item.get("level") == "Normal" for item in items)
            if all_normal and len(items) > 0:
                log_test("Filter level=Normal returns only Normal items", True, 
                        f"Found {len(items)} Normal items")
            else:
                log_test("Filter level=Normal returns only Normal items", False, 
                        f"Not all items are Normal or empty list")
        else:
            log_test("Filter level=Normal", False, f"Status {resp.status_code}")
        
        # Test level=Abnormal filter
        resp = requests.get(f"{BASE_URL}/admin/assessments?level=Abnormal", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_abnormal = all(item.get("level") == "Abnormal" for item in items)
            if all_abnormal and len(items) > 0:
                log_test("Filter level=Abnormal returns only Abnormal items", True, 
                        f"Found {len(items)} Abnormal items")
            else:
                log_test("Filter level=Abnormal returns only Abnormal items", False, 
                        f"Not all items are Abnormal or empty list")
        else:
            log_test("Filter level=Abnormal", False, f"Status {resp.status_code}")
        
        # Test redFlag=yes filter
        resp = requests.get(f"{BASE_URL}/admin/assessments?redFlag=yes", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_redflag = all(item.get("redFlag") == True for item in items)
            if all_redflag and len(items) > 0:
                log_test("Filter redFlag=yes returns only redFlag=true items", True, 
                        f"Found {len(items)} red flag items")
            else:
                log_test("Filter redFlag=yes returns only redFlag=true items", False, 
                        f"Not all items have redFlag=true or empty list")
        else:
            log_test("Filter redFlag=yes", False, f"Status {resp.status_code}")
        
        # Test redFlag=no filter
        resp = requests.get(f"{BASE_URL}/admin/assessments?redFlag=no", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_no_redflag = all(item.get("redFlag") == False for item in items)
            if all_no_redflag and len(items) > 0:
                log_test("Filter redFlag=no returns only redFlag=false items", True, 
                        f"Found {len(items)} non-red-flag items")
            else:
                log_test("Filter redFlag=no returns only redFlag=false items", False, 
                        f"Not all items have redFlag=false or empty list")
        else:
            log_test("Filter redFlag=no", False, f"Status {resp.status_code}")
        
        # Test instrument=phq9 filter
        resp = requests.get(f"{BASE_URL}/admin/assessments?instrument=phq9", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_phq9 = all(item.get("instrumentCode") == "phq9" for item in items)
            if all_phq9 and len(items) > 0:
                log_test("Filter instrument=phq9 returns only phq9 items", True, 
                        f"Found {len(items)} PHQ-9 assessments")
            else:
                log_test("Filter instrument=phq9 returns only phq9 items", False, 
                        f"Not all items are phq9 or empty list")
        else:
            log_test("Filter instrument=phq9", False, f"Status {resp.status_code}")
        
        # Test q filter with member name
        member_name = "Budi"  # Part of "Budi Santoso"
        resp = requests.get(f"{BASE_URL}/admin/assessments?q={member_name}", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            found_match = any(member_name.lower() in item.get("memberName", "").lower() for item in items)
            if found_match:
                log_test(f"Filter q={member_name} finds member name", True, 
                        f"Found {len(items)} items matching '{member_name}'")
            else:
                log_test(f"Filter q={member_name} finds member name", False, 
                        f"No items found matching '{member_name}'")
        else:
            log_test(f"Filter q={member_name}", False, f"Status {resp.status_code}")
        
        # Test q filter with account holder name
        account_name = "Siti"  # Part of "Siti Rahayu"
        resp = requests.get(f"{BASE_URL}/admin/assessments?q={account_name}", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            found_match = any(account_name.lower() in item.get("account", {}).get("name", "").lower() for item in items)
            if found_match:
                log_test(f"Filter q={account_name} finds account holder name", True, 
                        f"Found {len(items)} items matching '{account_name}'")
            else:
                log_test(f"Filter q={account_name} finds account holder name", False, 
                        f"No items found matching '{account_name}'")
        else:
            log_test(f"Filter q={account_name}", False, f"Status {resp.status_code}")
        
        # Test q filter with username
        username = test_data["userA"]["data"]["username"]
        resp = requests.get(f"{BASE_URL}/admin/assessments?q={username}", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            found_match = any(username in item.get("account", {}).get("username", "") for item in items)
            if found_match:
                log_test(f"Filter q={username} finds username", True, 
                        f"Found {len(items)} items matching username")
            else:
                log_test(f"Filter q={username} finds username", False, 
                        f"No items found matching username")
        else:
            log_test(f"Filter q={username}", False, f"Status {resp.status_code}")
        
        # Test kota filter
        kota = "Kabupaten Jember"
        resp = requests.get(f"{BASE_URL}/admin/assessments?kota={kota}", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_jember = all(item.get("kota") == kota for item in items)
            if all_jember and len(items) > 0:
                log_test(f"Filter kota={kota} returns only Jember items", True, 
                        f"Found {len(items)} items from Jember")
            else:
                log_test(f"Filter kota={kota} returns only Jember items", False, 
                        f"Not all items from Jember or empty list")
        else:
            log_test(f"Filter kota={kota}", False, f"Status {resp.status_code}")
        
        # Test kecamatan filter
        kecamatan = "Ajung"
        resp = requests.get(f"{BASE_URL}/admin/assessments?kecamatan={kecamatan}", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_ajung = all(item.get("kecamatan") == kecamatan for item in items)
            if all_ajung and len(items) > 0:
                log_test(f"Filter kecamatan={kecamatan} returns only Ajung items", True, 
                        f"Found {len(items)} items from Ajung")
            else:
                log_test(f"Filter kecamatan={kecamatan} returns only Ajung items", False, 
                        f"Not all items from Ajung or empty list")
        else:
            log_test(f"Filter kecamatan={kecamatan}", False, f"Status {resp.status_code}")
        
        # Test kelurahan filter
        kelurahan = "Ajung"
        resp = requests.get(f"{BASE_URL}/admin/assessments?kelurahan={kelurahan}", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_ajung_kel = all(item.get("kelurahan") == kelurahan for item in items)
            if all_ajung_kel and len(items) > 0:
                log_test(f"Filter kelurahan={kelurahan} returns only Ajung kelurahan items", True, 
                        f"Found {len(items)} items from Ajung kelurahan")
            else:
                log_test(f"Filter kelurahan={kelurahan} returns only Ajung kelurahan items", False, 
                        f"Not all items from Ajung kelurahan or empty list")
        else:
            log_test(f"Filter kelurahan={kelurahan}", False, f"Status {resp.status_code}")
        
        # Test summary consistency with level filter
        # Get unfiltered summary
        resp = requests.get(f"{BASE_URL}/admin/assessments", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            unfiltered_data = resp.json()
            unfiltered_summary = unfiltered_data.get("summary", {})
            unfiltered_total = unfiltered_data.get("total")
            
            # Get filtered by level=Normal
            resp = requests.get(f"{BASE_URL}/admin/assessments?level=Normal", 
                               headers={"Authorization": f"Bearer {admin_token}"}, 
                               timeout=10)
            if resp.status_code == 200:
                filtered_data = resp.json()
                filtered_summary = filtered_data.get("summary", {})
                filtered_total = filtered_data.get("total")
                
                # Summary should be pre-level-filter (same as unfiltered)
                # But total should reflect level filter
                summary_consistent = (filtered_summary.get("total") == unfiltered_summary.get("total"))
                total_reflects_filter = (filtered_total <= unfiltered_total)
                
                if summary_consistent and total_reflects_filter:
                    log_test("Summary counts consistent (pre-filter) but total reflects level filter", True, 
                            f"summary.total={filtered_summary.get('total')} (pre-filter), total={filtered_total} (post-filter)")
                else:
                    log_test("Summary counts consistent (pre-filter) but total reflects level filter", False, 
                            f"summary_consistent={summary_consistent}, total_reflects_filter={total_reflects_filter}")
        
    except Exception as e:
        log_test("Filters test", False, f"Exception: {e}")

def test_pagination(admin_token):
    """Test 3: Pagination - limit, page, pages calculation"""
    print("\n" + "="*80)
    print("TEST 3: Pagination")
    print("="*80)
    
    try:
        # Test limit=2&page=1
        resp1 = requests.get(f"{BASE_URL}/admin/assessments?limit=2&page=1", 
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp1.status_code != 200:
            log_test("GET with limit=2&page=1", False, f"Status {resp1.status_code}")
            return
        
        data1 = resp1.json()
        items1 = data1.get("items", [])
        total = data1.get("total", 0)
        pages = data1.get("pages", 0)
        
        log_test("GET with limit=2&page=1 returns 200", True, 
                f"items count={len(items1)}, total={total}, pages={pages}")
        
        # Test limit=2&page=2
        resp2 = requests.get(f"{BASE_URL}/admin/assessments?limit=2&page=2", 
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp2.status_code != 200:
            log_test("GET with limit=2&page=2", False, f"Status {resp2.status_code}")
            return
        
        data2 = resp2.json()
        items2 = data2.get("items", [])
        
        log_test("GET with limit=2&page=2 returns 200", True, 
                f"items count={len(items2)}")
        
        # Check that page 1 and page 2 return different items
        if len(items1) > 0 and len(items2) > 0:
            ids1 = [item.get("id") for item in items1]
            ids2 = [item.get("id") for item in items2]
            different = not any(id in ids2 for id in ids1)
            if different:
                log_test("Page 1 and page 2 return different items", True)
            else:
                log_test("Page 1 and page 2 return different items", False, 
                        "Some items appear in both pages")
        
        # Check pages calculation: pages = ceil(total/limit)
        import math
        expected_pages = math.ceil(total / 2) if total > 0 else 1
        if pages == expected_pages:
            log_test("Pages calculation correct (ceil(total/limit))", True, 
                    f"pages={pages}, expected={expected_pages}")
        else:
            log_test("Pages calculation correct (ceil(total/limit))", False, 
                    f"pages={pages}, expected={expected_pages}")
        
        # Test limit capped at 100
        resp3 = requests.get(f"{BASE_URL}/admin/assessments?limit=200", 
                            headers={"Authorization": f"Bearer {admin_token}"}, 
                            timeout=10)
        if resp3.status_code == 200:
            data3 = resp3.json()
            limit_returned = data3.get("limit", 0)
            if limit_returned <= 100:
                log_test("Limit capped at 100", True, f"limit={limit_returned}")
            else:
                log_test("Limit capped at 100", False, f"limit={limit_returned} exceeds 100")
        else:
            log_test("Limit capped at 100", False, f"Status {resp3.status_code}")
        
    except Exception as e:
        log_test("Pagination test", False, f"Exception: {e}")

def test_assessment_detail(admin_token, test_data):
    """Test 4: GET /api/admin/assessments/:id - detail view"""
    print("\n" + "="*80)
    print("TEST 4: GET /api/admin/assessments/:id - Detail View")
    print("="*80)
    
    try:
        # Get an assessment ID from test data
        assessment_id = test_data["userA"]["assessments"][0]
        
        resp = requests.get(f"{BASE_URL}/admin/assessments/{assessment_id}", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        
        if resp.status_code != 200:
            log_test("GET /api/admin/assessments/:id returns 200", False, 
                    f"Status {resp.status_code}: {resp.text}")
            return
        
        data = resp.json()
        log_test("GET /api/admin/assessments/:id returns 200", True)
        
        # Check result field
        if "result" in data:
            log_test("Response contains 'result' field", True)
        else:
            log_test("Response contains 'result' field", False)
        
        # Check answerDetail field
        if "answerDetail" in data:
            answer_detail = data.get("answerDetail", [])
            if len(answer_detail) > 0:
                item = answer_detail[0]
                if all(f in item for f in ["text", "value", "label"]):
                    log_test("Response contains 'answerDetail' array with text/value/label", True, 
                            f"answerDetail has {len(answer_detail)} items")
                else:
                    log_test("Response contains 'answerDetail' array with text/value/label", False, 
                            f"Missing fields in answerDetail item: {list(item.keys())}")
            else:
                log_test("Response contains 'answerDetail' array", False, "answerDetail is empty")
        else:
            log_test("Response contains 'answerDetail' field", False)
        
        # Check account field (no passwordHash)
        if "account" in data:
            account = data.get("account", {})
            if "passwordHash" not in account:
                log_test("Account does NOT contain passwordHash", True)
            else:
                log_test("Account does NOT contain passwordHash", False)
            
            account_fields = ["name", "username", "alamat", "kota", "kecamatan", "kelurahan"]
            if all(f in account for f in account_fields):
                log_test("Account contains required fields", True, 
                        f"Fields: {', '.join(account_fields)}")
            else:
                log_test("Account contains required fields", False, 
                        f"Missing some fields: {list(account.keys())}")
        else:
            log_test("Response contains 'account' field", False)
        
        # Check member field
        if "member" in data:
            member = data.get("member", {})
            if member:
                member_fields = ["fullName", "relationship", "age"]
                if all(f in member for f in member_fields):
                    log_test("Member contains fullName/relationship/age", True, 
                            f"Member: {member.get('fullName')}, age: {member.get('age')}")
                else:
                    log_test("Member contains fullName/relationship/age", False, 
                            f"Missing fields: {list(member.keys())}")
            else:
                log_test("Member field present", False, "Member is null")
        else:
            log_test("Response contains 'member' field", False)
        
        # Check family field
        if "family" in data:
            family = data.get("family", [])
            if len(family) > 0:
                # Check that one member has isCurrent=true
                has_current = any(m.get("isCurrent") == True for m in family)
                if has_current:
                    log_test("Family has one member with isCurrent=true", True, 
                            f"Family has {len(family)} members")
                else:
                    log_test("Family has one member with isCurrent=true", False)
                
                # Check family member structure
                fam_member = family[0]
                fam_fields = ["assessmentCount", "latest"]
                if all(f in fam_member for f in fam_fields):
                    log_test("Family members have assessmentCount & latest", True)
                else:
                    log_test("Family members have assessmentCount & latest", False, 
                            f"Missing fields: {list(fam_member.keys())}")
            else:
                log_test("Family array not empty", False, "Family is empty")
        else:
            log_test("Response contains 'family' field", False)
        
        # Check memberHistory field
        if "memberHistory" in data:
            member_history = data.get("memberHistory", [])
            log_test("Response contains 'memberHistory' field", True, 
                    f"memberHistory has {len(member_history)} items")
        else:
            log_test("Response contains 'memberHistory' field", False)
        
        # Test unknown ID returns 404
        resp = requests.get(f"{BASE_URL}/admin/assessments/nonexistent-id-999", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 404:
            log_test("Unknown assessment ID returns 404", True)
        else:
            log_test("Unknown assessment ID returns 404", False, 
                    f"Expected 404, got {resp.status_code}")
        
    except Exception as e:
        log_test("Assessment detail test", False, f"Exception: {e}")

def test_assessment_accounts(admin_token):
    """Test 5: GET /api/admin/assessment-accounts - account-level view"""
    print("\n" + "="*80)
    print("TEST 5: GET /api/admin/assessment-accounts - Account-Level View")
    print("="*80)
    
    try:
        resp = requests.get(f"{BASE_URL}/admin/assessment-accounts", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        
        if resp.status_code != 200:
            log_test("GET /api/admin/assessment-accounts returns 200", False, 
                    f"Status {resp.status_code}: {resp.text}")
            return
        
        data = resp.json()
        log_test("GET /api/admin/assessment-accounts returns 200", True)
        
        # Check shape
        required_fields = ["items", "total", "page", "pages", "limit"]
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            log_test("Response has required fields", False, f"Missing: {missing_fields}")
        else:
            log_test("Response has required fields", True, 
                    f"All fields present: {', '.join(required_fields)}")
        
        # Check items structure
        items = data.get("items", [])
        if len(items) > 0:
            item = items[0]
            
            # Check account field
            if "account" in item:
                account = item.get("account", {})
                account_fields = ["name", "username", "alamat", "kota", "kecamatan", "kelurahan", "status"]
                if all(f in account for f in account_fields):
                    log_test("Each item has account with required fields", True)
                else:
                    log_test("Each item has account with required fields", False, 
                            f"Missing fields: {[f for f in account_fields if f not in account]}")
            else:
                log_test("Each item has account field", False)
            
            # Check memberCount, assessmentCount, redFlagCount, lastAssessmentAt
            item_fields = ["memberCount", "assessmentCount", "redFlagCount", "lastAssessmentAt"]
            if all(f in item for f in item_fields):
                log_test("Each item has memberCount/assessmentCount/redFlagCount/lastAssessmentAt", True, 
                        f"memberCount={item.get('memberCount')}, assessmentCount={item.get('assessmentCount')}, redFlagCount={item.get('redFlagCount')}")
            else:
                log_test("Each item has required count fields", False, 
                        f"Missing: {[f for f in item_fields if f not in item]}")
            
            # Check members array
            if "members" in item:
                members = item.get("members", [])
                if len(members) > 0:
                    member = members[0]
                    member_fields = ["fullName", "relationship", "assessmentCount", "latest"]
                    if all(f in member for f in member_fields):
                        log_test("Each item has members array with fullName/relationship/assessmentCount/latest", True, 
                                f"First member: {member.get('fullName')}, assessmentCount={member.get('assessmentCount')}")
                    else:
                        log_test("Each item has members with required fields", False, 
                                f"Missing: {[f for f in member_fields if f not in member]}")
                else:
                    log_test("Members array not empty", False, "Members array is empty")
            else:
                log_test("Each item has members field", False)
        else:
            log_test("Items list not empty", False, "No items in response")
        
        # Test filters work (q, level, redFlag, region)
        resp = requests.get(f"{BASE_URL}/admin/assessment-accounts?level=Abnormal", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            log_test("Filter level=Abnormal works on assessment-accounts", True)
        else:
            log_test("Filter level=Abnormal works on assessment-accounts", False, 
                    f"Status {resp.status_code}")
        
        # Test pagination works
        resp = requests.get(f"{BASE_URL}/admin/assessment-accounts?limit=1&page=1", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("limit") == 1 and len(data.get("items", [])) <= 1:
                log_test("Pagination works on assessment-accounts", True, 
                        f"limit=1, items count={len(data.get('items', []))}")
            else:
                log_test("Pagination works on assessment-accounts", False, 
                        f"limit={data.get('limit')}, items count={len(data.get('items', []))}")
        else:
            log_test("Pagination works on assessment-accounts", False, 
                    f"Status {resp.status_code}")
        
    except Exception as e:
        log_test("Assessment accounts test", False, f"Exception: {e}")

def test_rbac_scoping(admin_token, test_data):
    """Test 6: RBAC and scoping for regional admins"""
    print("\n" + "="*80)
    print("TEST 6: RBAC & Scoping")
    print("="*80)
    
    try:
        # Test normal user token returns 403
        user_token = test_data["userA"]["token"]
        
        endpoints = [
            "/admin/assessments",
            "/admin/assessment-accounts"
        ]
        
        for endpoint in endpoints:
            resp = requests.get(f"{BASE_URL}{endpoint}", 
                               headers={"Authorization": f"Bearer {user_token}"}, 
                               timeout=10)
            if resp.status_code == 403:
                log_test(f"Normal user token returns 403 on {endpoint}", True)
            else:
                log_test(f"Normal user token returns 403 on {endpoint}", False, 
                        f"Expected 403, got {resp.status_code}")
        
        # Test no token returns 401
        for endpoint in endpoints:
            resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if resp.status_code == 401:
                log_test(f"No token returns 401 on {endpoint}", True)
            else:
                log_test(f"No token returns 401 on {endpoint}", False, 
                        f"Expected 401, got {resp.status_code}")
        
        # Create scoped admins
        timestamp = int(datetime.now().timestamp())
        
        # Create admin_pa (Jember)
        admin_pa_data = {
            "name": "Admin PA Jember",
            "username": f"admin_pa_jember_{timestamp}",
            "password": "pass123",
            "role": "admin_pa",
            "scopeKota": "Kabupaten Jember"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_pa_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_pa (Jember)", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_pa (Jember)", True)
        
        # Login as admin_pa
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_pa_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_pa", False, f"Status {resp.status_code}")
            return
        admin_pa_token = resp.json().get("token")
        log_test("Login as admin_pa", True)
        
        # Test admin_pa sees only Jember items
        resp = requests.get(f"{BASE_URL}/admin/assessments", 
                           headers={"Authorization": f"Bearer {admin_pa_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_jember = all(item.get("kota") == "Kabupaten Jember" for item in items)
            if all_jember:
                log_test("admin_pa (Jember) sees only Jember items", True, 
                        f"All {len(items)} items are from Jember")
            else:
                non_jember = [item for item in items if item.get("kota") != "Kabupaten Jember"]
                log_test("admin_pa (Jember) sees only Jember items", False, 
                        f"Found {len(non_jember)} non-Jember items")
        else:
            log_test("admin_pa GET /admin/assessments", False, f"Status {resp.status_code}")
        
        # Test admin_pa cannot see Banyuwangi items even with kota filter
        resp = requests.get(f"{BASE_URL}/admin/assessments?kota=Kabupaten Banyuwangi", 
                           headers={"Authorization": f"Bearer {admin_pa_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            has_banyuwangi = any(item.get("kota") == "Kabupaten Banyuwangi" for item in items)
            if not has_banyuwangi:
                log_test("admin_pa cannot see Banyuwangi items even with kota filter", True, 
                        f"No Banyuwangi items returned (scope enforced)")
            else:
                log_test("admin_pa cannot see Banyuwangi items even with kota filter", False, 
                        "Found Banyuwangi items (scope not enforced)")
        else:
            log_test("admin_pa with kota filter", False, f"Status {resp.status_code}")
        
        # Create admin_kua (Ajung)
        admin_kua_data = {
            "name": "Admin KUA Ajung",
            "username": f"admin_kua_ajung_{timestamp}",
            "password": "pass123",
            "role": "admin_kua",
            "scopeKecamatan": "Ajung"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_kua_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_kua (Ajung)", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_kua (Ajung)", True)
        
        # Login as admin_kua
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_kua_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_kua", False, f"Status {resp.status_code}")
            return
        admin_kua_token = resp.json().get("token")
        log_test("Login as admin_kua", True)
        
        # Test admin_kua sees only Ajung kecamatan items
        resp = requests.get(f"{BASE_URL}/admin/assessments", 
                           headers={"Authorization": f"Bearer {admin_kua_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_ajung = all(item.get("kecamatan") == "Ajung" for item in items)
            if all_ajung:
                log_test("admin_kua (Ajung) sees only Ajung kecamatan items", True, 
                        f"All {len(items)} items are from Ajung kecamatan")
            else:
                non_ajung = [item for item in items if item.get("kecamatan") != "Ajung"]
                log_test("admin_kua (Ajung) sees only Ajung kecamatan items", False, 
                        f"Found {len(non_ajung)} non-Ajung items")
        else:
            log_test("admin_kua GET /admin/assessments", False, f"Status {resp.status_code}")
        
        # Create admin_mudin (Ajung kelurahan)
        admin_mudin_data = {
            "name": "Admin Mudin Ajung",
            "username": f"admin_mudin_ajung_{timestamp}",
            "password": "pass123",
            "role": "admin_mudin",
            "scopeKelurahan": "Ajung"
        }
        resp = requests.post(f"{BASE_URL}/admin/admins", json=admin_mudin_data,
                            headers={"Authorization": f"Bearer {admin_token}"}, timeout=10)
        if resp.status_code != 200:
            log_test("Create admin_mudin (Ajung)", False, f"Status {resp.status_code}")
            return
        log_test("Create admin_mudin (Ajung)", True)
        
        # Login as admin_mudin
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": admin_mudin_data["username"], "password": "pass123"},
                            timeout=10)
        if resp.status_code != 200:
            log_test("Login as admin_mudin", False, f"Status {resp.status_code}")
            return
        admin_mudin_token = resp.json().get("token")
        log_test("Login as admin_mudin", True)
        
        # Test admin_mudin sees only Ajung kelurahan items
        resp = requests.get(f"{BASE_URL}/admin/assessments", 
                           headers={"Authorization": f"Bearer {admin_mudin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            items = data.get("items", [])
            all_ajung_kel = all(item.get("kelurahan") == "Ajung" for item in items)
            if all_ajung_kel:
                log_test("admin_mudin (Ajung) sees only Ajung kelurahan items", True, 
                        f"All {len(items)} items are from Ajung kelurahan")
            else:
                non_ajung_kel = [item for item in items if item.get("kelurahan") != "Ajung"]
                log_test("admin_mudin (Ajung) sees only Ajung kelurahan items", False, 
                        f"Found {len(non_ajung_kel)} non-Ajung kelurahan items")
        else:
            log_test("admin_mudin GET /admin/assessments", False, f"Status {resp.status_code}")
        
        # Test scoped admin GET /admin/assessments/:id with Banyuwangi assessment returns 404
        banyuwangi_assessment_id = test_data["userB"]["assessments"][0]
        resp = requests.get(f"{BASE_URL}/admin/assessments/{banyuwangi_assessment_id}", 
                           headers={"Authorization": f"Bearer {admin_pa_token}"}, 
                           timeout=10)
        if resp.status_code == 404:
            log_test("Scoped admin GET /admin/assessments/:id of out-of-scope assessment returns 404", True)
        else:
            log_test("Scoped admin GET /admin/assessments/:id of out-of-scope assessment returns 404", False, 
                    f"Expected 404, got {resp.status_code}")
        
        # Test scoped admins still get 403 on other admin routes
        forbidden_routes = ["/admin/users", "/admin/instruments"]
        for route in forbidden_routes:
            resp = requests.get(f"{BASE_URL}{route}", 
                               headers={"Authorization": f"Bearer {admin_pa_token}"}, 
                               timeout=10)
            if resp.status_code == 403:
                log_test(f"Scoped admin gets 403 on {route}", True)
            else:
                log_test(f"Scoped admin gets 403 on {route}", False, 
                        f"Expected 403, got {resp.status_code}")
        
    except Exception as e:
        log_test("RBAC & scoping test", False, f"Exception: {e}")

def test_concurrency(admin_token):
    """Test 7: Concurrency - fire parallel requests after restart"""
    print("\n" + "="*80)
    print("TEST 7: Concurrency")
    print("="*80)
    
    try:
        # Restart nextjs service
        print("Restarting nextjs service...")
        import subprocess
        result = subprocess.run(["sudo", "supervisorctl", "restart", "nextjs"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log_test("Restart nextjs service", True)
        else:
            log_test("Restart nextjs service", False, f"Exit code {result.returncode}")
        
        # Wait for service to start
        print("Waiting for service to start...")
        time.sleep(5)
        
        # Wait until port responds
        max_wait = 30
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                resp = requests.get(f"{BASE_URL}/articles", timeout=2)
                if resp.status_code in [200, 401, 403]:
                    print("Service is responding")
                    break
            except:
                pass
            time.sleep(1)
        
        # Fire ~10 parallel requests
        def make_request(endpoint):
            try:
                if endpoint == "/articles":
                    resp = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                else:
                    resp = requests.post(f"{BASE_URL}{endpoint}", 
                                       json={"username": SUPER_ADMIN_USERNAME, "password": SUPER_ADMIN_PASSWORD},
                                       timeout=10)
                return (endpoint, resp.status_code)
            except Exception as e:
                return (endpoint, f"Exception: {e}")
        
        endpoints = ["/articles", "/auth/login"] * 5
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, ep) for ep in endpoints]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Check that none returned 500
        has_500 = any(r[1] == 500 for r in results)
        if not has_500:
            log_test("Concurrency test: no 500 errors", True, 
                    f"All {len(results)} requests completed without 500 errors")
        else:
            errors_500 = [r for r in results if r[1] == 500]
            log_test("Concurrency test: no 500 errors", False, 
                    f"Found {len(errors_500)} requests with 500 errors")
        
        # Verify no duplicate instruments
        resp = requests.get(f"{BASE_URL}/admin/instruments", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            instruments = resp.json()
            codes = [i.get("code") for i in instruments]
            unique_codes = set(codes)
            if len(codes) == len(unique_codes):
                log_test("No duplicate instruments after concurrency test", True, 
                        f"Found {len(codes)} unique instruments")
            else:
                log_test("No duplicate instruments after concurrency test", False, 
                        f"Found duplicates: {len(codes)} total, {len(unique_codes)} unique")
        else:
            log_test("GET /admin/instruments after concurrency", False, 
                    f"Status {resp.status_code}")
        
        # Verify no duplicate articles
        resp = requests.get(f"{BASE_URL}/articles", timeout=10)
        if resp.status_code == 200:
            articles = resp.json()
            titles = [a.get("title") for a in articles]
            unique_titles = set(titles)
            if len(titles) == len(unique_titles):
                log_test("No duplicate articles after concurrency test", True, 
                        f"Found {len(titles)} unique articles")
            else:
                log_test("No duplicate articles after concurrency test", False, 
                        f"Found duplicates: {len(titles)} total, {len(unique_titles)} unique")
        else:
            log_test("GET /articles after concurrency", False, 
                    f"Status {resp.status_code}")
        
    except Exception as e:
        log_test("Concurrency test", False, f"Exception: {e}")

def test_regression(admin_token):
    """Test 8: Regression - quick check of existing endpoints"""
    print("\n" + "="*80)
    print("TEST 8: Regression Quick Check")
    print("="*80)
    
    try:
        # Test GET /admin/alerts still works
        resp = requests.get(f"{BASE_URL}/admin/alerts", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            log_test("GET /admin/alerts still works", True)
        else:
            log_test("GET /admin/alerts still works", False, 
                    f"Status {resp.status_code}")
        
        # Test GET /admin/stats still works
        resp = requests.get(f"{BASE_URL}/admin/stats", 
                           headers={"Authorization": f"Bearer {admin_token}"}, 
                           timeout=10)
        if resp.status_code == 200:
            log_test("GET /admin/stats still works", True)
        else:
            log_test("GET /admin/stats still works", False, 
                    f"Status {resp.status_code}")
        
    except Exception as e:
        log_test("Regression test", False, f"Exception: {e}")

def main():
    print("="*80)
    print("NEW ASSESSMENT ENDPOINTS TEST SUITE")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Super Admin: {SUPER_ADMIN_USERNAME} / {SUPER_ADMIN_PASSWORD}")
    print("="*80)
    
    # Login as super admin
    try:
        resp = requests.post(f"{BASE_URL}/auth/login", 
                            json={"username": SUPER_ADMIN_USERNAME, "password": SUPER_ADMIN_PASSWORD},
                            timeout=30)
        if resp.status_code != 200:
            print(f"❌ Failed to login as super admin: {resp.status_code}")
            sys.exit(1)
        admin_token = resp.json().get("token")
        print(f"✅ Logged in as super admin")
    except Exception as e:
        print(f"❌ Exception during admin login: {e}")
        sys.exit(1)
    
    # Setup test data
    test_data = setup_test_data()
    if not test_data:
        print("❌ Failed to setup test data")
        sys.exit(1)
    
    # Run tests
    test_admin_assessments_list(admin_token, test_data)
    test_filters(admin_token, test_data)
    test_pagination(admin_token)
    test_assessment_detail(admin_token, test_data)
    test_assessment_accounts(admin_token)
    test_rbac_scoping(admin_token, test_data)
    test_concurrency(admin_token)
    test_regression(admin_token)
    
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
