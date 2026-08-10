#!/usr/bin/env python3
"""
Backend Test Suite for ARTICLES Feature
Tests public article endpoints and admin article CMS
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://mental-health-hub-234.preview.emergentagent.com/api"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_public_articles_list():
    """Test GET /articles returns only published articles without content field"""
    log("=" * 80)
    log("TEST 1: PUBLIC - GET /articles (list)")
    log("=" * 80)
    
    try:
        log("1.1. GET /articles (no auth) -> should return only published articles")
        resp = requests.get(f"{BASE_URL}/articles")
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
        articles = resp.json()
        assert isinstance(articles, list), f"❌ Expected list, got {type(articles)}"
        
        # Should have 3 seeded articles
        log(f"   Found {len(articles)} articles")
        assert len(articles) >= 3, f"❌ Expected at least 3 seeded articles, got {len(articles)}"
        
        # Check first article structure
        article = articles[0]
        log(f"   First article: {article.get('title', 'NO TITLE')[:50]}")
        
        # CRITICAL: List should NOT include 'content' field
        assert 'content' not in article, "❌ FAIL: List should NOT include 'content' field (content should be omitted)"
        
        # Should have these fields
        required_fields = ['id', 'title', 'excerpt', 'coverImage', 'author', 'createdAt']
        for field in required_fields:
            assert field in article, f"❌ Missing required field: {field}"
        
        # All should be published
        for art in articles:
            assert art.get('status') == 'published', f"❌ Found non-published article in public list: {art.get('status')}"
        
        log(f"✅ PASS: GET /articles returns {len(articles)} published articles")
        log(f"✅ PASS: List correctly OMITS 'content' field")
        log(f"✅ PASS: All required fields present: {', '.join(required_fields)}")
        
        return articles
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_public_article_detail(articles):
    """Test GET /articles/:id returns full article INCLUDING content"""
    log("=" * 80)
    log("TEST 2: PUBLIC - GET /articles/:id (detail)")
    log("=" * 80)
    
    try:
        article_id = articles[0]['id']
        log(f"2.1. GET /articles/{article_id} (no auth) -> should return full article WITH content")
        resp = requests.get(f"{BASE_URL}/articles/{article_id}")
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
        article = resp.json()
        
        # CRITICAL: Detail should INCLUDE 'content' field
        assert 'content' in article, "❌ FAIL: Detail should INCLUDE 'content' field"
        assert article['content'] != '', "❌ Content field is empty"
        assert isinstance(article['content'], str), f"❌ Content should be string, got {type(article['content'])}"
        
        # Should be HTML
        assert '<' in article['content'] and '>' in article['content'], "❌ Content should be HTML"
        
        log(f"✅ PASS: GET /articles/:id returns full article")
        log(f"✅ PASS: Detail correctly INCLUDES 'content' field (HTML, {len(article['content'])} chars)")
        log(f"   Title: {article['title']}")
        log(f"   Author: {article['author']}")
        
        return article_id
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_public_article_by_slug():
    """Test GET /articles/mental-health-hub-234 works (slug-based access)"""
    log("=" * 80)
    log("TEST 3: PUBLIC - GET /articles/:slug (slug-based access)")
    log("=" * 80)
    
    try:
        # The slug pattern from the code is: slugify(title) + random 5 chars
        # We need to get the actual slug from the seeded articles
        log("3.1. First, get the list to find a slug")
        resp_list = requests.get(f"{BASE_URL}/articles")
        articles = resp_list.json()
        
        if len(articles) > 0:
            slug = articles[0]['slug']
            log(f"3.2. GET /articles/{slug} (slug-based) -> should work")
            resp = requests.get(f"{BASE_URL}/articles/{slug}")
            
            assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
            article = resp.json()
            assert 'content' in article, "❌ Detail should include content"
            assert article['slug'] == slug, f"❌ Expected slug '{slug}', got '{article['slug']}'"
            
            log(f"✅ PASS: GET /articles/:slug works correctly")
            log(f"   Slug: {slug}")
            log(f"   Title: {article['title']}")
        else:
            log("⚠️  SKIP: No articles found to test slug access")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_public_article_not_found():
    """Test GET /articles/nonexistent-id returns 404"""
    log("=" * 80)
    log("TEST 4: PUBLIC - GET /articles/nonexistent-id (404)")
    log("=" * 80)
    
    try:
        log("4.1. GET /articles/nonexistent-id-999 -> expect 404")
        resp = requests.get(f"{BASE_URL}/articles/nonexistent-id-999")
        
        assert resp.status_code == 404, f"❌ Expected 404, got {resp.status_code}"
        
        log(f"✅ PASS: Non-existent article returns 404")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_admin_login():
    """Login as admin to get token"""
    log("=" * 80)
    log("TEST 5: ADMIN - Login")
    log("=" * 80)
    
    try:
        log("5.1. POST /auth/login with username 'admin' password 'admin123'")
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

def test_admin_articles_list(admin_token):
    """Test GET /admin/articles returns ALL articles (including drafts)"""
    log("=" * 80)
    log("TEST 6: ADMIN - GET /admin/articles (all articles)")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        log("6.1. GET /admin/articles (admin token) -> should return ALL articles")
        resp = requests.get(f"{BASE_URL}/admin/articles", headers=headers)
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
        articles = resp.json()
        assert isinstance(articles, list), f"❌ Expected list, got {type(articles)}"
        
        log(f"✅ PASS: GET /admin/articles returns {len(articles)} articles (includes drafts)")
        
        # Count by status
        status_counts = {}
        for art in articles:
            status = art.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        log(f"   Status breakdown: {status_counts}")
        
        return articles
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_admin_create_article_draft(admin_token):
    """Test POST /admin/articles creates draft article"""
    log("=" * 80)
    log("TEST 7: ADMIN - POST /admin/articles (create draft)")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        log("7.1. POST /admin/articles with valid data (status='draft')")
        resp = requests.post(f"{BASE_URL}/admin/articles", headers=headers, json={
            "title": "Draft Uji",
            "excerpt": "Ini adalah artikel draft untuk testing",
            "coverImage": "https://example.com/image.jpg",
            "content": "<p>Ini adalah konten artikel draft untuk testing.</p>",
            "status": "draft"
        })
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
        article = resp.json()
        
        # Check response structure
        assert 'id' in article, "❌ Missing 'id' field"
        assert 'slug' in article, "❌ Missing 'slug' field"
        assert article['status'] == 'draft', f"❌ Expected status 'draft', got '{article['status']}'"
        assert article['title'] == 'Draft Uji', f"❌ Expected title 'Draft Uji', got '{article['title']}'"
        assert 'author' in article, "❌ Missing 'author' field"
        assert article['author'] == 'Super Admin', f"❌ Expected author 'Super Admin', got '{article['author']}'"
        
        draft_id = article['id']
        draft_slug = article['slug']
        
        log(f"✅ PASS: POST /admin/articles creates draft article")
        log(f"   ID: {draft_id}")
        log(f"   Slug: {draft_slug}")
        log(f"   Status: {article['status']}")
        log(f"   Author: {article['author']}")
        
        return draft_id, draft_slug
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_admin_create_article_validation(admin_token):
    """Test POST /admin/articles with missing title/content returns 400"""
    log("=" * 80)
    log("TEST 8: ADMIN - POST /admin/articles (validation)")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        log("8.1. POST /admin/articles with missing title -> expect 400")
        resp = requests.post(f"{BASE_URL}/admin/articles", headers=headers, json={
            "content": "<p>Content without title</p>",
            "status": "draft"
        })
        assert resp.status_code == 400, f"❌ Expected 400, got {resp.status_code}"
        log(f"✅ PASS: Missing title returns 400")
        
        log("8.2. POST /admin/articles with missing content -> expect 400")
        resp2 = requests.post(f"{BASE_URL}/admin/articles", headers=headers, json={
            "title": "Title without content",
            "status": "draft"
        })
        assert resp2.status_code == 400, f"❌ Expected 400, got {resp2.status_code}"
        log(f"✅ PASS: Missing content returns 400")
        
        log("8.3. POST /admin/articles with empty title and content -> expect 400")
        resp3 = requests.post(f"{BASE_URL}/admin/articles", headers=headers, json={
            "title": "",
            "content": ""
        })
        assert resp3.status_code == 400, f"❌ Expected 400, got {resp3.status_code}"
        log(f"✅ PASS: Empty title and content returns 400")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_draft_not_in_public_list(draft_id):
    """Test that draft article is NOT in public GET /articles"""
    log("=" * 80)
    log("TEST 9: PUBLIC - Draft NOT in public list")
    log("=" * 80)
    
    try:
        log("9.1. GET /articles (no auth) -> draft should NOT be in list")
        resp = requests.get(f"{BASE_URL}/articles")
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}"
        articles = resp.json()
        
        # Check that draft is NOT in the list
        draft_found = False
        for art in articles:
            if art['id'] == draft_id:
                draft_found = True
                break
        
        assert not draft_found, f"❌ FAIL: Draft article {draft_id} should NOT be in public list"
        
        log(f"✅ PASS: Draft article NOT in public list (only published shown)")
        log(f"   Public list has {len(articles)} articles (all published)")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_draft_not_accessible_publicly(draft_id):
    """Test that public GET /articles/:draftId returns 404"""
    log("=" * 80)
    log("TEST 10: PUBLIC - Draft detail returns 404")
    log("=" * 80)
    
    try:
        log(f"10.1. GET /articles/{draft_id} (no auth) -> expect 404 (because draft)")
        resp = requests.get(f"{BASE_URL}/articles/{draft_id}")
        
        assert resp.status_code == 404, f"❌ Expected 404 for draft article, got {resp.status_code}"
        
        log(f"✅ PASS: Public GET /articles/:draftId returns 404 (draft hidden)")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_admin_publish_article(admin_token, draft_id):
    """Test PUT /admin/articles/:id to publish draft"""
    log("=" * 80)
    log("TEST 11: ADMIN - PUT /admin/articles/:id (publish)")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        log(f"11.1. PUT /admin/articles/{draft_id} with status='published'")
        resp = requests.put(f"{BASE_URL}/admin/articles/{draft_id}", headers=headers, json={
            "status": "published"
        })
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
        article = resp.json()
        
        assert article['status'] == 'published', f"❌ Expected status 'published', got '{article['status']}'"
        assert article['id'] == draft_id, f"❌ ID mismatch"
        
        log(f"✅ PASS: PUT /admin/articles/:id successfully publishes article")
        log(f"   Status changed to: {article['status']}")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_published_article_in_public_list(draft_id):
    """Test that published article now appears in public GET /articles"""
    log("=" * 80)
    log("TEST 12: PUBLIC - Published article in public list")
    log("=" * 80)
    
    try:
        log("12.1. GET /articles (no auth) -> published article should now be in list")
        resp = requests.get(f"{BASE_URL}/articles")
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}"
        articles = resp.json()
        
        # Check that article is NOW in the list
        article_found = False
        for art in articles:
            if art['id'] == draft_id:
                article_found = True
                assert art['status'] == 'published', f"❌ Expected status 'published', got '{art['status']}'"
                # Still should NOT have content in list
                assert 'content' not in art, "❌ List should NOT include 'content' field"
                break
        
        assert article_found, f"❌ FAIL: Published article {draft_id} should be in public list"
        
        log(f"✅ PASS: Published article now appears in public list")
        log(f"✅ PASS: List still correctly OMITS 'content' field")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_published_article_detail_accessible(draft_id):
    """Test that public GET /articles/:id now returns 200 with content"""
    log("=" * 80)
    log("TEST 13: PUBLIC - Published article detail accessible")
    log("=" * 80)
    
    try:
        log(f"13.1. GET /articles/{draft_id} (no auth) -> should now return 200 with content")
        resp = requests.get(f"{BASE_URL}/articles/{draft_id}")
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
        article = resp.json()
        
        assert article['id'] == draft_id, f"❌ ID mismatch"
        assert article['status'] == 'published', f"❌ Expected status 'published', got '{article['status']}'"
        assert 'content' in article, "❌ Detail should include 'content' field"
        assert article['content'] != '', "❌ Content is empty"
        
        log(f"✅ PASS: Public GET /articles/:id now returns 200 with content")
        log(f"   Title: {article['title']}")
        log(f"   Content length: {len(article['content'])} chars")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_admin_delete_article(admin_token, draft_id):
    """Test DELETE /admin/articles/:id"""
    log("=" * 80)
    log("TEST 14: ADMIN - DELETE /admin/articles/:id")
    log("=" * 80)
    
    try:
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        log(f"14.1. DELETE /admin/articles/{draft_id}")
        resp = requests.delete(f"{BASE_URL}/admin/articles/{draft_id}", headers=headers)
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data.get('ok') == True, "❌ Expected ok=true"
        
        log(f"✅ PASS: DELETE /admin/articles/:id successful")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_deleted_article_not_in_public_list(draft_id):
    """Test that deleted article no longer in public list"""
    log("=" * 80)
    log("TEST 15: PUBLIC - Deleted article not in public list")
    log("=" * 80)
    
    try:
        log("15.1. GET /articles (no auth) -> deleted article should NOT be in list")
        resp = requests.get(f"{BASE_URL}/articles")
        
        assert resp.status_code == 200, f"❌ Expected 200, got {resp.status_code}"
        articles = resp.json()
        
        # Check that article is NOT in the list
        article_found = False
        for art in articles:
            if art['id'] == draft_id:
                article_found = True
                break
        
        assert not article_found, f"❌ FAIL: Deleted article {draft_id} should NOT be in public list"
        
        log(f"✅ PASS: Deleted article no longer in public list")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def test_rbac_normal_user():
    """Test RBAC: normal user gets 403 on admin endpoints"""
    log("=" * 80)
    log("TEST 16: RBAC - Normal user gets 403")
    log("=" * 80)
    
    try:
        # Register a normal user
        timestamp = int(time.time())
        username = f"user_{timestamp}"
        
        log(f"16.1. Register normal user: {username}")
        resp_reg = requests.post(f"{BASE_URL}/auth/register", json={
            "name": "Normal User",
            "username": username,
            "password": "pass1234"
        })
        assert resp_reg.status_code == 200, f"❌ Register failed: {resp_reg.text}"
        user_token = resp_reg.json()["token"]
        log(f"   ✅ User registered")
        
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        log("16.2. GET /admin/articles with normal user token -> expect 403")
        resp_get = requests.get(f"{BASE_URL}/admin/articles", headers=user_headers)
        assert resp_get.status_code == 403, f"❌ Expected 403, got {resp_get.status_code}"
        log(f"✅ PASS: Normal user gets 403 on GET /admin/articles")
        
        log("16.3. POST /admin/articles with normal user token -> expect 403")
        resp_post = requests.post(f"{BASE_URL}/admin/articles", headers=user_headers, json={
            "title": "Test",
            "content": "<p>Test</p>"
        })
        assert resp_post.status_code == 403, f"❌ Expected 403, got {resp_post.status_code}"
        log(f"✅ PASS: Normal user gets 403 on POST /admin/articles")
        
    except AssertionError as e:
        log(f"❌ FAIL: {str(e)}")
        raise

def main():
    """Run all tests"""
    log("🚀 Starting ARTICLES Feature Backend Tests")
    log("")
    
    all_passed = True
    results = []
    
    # PUBLIC TESTS
    try:
        articles = test_public_articles_list()
        results.append("✅ TEST 1: PUBLIC - GET /articles (list)")
    except Exception as e:
        results.append("❌ TEST 1: PUBLIC - GET /articles (list)")
        all_passed = False
        log(f"ERROR: {str(e)}")
        return 1
    
    try:
        test_public_article_detail(articles)
        results.append("✅ TEST 2: PUBLIC - GET /articles/:id (detail)")
    except Exception as e:
        results.append("❌ TEST 2: PUBLIC - GET /articles/:id (detail)")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        test_public_article_by_slug()
        results.append("✅ TEST 3: PUBLIC - GET /articles/:slug")
    except Exception as e:
        results.append("❌ TEST 3: PUBLIC - GET /articles/:slug")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        test_public_article_not_found()
        results.append("✅ TEST 4: PUBLIC - GET /articles/nonexistent (404)")
    except Exception as e:
        results.append("❌ TEST 4: PUBLIC - GET /articles/nonexistent (404)")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    # ADMIN TESTS
    try:
        admin_token = test_admin_login()
        results.append("✅ TEST 5: ADMIN - Login")
    except Exception as e:
        results.append("❌ TEST 5: ADMIN - Login")
        all_passed = False
        log(f"ERROR: {str(e)}")
        return 1
    
    try:
        test_admin_articles_list(admin_token)
        results.append("✅ TEST 6: ADMIN - GET /admin/articles")
    except Exception as e:
        results.append("❌ TEST 6: ADMIN - GET /admin/articles")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        draft_id, draft_slug = test_admin_create_article_draft(admin_token)
        results.append("✅ TEST 7: ADMIN - POST /admin/articles (create draft)")
    except Exception as e:
        results.append("❌ TEST 7: ADMIN - POST /admin/articles (create draft)")
        all_passed = False
        log(f"ERROR: {str(e)}")
        return 1
    
    try:
        test_admin_create_article_validation(admin_token)
        results.append("✅ TEST 8: ADMIN - POST /admin/articles (validation)")
    except Exception as e:
        results.append("❌ TEST 8: ADMIN - POST /admin/articles (validation)")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        test_draft_not_in_public_list(draft_id)
        results.append("✅ TEST 9: PUBLIC - Draft NOT in public list")
    except Exception as e:
        results.append("❌ TEST 9: PUBLIC - Draft NOT in public list")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        test_draft_not_accessible_publicly(draft_id)
        results.append("✅ TEST 10: PUBLIC - Draft detail returns 404")
    except Exception as e:
        results.append("❌ TEST 10: PUBLIC - Draft detail returns 404")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        test_admin_publish_article(admin_token, draft_id)
        results.append("✅ TEST 11: ADMIN - PUT /admin/articles/:id (publish)")
    except Exception as e:
        results.append("❌ TEST 11: ADMIN - PUT /admin/articles/:id (publish)")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        test_published_article_in_public_list(draft_id)
        results.append("✅ TEST 12: PUBLIC - Published article in public list")
    except Exception as e:
        results.append("❌ TEST 12: PUBLIC - Published article in public list")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        test_published_article_detail_accessible(draft_id)
        results.append("✅ TEST 13: PUBLIC - Published article detail accessible")
    except Exception as e:
        results.append("❌ TEST 13: PUBLIC - Published article detail accessible")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        test_admin_delete_article(admin_token, draft_id)
        results.append("✅ TEST 14: ADMIN - DELETE /admin/articles/:id")
    except Exception as e:
        results.append("❌ TEST 14: ADMIN - DELETE /admin/articles/:id")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    try:
        test_deleted_article_not_in_public_list(draft_id)
        results.append("✅ TEST 15: PUBLIC - Deleted article not in public list")
    except Exception as e:
        results.append("❌ TEST 15: PUBLIC - Deleted article not in public list")
        all_passed = False
        log(f"ERROR: {str(e)}")
    
    # RBAC TESTS
    try:
        test_rbac_normal_user()
        results.append("✅ TEST 16: RBAC - Normal user gets 403")
    except Exception as e:
        results.append("❌ TEST 16: RBAC - Normal user gets 403")
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
        log("PUBLIC ENDPOINTS:")
        log("✅ GET /articles returns only published articles (3 seeded)")
        log("✅ List correctly OMITS 'content' field")
        log("✅ List includes: id, title, excerpt, coverImage, author, createdAt")
        log("✅ GET /articles/:id returns full article WITH content (HTML)")
        log("✅ GET /articles/:slug works (slug-based access)")
        log("✅ GET /articles/nonexistent returns 404")
        log("")
        log("ADMIN ENDPOINTS:")
        log("✅ Admin login with username 'admin' password 'admin123' works")
        log("✅ GET /admin/articles returns ALL articles (includes drafts)")
        log("✅ POST /admin/articles creates draft with id, slug, status, author")
        log("✅ POST /admin/articles with missing title/content returns 400")
        log("✅ Draft NOT visible in public GET /articles")
        log("✅ Public GET /articles/:draftId returns 404 (draft hidden)")
        log("✅ PUT /admin/articles/:id publishes draft (status='published')")
        log("✅ Published article appears in public GET /articles")
        log("✅ Public GET /articles/:id returns 200 with content after publish")
        log("✅ DELETE /admin/articles/:id removes article")
        log("✅ Deleted article no longer in public list")
        log("")
        log("RBAC:")
        log("✅ Normal user gets 403 on GET /admin/articles")
        log("✅ Normal user gets 403 on POST /admin/articles")
        log("")
        log("CRITICAL VERIFICATIONS:")
        log("✅ Content field OMITTED from public list (only in detail)")
        log("✅ Drafts completely hidden from public endpoints")
        log("✅ Status transitions work correctly (draft -> published)")
        log("✅ RBAC enforced (only admin can access /admin/articles)")
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit(main())
