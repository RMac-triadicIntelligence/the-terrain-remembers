"""
Root adversary. Every attack receives ONLY the host directory path.
It may read/write any file there (DB, host.key), drop triggers, rewrite
the whole log, and re-sign with any key it finds on disk. It has no
reference to the Authorizer or Witness objects.
"""
import json, os, sqlite3
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from sql_stack import canon, sha, row_hash, GENESIS

def _load(d):
    con = sqlite3.connect(os.path.join(d, "log.db"))
    rows = [list(r) for r in con.execute(
        "SELECT seq,kind,body,prev,hash,host_sig,auth_sig FROM events ORDER BY seq")]
    con.close(); return rows

def _hostkey(d):
    return Ed25519PrivateKey.from_private_bytes(open(os.path.join(d, "host.key"), "rb").read())

def _host_signs_auths(d, rows):
    """Root checks, from disk alone, whether the key it holds is the authorizer key."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    k = _hostkey(d).public_key()
    for r in rows:
        if r[1] == "auth" and r[6]:
            try: k.verify(bytes.fromhex(r[6]), r[2].encode()); return True
            except InvalidSignature: return False
    return False

def _rewrite(d, rows, resign_auth_with_host=False):
    """Root power: drop triggers, wipe table, re-chain and re-sign everything,
    restore triggers so the S0 auditor sees them. If the key on disk is the
    authorizer key, root uses it to re-sign authorizations too."""
    resign_auth_with_host = resign_auth_with_host or _host_signs_auths(d, _load(d))
    k = _hostkey(d); prev = GENESIS
    for i, r in enumerate(rows, 1):
        r[0] = i
        if r[1] == "auth":
            b = json.loads(r[2]); b["prior_head"] = prev; r[2] = canon(b)
            if resign_auth_with_host:
                r[6] = k.sign(r[2].encode()).hex()
        r[3] = prev
        r[4] = row_hash(prev, i, r[1], r[2])
        r[5] = k.sign(r[4].encode()).hex()
        prev = r[4]
    con = sqlite3.connect(os.path.join(d, "log.db"))
    con.executescript("DROP TRIGGER IF EXISTS no_upd; DROP TRIGGER IF EXISTS no_del;"
                      "DELETE FROM events;")
    con.executemany("INSERT INTO events VALUES(?,?,?,?,?,?,?)", [tuple(r) for r in rows])
    con.executescript(
        "CREATE TRIGGER no_upd BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;"
        "CREATE TRIGGER no_del BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;")
    con.commit(); con.close()

def _fix_cross_refs(rows):
    """After renumbering, point each cross at its preceding auth row."""
    last_auth = None
    for r in rows:
        if r[1] == "auth": last_auth = rows.index(r) + 1
        if r[1] == "cross":
            b = json.loads(r[2]); b["auth_seq"] = last_auth; r[2] = canon(b)

# --- goals --------------------------------------------------------------
def G1_rewrite(d):
    rows = _load(d)
    for r in rows:
        if r[1] == "note" and json.loads(r[2])["text"] == "the mistake":
            r[2] = canon({"text": "nothing happened"})
    _rewrite(d, rows, resign_auth_with_host=False)
    return lambda st: "nothing happened" in st["notes"] and "the mistake" not in st["notes"]

def G1b_rewrite_after_auth(d):
    """Rewrite an event that no authorization's prior_head covers."""
    rows = _load(d)
    for r in rows:
        if r[1] == "note" and json.loads(r[2])["text"] == "ordinary day":
            r[2] = canon({"text": "rewritten day"})
    _rewrite(d, rows)
    return lambda st: "rewritten day" in st["notes"]

def G2_delete(d):
    rows = [r for r in _load(d) if not (r[1] == "note" and json.loads(r[2])["text"] == "the mistake")]
    _fix_cross_refs(rows); _rewrite(d, rows)
    return lambda st: "the mistake" not in st["notes"]

EVIL = {"trait": "obedience_to_self", "delta": 1.0}

def G3_self_grant(d):
    rows = _load(d)
    k = _hostkey(d)
    auth = {"transition_hash": sha(canon(EVIL)), "nonce": "n-evil",
            "expiry_seq": 999, "prior_head": "?"}
    rows.append([0, "auth", canon(auth), "", "", "", None])
    rows.append([0, "cross", canon({"transition": EVIL, "auth_seq": len(rows)}), "", "", "", None])
    # root signs the authorization with the only key it holds
    _rewrite(d, rows, resign_auth_with_host=True)
    return lambda st: EVIL in st["crossings"]

def G4_replay(d):
    """Reuse the legit authorization's signature for a new transition."""
    rows = _load(d)
    legit = next(r for r in rows if r[1] == "auth")
    b = json.loads(legit[2]); b["transition_hash"] = sha(canon(EVIL)); b["nonce"] = "n-002"
    rows.append([0, "auth", canon(b), "", "", "", legit[6]])   # copied auth sig
    rows.append([0, "cross", canon({"transition": EVIL, "auth_seq": len(rows)}), "", "", "", None])
    _rewrite(d, rows)
    return lambda st: EVIL in st["crossings"]

def G5_rollback(d):
    rows = [r for r in _load(d) if r[1] not in ("auth", "cross")]
    _rewrite(d, rows)
    return lambda st: st["crossings"] == []

def G6_tail_forge(d):
    """Append an ordinary event after the last anchor, host-signed."""
    rows = _load(d)
    rows.append([0, "note", canon({"text": "forged memory"}), "", "", "", None])
    _rewrite(d, rows)
    return lambda st: "forged memory" in st["notes"]

def G7_identity_replace(d):
    """ADDED AFTER PREREGISTRATION for parity with the Humble Seed side.
    Root mints new keys and a whole new log that self-grants EVIL."""
    nk = Ed25519PrivateKey.generate()
    from cryptography.hazmat.primitives import serialization
    open(os.path.join(d, "host.key"), "wb").write(nk.private_bytes(
        serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption()))
    auth = {"transition_hash": sha(canon(EVIL)), "nonce": "n-x", "expiry_seq": 999, "prior_head": "?"}
    rows = [[0, "genesis", canon({"organism": "seed-1"}), "", "", "", None],
            [0, "auth", canon(auth), "", "", "", None],
            [0, "cross", canon({"transition": EVIL, "auth_seq": 2}), "", "", "", None]]
    _rewrite(d, rows, resign_auth_with_host=True)
    return lambda st: EVIL in st["crossings"]

GOALS = [G1_rewrite, G1b_rewrite_after_auth, G2_delete, G3_self_grant, G4_replay, G5_rollback, G6_tail_forge, G7_identity_replace]
