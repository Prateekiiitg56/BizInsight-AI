from tests.conftest import upload

CSV = (
    "Review,other\n"
    '"Absolutely love this product, works great!",x\n'
    '"Terrible quality, it broke after one day.",y\n'
    '"Delivery was late and the box was damaged.",z\n'
    '"It is a phone case.",w\n'
)


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_register_login_and_me(client, make_user):
    user = make_user()
    res = client.post("/api/auth/login", json={"username": user["username"], "password": "password123"})
    assert res.status_code == 200
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {res.json()['token']}"})
    assert me.json()["username"] == user["username"]


def test_login_errors_do_not_reveal_which_field_was_wrong(client, make_user):
    user = make_user()
    wrong_pw = client.post("/api/auth/login", json={"username": user["username"], "password": "nope"})
    no_user = client.post("/api/auth/login", json={"username": "ghost", "password": "nope"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json()["detail"] == no_user.json()["detail"]


def test_register_validation(client):
    base = {"username": "valid_name", "email": "a@b.co", "password": "password123", "confirm_password": "password123"}
    assert client.post("/api/auth/register", json={**base, "password": "short", "confirm_password": "short"}).status_code == 400
    assert client.post("/api/auth/register", json={**base, "confirm_password": "different1"}).status_code == 400
    assert client.post("/api/auth/register", json={**base, "email": "not-an-email"}).status_code == 400
    assert client.post("/api/auth/register", json={**base, "username": "a b"}).status_code == 400


def test_duplicate_username_is_rejected(client, make_user):
    user = make_user()
    res = client.post(
        "/api/auth/register",
        json={"username": user["username"], "email": "other@example.com", "password": "password123", "confirm_password": "password123"},
    )
    assert res.status_code == 409


def test_google_only_account_password_login_fails_cleanly(client):
    from database import create_google_user

    assert create_google_user("googler", "googler@example.com") is True
    res = client.post("/api/auth/login", json={"username": "googler", "password": "anything"})
    assert res.status_code == 401


def test_protected_routes_require_auth(client):
    for path in ["/api/dashboard/summary", "/api/dashboard/alerts", "/api/reviews", "/api/reviews/export", "/api/auth/me"]:
        assert client.get(path).status_code in (401, 403), path
    bad = {"Authorization": "Bearer not-a-jwt"}
    assert client.get("/api/dashboard/summary", headers=bad).status_code == 401


def test_upload_scores_and_summarizes(client, make_user):
    user = make_user()
    res = upload(client, user, CSV)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total_processed"] == 4
    assert body["positive"] >= 1 and body["negative"] >= 2
    assert body["positive"] + body["negative"] + body["neutral"] == 4

    summary = client.get("/api/dashboard/summary", headers=user["headers"]).json()
    assert summary["total_reviews"] == 4
    assert summary["trend"] and summary["top_keywords"]

    alerts = client.get("/api/dashboard/alerts", headers=user["headers"]).json()
    assert alerts["risk_level"] == "high"
    assert alerts["threshold"] == 40.0


def test_upload_rejects_bad_files(client, make_user):
    user = make_user()
    assert upload(client, user, "a,b\n1,2\n").status_code == 400  # no review column
    assert upload(client, user, "review\n\n").status_code == 400  # no rows
    assert upload(client, user, "", filename="x.csv").status_code == 400  # empty
    assert upload(client, user, CSV, filename="reviews.txt").status_code == 400  # wrong type


def test_upload_accepts_latin1(client, make_user):
    user = make_user()
    res = upload(client, user, "review\nCaf\xe9 was great\n".encode("latin-1"))
    assert res.status_code == 200


def test_reviews_are_isolated_between_users(client, make_user):
    alice, bob = make_user(), make_user()
    upload(client, alice, CSV)
    assert client.get("/api/reviews", headers=bob["headers"]).json()["total"] == 0
    assert client.get("/api/dashboard/summary", headers=bob["headers"]).json()["total_reviews"] == 0
    assert client.get("/api/reviews/export", headers=bob["headers"]).status_code == 404


def test_pagination_and_export(client, make_user):
    user = make_user()
    upload(client, user, CSV)
    page = client.get("/api/reviews?page=2&page_size=3", headers=user["headers"]).json()
    assert page["total"] == 4 and len(page["reviews"]) == 1

    export = client.get("/api/reviews/export", headers=user["headers"])
    assert export.status_code == 200
    assert export.text.splitlines()[0] == "review,sentiment,date"
    assert len(export.text.strip().splitlines()) == 5


def test_clear_only_removes_own_reviews(client, make_user):
    alice, bob = make_user(), make_user()
    upload(client, alice, CSV)
    upload(client, bob, CSV)
    assert client.delete("/api/admin/reviews", headers=alice["headers"]).status_code == 200
    assert client.get("/api/reviews", headers=alice["headers"]).json()["total"] == 0
    assert client.get("/api/reviews", headers=bob["headers"]).json()["total"] == 4


def test_clustering_needs_enough_reviews(client, make_user):
    user = make_user()
    upload(client, user, CSV)
    res = client.post("/api/clustering/run", json={"mode": "negative"}, headers=user["headers"])
    assert res.status_code == 400
    assert client.post("/api/clustering/run", json={"mode": "bogus"}, headers=user["headers"]).status_code == 422


def test_clustering_jobs_are_private(client, make_user):
    import time
    from bizinsight_api.routes import clustering

    owner, other = make_user(), make_user()
    clustering._jobs["job-1"] = {
        "user_id": owner["id"], "status": "running", "message": "", "result": None, "created_at": time.time(),
    }
    assert client.get("/api/clustering/status/job-1", headers=owner["headers"]).status_code == 200
    assert client.get("/api/clustering/status/job-1", headers=other["headers"]).status_code == 404
    assert client.get("/api/clustering/status/job-1").status_code in (401, 403)


def test_admin_routes(client, make_user):
    from database import get_user_by_username
    from bizinsight_api.routes.auth import create_token

    regular, target = make_user(), make_user()
    assert client.get("/api/admin/users", headers=regular["headers"]).status_code == 403

    admin = get_user_by_username(regular["username"]) | {"role": "admin"}
    headers = {"Authorization": f"Bearer {create_token(admin)}"}
    users = client.get("/api/admin/users", headers=headers).json()["users"]
    assert any(u["username"] == target["username"] for u in users)
    assert client.delete(f"/api/admin/users/{admin['id']}", headers=headers).status_code == 400
    assert client.delete(f"/api/admin/users/{target['id']}", headers=headers).status_code == 200


def test_vector_sync_is_incremental_and_scoped(client, make_user):
    from rag_api.indexing import sync_user_reviews
    from rag_api.vector_store import get_vector_store_manager

    alice, bob = make_user(), make_user()
    upload(client, alice, CSV)
    upload(client, bob, CSV)
    vsm = get_vector_store_manager()

    sync_user_reviews(alice["id"])
    assert sync_user_reviews(alice["id"]) == 0  # nothing new → nothing re-embedded
    assert vsm.count_documents(alice["id"]) == 4

    upload(client, alice, "review\nBrand new review text\n")
    sync_user_reviews(alice["id"])  # the upload's background sync may already have added it
    assert vsm.count_documents(alice["id"]) == 5
    assert sync_user_reviews(alice["id"]) == 0

    client.delete("/api/admin/reviews", headers=alice["headers"])
    assert vsm.count_documents(alice["id"]) == 0
    sync_user_reviews(bob["id"])
    assert vsm.count_documents(bob["id"]) == 4
