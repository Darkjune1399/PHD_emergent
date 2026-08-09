#!/usr/bin/env python3
"""
Backend API Test for Psychological Health Assessment System
Focus: SCORING ACCURACY verification
"""
import requests
import json
from datetime import datetime, timedelta
import random
import string

# Base URL from environment
BASE_URL = "https://mental-health-hub-234.preview.emergentagent.com/api"

# Test data storage
test_data = {
    'token': None,
    'user': None,
    'members': {},
    'assessments': {}
}

def generate_unique_email():
    """Generate unique email for testing"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}_{int(datetime.now().timestamp())}@example.com"

def get_dob_for_age(target_age):
    """Calculate DOB for a target age"""
    today = datetime.now()
    dob = today - timedelta(days=target_age * 365.25)
    return dob.strftime("%Y-%m-%d")

print("=" * 80)
print("BACKEND API TESTING - PSYCHOLOGICAL HEALTH ASSESSMENT SYSTEM")
print("=" * 80)
print(f"Base URL: {BASE_URL}")
print()

# ============================================================================
# 1. AUTH TESTS
# ============================================================================
print("=" * 80)
print("1. AUTH TESTS")
print("=" * 80)

# Test 1.1: Register with unique email
print("\n[TEST 1.1] POST /auth/register - Create new user")
try:
    email = generate_unique_email()
    register_data = {
        "name": "Test User",
        "email": email,
        "password": "SecurePass123!"
    }
    response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'token' in data and 'user' in data:
            test_data['token'] = data['token']
            test_data['user'] = data['user']
            print(f"✅ PASS: User registered successfully")
            print(f"   User ID: {data['user']['id']}")
            print(f"   Email: {data['user']['email']}")
            print(f"   Token received: {data['token'][:20]}...")
        else:
            print(f"❌ FAIL: Response missing token or user")
            print(f"   Response: {data}")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 1.2: Login with correct credentials
print("\n[TEST 1.2] POST /auth/login - Login with correct password")
try:
    login_data = {
        "email": email,
        "password": "SecurePass123!"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'token' in data:
            print(f"✅ PASS: Login successful")
            print(f"   Token: {data['token'][:20]}...")
        else:
            print(f"❌ FAIL: Response missing token")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 1.3: Login with wrong password
print("\n[TEST 1.3] POST /auth/login - Login with wrong password (expect 401)")
try:
    login_data = {
        "email": email,
        "password": "WrongPassword123!"
    }
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 401:
        print(f"✅ PASS: Correctly rejected wrong password with 401")
    else:
        print(f"❌ FAIL: Expected 401, got {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 1.4: GET /auth/me with Bearer token
print("\n[TEST 1.4] GET /auth/me - With valid Bearer token")
try:
    headers = {"Authorization": f"Bearer {test_data['token']}"}
    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if 'user' in data:
            print(f"✅ PASS: User data retrieved successfully")
            print(f"   User: {data['user']['name']} ({data['user']['email']})")
        else:
            print(f"❌ FAIL: Response missing user")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 1.5: GET /auth/me without token
print("\n[TEST 1.5] GET /auth/me - Without token (expect 401)")
try:
    response = requests.get(f"{BASE_URL}/auth/me")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 401:
        print(f"✅ PASS: Correctly rejected request without token with 401")
    else:
        print(f"❌ FAIL: Expected 401, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# ============================================================================
# 2. MEMBERS + AGE ROUTING TESTS
# ============================================================================
print("\n" + "=" * 80)
print("2. MEMBERS + AGE ROUTING TESTS")
print("=" * 80)

headers = {"Authorization": f"Bearer {test_data['token']}"}

# Test 2.1: Create member age ~5 (should get sdq_parent only)
print("\n[TEST 2.1] POST /members - Age ~5 (expect sdq_parent only)")
try:
    member_data = {
        "fullName": "Child Age 5",
        "gender": "Laki-laki",
        "dob": get_dob_for_age(5),
        "relationship": "Anak"
    }
    response = requests.post(f"{BASE_URL}/members", json=member_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        test_data['members']['age5'] = data
        print(f"   Member ID: {data['id']}")
        print(f"   Age: {data['age']}")
        print(f"   Instruments: {[i['code'] for i in data['instruments']]}")
        
        if len(data['instruments']) == 1 and data['instruments'][0]['code'] == 'sdq_parent':
            print(f"✅ PASS: Age 5 correctly assigned sdq_parent only")
        else:
            print(f"❌ FAIL: Expected only sdq_parent, got {[i['code'] for i in data['instruments']]}")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 2.2: Create member age ~14 (should get sdq_self only)
print("\n[TEST 2.2] POST /members - Age ~14 (expect sdq_self only)")
try:
    member_data = {
        "fullName": "Teen Age 14",
        "gender": "Perempuan",
        "dob": get_dob_for_age(14),
        "relationship": "Anak"
    }
    response = requests.post(f"{BASE_URL}/members", json=member_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        test_data['members']['age14'] = data
        print(f"   Member ID: {data['id']}")
        print(f"   Age: {data['age']}")
        print(f"   Instruments: {[i['code'] for i in data['instruments']]}")
        
        if len(data['instruments']) == 1 and data['instruments'][0]['code'] == 'sdq_self':
            print(f"✅ PASS: Age 14 correctly assigned sdq_self only")
        else:
            print(f"❌ FAIL: Expected only sdq_self, got {[i['code'] for i in data['instruments']]}")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 2.3: Create member age ~30 (should get phq9 + ghq12)
print("\n[TEST 2.3] POST /members - Age ~30 (expect phq9 + ghq12)")
try:
    member_data = {
        "fullName": "Adult Age 30",
        "gender": "Laki-laki",
        "dob": get_dob_for_age(30),
        "relationship": "Diri Sendiri"
    }
    response = requests.post(f"{BASE_URL}/members", json=member_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        test_data['members']['age30'] = data
        print(f"   Member ID: {data['id']}")
        print(f"   Age: {data['age']}")
        print(f"   Instruments: {[i['code'] for i in data['instruments']]}")
        
        codes = [i['code'] for i in data['instruments']]
        if 'phq9' in codes and 'ghq12' in codes and len(codes) == 2:
            print(f"✅ PASS: Age 30 correctly assigned phq9 + ghq12")
        else:
            print(f"❌ FAIL: Expected phq9 + ghq12, got {codes}")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 2.4: GET /members - List all members
print("\n[TEST 2.4] GET /members - List all members")
try:
    response = requests.get(f"{BASE_URL}/members", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PASS: Retrieved {len(data)} members")
        for m in data:
            print(f"   - {m['fullName']} (age {m['age']}): {[i['code'] for i in m['instruments']]}")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# ============================================================================
# 3. QUESTIONNAIRE TESTS
# ============================================================================
print("\n" + "=" * 80)
print("3. QUESTIONNAIRE TESTS")
print("=" * 80)

# Test 3.1: GET /questionnaire/sdq_parent
print("\n[TEST 3.1] GET /questionnaire/sdq_parent - Verify structure")
try:
    response = requests.get(f"{BASE_URL}/questionnaire/sdq_parent")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        items_count = len(data['items'])
        options_count = len(data['options'])
        print(f"   Items: {items_count}")
        print(f"   Options: {options_count}")
        
        if items_count == 25 and options_count == 3:
            print(f"✅ PASS: SDQ has 25 items and 3 options")
        else:
            print(f"❌ FAIL: Expected 25 items and 3 options, got {items_count} items and {options_count} options")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 3.2: GET /questionnaire/phq9
print("\n[TEST 3.2] GET /questionnaire/phq9 - Verify structure")
try:
    response = requests.get(f"{BASE_URL}/questionnaire/phq9")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        items_count = len(data['items'])
        options_count = len(data['options'])
        print(f"   Items: {items_count}")
        print(f"   Options: {options_count}")
        
        if items_count == 9 and options_count == 4:
            print(f"✅ PASS: PHQ-9 has 9 items and 4 options")
        else:
            print(f"❌ FAIL: Expected 9 items and 4 options, got {items_count} items and {options_count} options")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 3.3: GET /questionnaire/ghq12
print("\n[TEST 3.3] GET /questionnaire/ghq12 - Verify structure")
try:
    response = requests.get(f"{BASE_URL}/questionnaire/ghq12")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        items_count = len(data['items'])
        options_count = len(data['options'])
        print(f"   Items: {items_count}")
        print(f"   Options: {options_count}")
        
        if items_count == 12 and options_count == 4:
            print(f"✅ PASS: GHQ-12 has 12 items and 4 options")
        else:
            print(f"❌ FAIL: Expected 12 items and 4 options, got {items_count} items and {options_count} options")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# ============================================================================
# 4. ASSESSMENT SCORING TESTS - SDQ
# ============================================================================
print("\n" + "=" * 80)
print("4. ASSESSMENT SCORING TESTS - SDQ (CRITICAL)")
print("=" * 80)

# Test 4.1: SDQ with all answers = 0 (verify reversed scoring)
print("\n[TEST 4.1] SDQ Scoring - All answers = 0 (verify reversed items)")
print("Expected: E=0, C=2 (item7 rev), H=4 (items21,25 rev), P=4 (items11,14 rev), Pr=0, Total=10")
try:
    # All answers = 0
    answers = {str(i): 0 for i in range(1, 26)}
    
    assessment_data = {
        "memberId": test_data['members']['age5']['id'],
        "instrumentCode": "sdq_parent",
        "answers": answers
    }
    
    response = requests.post(f"{BASE_URL}/assessments", json=assessment_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        result = data['result']
        test_data['assessments']['sdq_all_zero'] = data
        
        print(f"   Subscales: {result['subscales']}")
        print(f"   Total Difficulties: {result['totalDifficulties']}")
        print(f"   Categories: {result['categories']}")
        
        # Verify exact values
        expected = {
            'E': 0,  # Items 3,8,13,16,24 - all 0, no reversed
            'C': 2,  # Items 5,7,12,18,22 - item 7 is reversed (2-0=2), others 0
            'H': 4,  # Items 2,10,15,21,25 - items 21,25 reversed (2-0=2 each), others 0
            'P': 4,  # Items 6,11,14,19,23 - items 11,14 reversed (2-0=2 each), others 0
            'Pr': 0  # Items 1,4,9,17,20 - all 0, no reversed
        }
        expected_total = 10  # E+C+H+P = 0+2+4+4
        
        all_correct = True
        for key, expected_val in expected.items():
            actual_val = result['subscales'][key]
            if actual_val != expected_val:
                print(f"   ❌ {key}: Expected {expected_val}, got {actual_val}")
                all_correct = False
            else:
                print(f"   ✓ {key}: {actual_val} (correct)")
        
        if result['totalDifficulties'] != expected_total:
            print(f"   ❌ Total: Expected {expected_total}, got {result['totalDifficulties']}")
            all_correct = False
        else:
            print(f"   ✓ Total: {result['totalDifficulties']} (correct)")
        
        if all_correct:
            print(f"✅ PASS: SDQ reversed scoring is ACCURATE")
        else:
            print(f"❌ FAIL: SDQ scoring has errors")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# ============================================================================
# 5. ASSESSMENT SCORING TESTS - PHQ-9
# ============================================================================
print("\n" + "=" * 80)
print("5. ASSESSMENT SCORING TESTS - PHQ-9 (CRITICAL)")
print("=" * 80)

# Test 5.1: PHQ-9 with item9=2, others=0 (suicide risk)
print("\n[TEST 5.1] PHQ-9 Scoring - Item9=2, others=0 (suicide risk)")
print("Expected: item9=2, suicideRisk=true, redFlag=true, total=2, severity='Minimal'")
try:
    answers = {str(i): 0 for i in range(1, 10)}
    answers['9'] = 2
    
    assessment_data = {
        "memberId": test_data['members']['age30']['id'],
        "instrumentCode": "phq9",
        "answers": answers
    }
    
    response = requests.post(f"{BASE_URL}/assessments", json=assessment_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        result = data['result']
        test_data['assessments']['phq9_suicide'] = data
        
        print(f"   Total: {result['total']}")
        print(f"   Item9: {result['item9']}")
        print(f"   Severity: {result['severity']}")
        print(f"   Suicide Risk: {result['suicideRisk']}")
        print(f"   Red Flag: {result['redFlag']}")
        
        all_correct = True
        if result['item9'] != 2:
            print(f"   ❌ item9: Expected 2, got {result['item9']}")
            all_correct = False
        if result['suicideRisk'] != True:
            print(f"   ❌ suicideRisk: Expected true, got {result['suicideRisk']}")
            all_correct = False
        if result['redFlag'] != True:
            print(f"   ❌ redFlag: Expected true, got {result['redFlag']}")
            all_correct = False
        if result['total'] != 2:
            print(f"   ❌ total: Expected 2, got {result['total']}")
            all_correct = False
        if result['severity'] != 'Minimal':
            print(f"   ❌ severity: Expected 'Minimal', got {result['severity']}")
            all_correct = False
        
        if all_correct:
            print(f"✅ PASS: PHQ-9 suicide risk detection is ACCURATE")
        else:
            print(f"❌ FAIL: PHQ-9 suicide risk scoring has errors")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 5.2: PHQ-9 with all answers=3 (severe depression)
print("\n[TEST 5.2] PHQ-9 Scoring - All answers=3 (severe depression)")
print("Expected: total=27, severity='Berat', redFlag=true")
try:
    answers = {str(i): 3 for i in range(1, 10)}
    
    assessment_data = {
        "memberId": test_data['members']['age30']['id'],
        "instrumentCode": "phq9",
        "answers": answers
    }
    
    response = requests.post(f"{BASE_URL}/assessments", json=assessment_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        result = data['result']
        test_data['assessments']['phq9_severe'] = data
        
        print(f"   Total: {result['total']}")
        print(f"   Severity: {result['severity']}")
        print(f"   Red Flag: {result['redFlag']}")
        
        all_correct = True
        if result['total'] != 27:
            print(f"   ❌ total: Expected 27, got {result['total']}")
            all_correct = False
        if result['severity'] != 'Berat':
            print(f"   ❌ severity: Expected 'Berat', got {result['severity']}")
            all_correct = False
        if result['redFlag'] != True:
            print(f"   ❌ redFlag: Expected true, got {result['redFlag']}")
            all_correct = False
        
        if all_correct:
            print(f"✅ PASS: PHQ-9 severe depression scoring is ACCURATE")
        else:
            print(f"❌ FAIL: PHQ-9 severe depression scoring has errors")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# ============================================================================
# 6. ASSESSMENT SCORING TESTS - GHQ-12
# ============================================================================
print("\n" + "=" * 80)
print("6. ASSESSMENT SCORING TESTS - GHQ-12 (CRITICAL)")
print("=" * 80)

# Test 6.1: GHQ-12 with all answers=2 (psychological distress)
print("\n[TEST 6.1] GHQ-12 Scoring - All answers=2 (distress)")
print("Expected: total=24 (>=18), overallCategory='Indikasi Masalah Psikologis', redFlag=true")
try:
    answers = {str(i): 2 for i in range(1, 13)}
    
    assessment_data = {
        "memberId": test_data['members']['age30']['id'],
        "instrumentCode": "ghq12",
        "answers": answers
    }
    
    response = requests.post(f"{BASE_URL}/assessments", json=assessment_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        result = data['result']
        test_data['assessments']['ghq12_distress'] = data
        
        print(f"   Total: {result['total']}")
        print(f"   Overall Category: {result['overallCategory']}")
        print(f"   Red Flag: {result['redFlag']}")
        
        all_correct = True
        if result['total'] != 24:
            print(f"   ❌ total: Expected 24, got {result['total']}")
            all_correct = False
        if result['overallCategory'] != 'Indikasi Masalah Psikologis':
            print(f"   ❌ overallCategory: Expected 'Indikasi Masalah Psikologis', got {result['overallCategory']}")
            all_correct = False
        if result['redFlag'] != True:
            print(f"   ❌ redFlag: Expected true, got {result['redFlag']}")
            all_correct = False
        
        if all_correct:
            print(f"✅ PASS: GHQ-12 distress detection is ACCURATE")
        else:
            print(f"❌ FAIL: GHQ-12 distress scoring has errors")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 6.2: GHQ-12 with all answers=1 (normal)
print("\n[TEST 6.2] GHQ-12 Scoring - All answers=1 (normal)")
print("Expected: total=12 (<18), overallCategory='Normal', redFlag=false")
try:
    answers = {str(i): 1 for i in range(1, 13)}
    
    assessment_data = {
        "memberId": test_data['members']['age30']['id'],
        "instrumentCode": "ghq12",
        "answers": answers
    }
    
    response = requests.post(f"{BASE_URL}/assessments", json=assessment_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        result = data['result']
        test_data['assessments']['ghq12_normal'] = data
        
        print(f"   Total: {result['total']}")
        print(f"   Overall Category: {result['overallCategory']}")
        print(f"   Red Flag: {result['redFlag']}")
        
        all_correct = True
        if result['total'] != 12:
            print(f"   ❌ total: Expected 12, got {result['total']}")
            all_correct = False
        if result['overallCategory'] != 'Normal':
            print(f"   ❌ overallCategory: Expected 'Normal', got {result['overallCategory']}")
            all_correct = False
        if result['redFlag'] != False:
            print(f"   ❌ redFlag: Expected false, got {result['redFlag']}")
            all_correct = False
        
        if all_correct:
            print(f"✅ PASS: GHQ-12 normal scoring is ACCURATE")
        else:
            print(f"❌ FAIL: GHQ-12 normal scoring has errors")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# ============================================================================
# 7. ASSESSMENT HISTORY TESTS
# ============================================================================
print("\n" + "=" * 80)
print("7. ASSESSMENT HISTORY TESTS")
print("=" * 80)

# Test 7.1: GET /assessments with memberId filter
print("\n[TEST 7.1] GET /assessments?memberId=... - Filter by member")
try:
    member_id = test_data['members']['age30']['id']
    response = requests.get(f"{BASE_URL}/assessments?memberId={member_id}", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PASS: Retrieved {len(data)} assessments for member")
        for a in data:
            print(f"   - {a['instrumentCode']}: {a['result']['overallCategory']}")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 7.2: GET /assessments - All assessments
print("\n[TEST 7.2] GET /assessments - All assessments")
try:
    response = requests.get(f"{BASE_URL}/assessments", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PASS: Retrieved {len(data)} total assessments")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# Test 7.3: GET /assessments/:id - Single assessment
print("\n[TEST 7.3] GET /assessments/:id - Single assessment")
try:
    assessment_id = test_data['assessments']['phq9_suicide']['id']
    response = requests.get(f"{BASE_URL}/assessments/{assessment_id}", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PASS: Retrieved single assessment")
        print(f"   Instrument: {data['instrumentCode']}")
        print(f"   Result: {data['result']['overallCategory']}")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# ============================================================================
# 8. REFERRALS TEST
# ============================================================================
print("\n" + "=" * 80)
print("8. REFERRALS TEST")
print("=" * 80)

print("\n[TEST 8.1] GET /referrals - Emergency contacts")
try:
    response = requests.get(f"{BASE_URL}/referrals")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ PASS: Retrieved {len(data)} referral contacts")
        for r in data:
            print(f"   - {r['name']}: {r['contact']}")
    else:
        print(f"❌ FAIL: Expected 200, got {response.status_code}")
except Exception as e:
    print(f"❌ FAIL: Exception - {str(e)}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("\nAll backend API tests completed.")
print("Review the results above for any failures marked with ❌")
print("\nCritical scoring tests:")
print("  - SDQ reversed scoring (items 7,11,14,21,25)")
print("  - PHQ-9 suicide risk detection (item9>0)")
print("  - GHQ-12 threshold detection (total>=18)")
print("\nIf all tests show ✅ PASS, the backend is working correctly.")
print("=" * 80)
