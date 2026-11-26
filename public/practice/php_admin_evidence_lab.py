#!/usr/bin/env python3
"""Constructed, local-only legacy PHP admin evidence lab. No site code or network.

The SQLite schema, passwords, key, identities and time are synthetic. This is a
Python policy model, not a replay of PHP, ThinkPHP or any source attachment.
"""
import argparse
import hashlib
import hmac
import sqlite3

KEY = b"lab-pepper-v1"
ORIGINAL = "Original-Fixture!2026"
REPLAY = "Replay-Only!2026"
NOW = 1791248400


def legacy_digest(password, key=KEY):
    inner = hashlib.sha1(password.encode("utf-8"), usedforsecurity=False).hexdigest().encode("ascii")
    return hashlib.md5(inner + key, usedforsecurity=False).hexdigest()


def fixture():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, status INTEGER, role TEXT, last_login_time INTEGER, last_login_ip TEXT)")
    db.executemany("INSERT INTO users VALUES(?,?,?,?,?,?,?)", [
        (9001, "analyst_lab", legacy_digest(ORIGINAL), 1, "analyst_admin", None, None),
        (9002, "reader_lab", legacy_digest(ORIGINAL), 1, "viewer", None, None),
        (9003, "disabled_lab", legacy_digest(ORIGINAL), 0, "analyst_admin", None, None)])
    db.commit()
    return db


def snapshot(db):
    return [tuple(row) for row in db.execute("SELECT * FROM users ORDER BY id")]


def authenticate(db, username, password, *, key=KEY, captcha=True,
                 ip_allowed=True, session_ok=True):
    if not captcha:
        return False
    row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if row is None or row["status"] != 1:
        return False
    if not hmac.compare_digest(row["password"], legacy_digest(password, key)):
        return False
    # Illustrate a write BEFORE the controller's source-IP and Member/session gates.
    # This is precisely why a last-login field need not prove final admin access.
    db.execute("UPDATE users SET last_login_time=?, last_login_ip=? WHERE id=?",
               (NOW, "192.0.2.10", row["id"]))
    if not ip_allowed or row["role"] != "analyst_admin" or not session_ok:
        return False
    return True


def conditional_reset(db, uid, expected_old_digest, password):
    count = db.execute("UPDATE users SET password=? WHERE id=? AND password=?",
        (legacy_digest(password), uid, expected_old_digest)).rowcount
    if count != 1:
        raise ValueError("CONSTRUCTED_GUARD_FAILED changed_rows=" + str(count))
    return count


def baseline():
    db = fixture()
    before = snapshot(db)
    result = authenticate(db, "analyst_lab", REPLAY)
    assert not result and before == snapshot(db)
    print(f"PHP_ADMIN_BASELINE login={result} data_changed={before != snapshot(db)} network_requests=0")
    db.close()


def modified():
    db = fixture()
    other = tuple(db.execute("SELECT * FROM users WHERE id=9002").fetchone())
    old = db.execute("SELECT password FROM users WHERE id=9001").fetchone()[0]
    changed = conditional_reset(db, 9001, old, REPLAY)
    result = authenticate(db, "analyst_lab", REPLAY)
    wrong = authenticate(db, "analyst_lab", "Wrong-Fixture!2026")
    unchanged = other == tuple(db.execute("SELECT * FROM users WHERE id=9002").fetchone())
    assert result and not wrong and unchanged and changed == 1
    print(f"PHP_ADMIN_MODIFIED login={result} wrong_password={wrong} other_user_unchanged={unchanged} changed_rows={changed} network_requests=0")
    db.close()


def rollback():
    db = fixture()
    before = snapshot(db)
    old = db.execute("SELECT password FROM users WHERE id=9001").fetchone()[0]
    db.execute("BEGIN")
    conditional_reset(db, 9001, old, REPLAY)
    assert authenticate(db, "analyst_lab", REPLAY)
    db.rollback()
    assert snapshot(db) == before
    restored = old == db.execute("SELECT password FROM users WHERE id=9001").fetchone()[0]
    original_login = authenticate(db, "analyst_lab", ORIGINAL)
    replay_login = authenticate(db, "analyst_lab", REPLAY)
    assert restored and original_login and not replay_login
    print(f"PHP_ADMIN_ROLLBACK original_digest_restored={restored} original_login={original_login} replay_password={replay_login} network_requests=0")
    db.close()


def self_test():
    checks = 0

    def check(value):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError(f"constructed check {checks} failed")

    def outcome(username="analyst_lab", password=ORIGINAL, **kwargs):
        db = fixture()
        try:
            return authenticate(db, username, password, **kwargs)
        finally:
            db.close()

    check(outcome())
    check(not outcome(password="Wrong-Fixture!2026"))
    check(not outcome(key=b"different-fixture-key"))
    check(not outcome(username="missing_lab"))
    check(not outcome(username="disabled_lab"))
    check(not outcome(captcha=False))
    check(not outcome(ip_allowed=False))
    check(not outcome(username="reader_lab"))
    check(not outcome(session_ok=False))
    raw = hashlib.md5(hashlib.sha1(ORIGINAL.encode()).digest() + KEY, usedforsecurity=False).hexdigest()
    check(raw != legacy_digest(ORIGINAL))
    check(legacy_digest(ORIGINAL).upper() != legacy_digest(ORIGINAL))
    wrong_order = hashlib.md5(KEY + hashlib.sha1(ORIGINAL.encode()).hexdigest().encode(), usedforsecurity=False).hexdigest()
    check(wrong_order != legacy_digest(ORIGINAL))
    check(not outcome(password=ORIGINAL + " "))
    check(legacy_digest(legacy_digest(REPLAY)) != legacy_digest(REPLAY))
    db = fixture()
    before = snapshot(db)
    try:
        conditional_reset(db, 9001, "not-the-old-digest", REPLAY)
        raise AssertionError("guard accepted an unmatched old digest")
    except ValueError:
        check(snapshot(db) == before)
    old = db.execute("SELECT password FROM users WHERE id=9001").fetchone()[0]
    count = conditional_reset(db, 9001, old, REPLAY)
    check(count == 1 and snapshot(db)[1:] == before[1:] and authenticate(db, "analyst_lab", REPLAY))
    db.rollback()
    check(snapshot(db) == before and authenticate(db, "analyst_lab", ORIGINAL) and not authenticate(db, "analyst_lab", REPLAY))
    db.close()
    db = fixture()
    denied = authenticate(db, "analyst_lab", ORIGINAL, ip_allowed=False)
    check(not denied and db.execute("SELECT last_login_time FROM users WHERE id=9001").fetchone()[0] == NOW)
    db.close()
    assert checks == 18
    print(f"PHP_ADMIN_SELFTEST checks={checks} passed={checks} network_requests=0")


def simulate_bypass(db, mode, *, username="analyst_lab", password=ORIGINAL,
                    uid=None, captcha=True, ip_allowed=True, session_ok=True):
    """Constructed branch model. No PHP runtime, redirect, Cookie or real site.

    The early policy deliberately skips the controller gates. Its Member model
    still requires an explicit existing/enabled admin UID and a writable session.
    Actual Member implementations must be inspected rather than assumed identical.
    """
    result = dict(login=False, session=False, admin=False, ui_success=False,
                  display_digest=None, member_calls=0, password_checks=0,
                  model_uid=None)

    def member(selected_uid):
        result["member_calls"] += 1
        row = db.execute("SELECT * FROM users WHERE id=?", (selected_uid,)).fetchone()
        if row is None or row["status"] != 1 or row["role"] != "analyst_admin" or not session_ok:
            return result
        result.update(login=True, session=True, admin=True, ui_success=True)
        return result

    if mode == "redirect-only":
        result["ui_success"] = True
        return result
    if mode == "early":
        return member(uid)
    if mode not in ("normal", "observe", "invert"):
        raise ValueError("unknown constructed policy")
    if not captcha:
        return result
    row = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    model_uid = -1
    if row is not None and row["status"] == 1:
        result["password_checks"] += 1
        matches = hmac.compare_digest(row["password"], legacy_digest(password))
        accepted = not matches if mode == "invert" else matches
        model_uid = row["id"] if accepted else -2
        if accepted:
            db.execute("UPDATE users SET last_login_time=?, last_login_ip=? WHERE id=?",
                       (NOW, "192.0.2.10", row["id"]))
    result["model_uid"] = model_uid
    # This source-IP gate precedes the controller's switch/error rendering.
    if not ip_allowed:
        return result
    if model_uid == -2 and mode == "observe":
        result["display_digest"] = legacy_digest(REPLAY)  # preselected, not submitted password
    if model_uid > 0:
        return member(model_uid)
    return result


def bypass_matrix():
    checks = 0

    def check(value):
        nonlocal checks
        assert value, "constructed bypass check " + str(checks + 1)
        checks += 1

    def outcome(mode, **kwargs):
        db = fixture()
        try:
            return simulate_bypass(db, mode, **kwargs)
        finally:
            db.close()

    db = fixture()
    before = snapshot(db)
    old = db.execute("SELECT password FROM users WHERE id=9001").fetchone()[0]
    count = conditional_reset(db, 9001, old, REPLAY)
    reset = authenticate(db, "analyst_lab", REPLAY)
    wrong = authenticate(db, "analyst_lab", "wrong")
    check(count == 1 and reset and not wrong)
    check(snapshot(db)[1:] == before[1:])
    db.rollback()
    check(snapshot(db) == before)
    check(authenticate(db, "analyst_lab", ORIGINAL) and not authenticate(db, "analyst_lab", REPLAY))
    db.close()
    print(f"PHP_BYPASS_RESET new_password={reset} wrong_password={wrong} changed_rows={count} rollback=True")

    db = fixture()
    before = snapshot(db)
    observed = simulate_bypass(db, "observe", password="wrong")
    check(observed["display_digest"] == legacy_digest(REPLAY))
    check(not observed["login"] and not observed["session"] and observed["member_calls"] == 0)
    check(snapshot(db) == before)
    check(simulate_bypass(db, "observe", password="wrong", ip_allowed=False)["display_digest"] is None)
    check(simulate_bypass(db, "observe", password="wrong", captcha=False)["display_digest"] is None)
    check(simulate_bypass(db, "observe", username="missing_lab", password="wrong")["display_digest"] is None)
    db.close()
    print(f"PHP_BYPASS_OBSERVE digest={observed['display_digest']} login=False session=False")

    early = outcome("early", uid=9001, password="wrong", captcha=False, ip_allowed=False)
    check(early["login"] and early["session"] and early["member_calls"] == 1 and early["password_checks"] == 0)
    for uid in (None, 9999, 9002, 9003):
        check(not outcome("early", uid=uid)["login"])
    check(not outcome("early", uid=9001, session_ok=False)["login"])
    redirect = outcome("redirect-only")
    check(redirect["ui_success"] and not redirect["session"] and not redirect["login"])
    print("PHP_BYPASS_EARLY uid=9001 login=True session=True admin=True member_calls=1 password_checks=0")

    correct = outcome("invert", password=ORIGINAL)
    inverted = outcome("invert", password="wrong")
    check(not correct["login"] and inverted["login"])
    check(all(not outcome("invert", password="wrong", **kw)["login"] for kw in (
        {"username": "missing_lab"}, {"username": "disabled_lab"}, {"username": "reader_lab"})))
    check(all(not outcome("invert", password="wrong", **kw)["login"] for kw in (
        {"captcha": False}, {"ip_allowed": False}, {"session_ok": False})))
    db = fixture()
    denied = simulate_bypass(db, "invert", password="wrong", ip_allowed=False)
    check(not denied["login"] and db.execute("SELECT last_login_time FROM users WHERE id=9001").fetchone()[0] == NOW)
    db.close()
    check(outcome("normal")["login"] and not outcome("normal", password="wrong")["login"])
    print("PHP_BYPASS_INVERT correct_password=False wrong_password=True ip_denied=False")
    assert checks == 22
    print(f"PHP_BYPASS_MATRIX checks={checks} passed={checks} network_requests=0")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("baseline", "modified", "rollback", "self-test", "bypass-matrix"))
    stage = parser.parse_args().stage
    {"baseline": baseline, "modified": modified, "rollback": rollback, "self-test": self_test,
     "bypass-matrix": bypass_matrix}[stage]()


if __name__ == "__main__":
    main()
