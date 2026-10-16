#!/usr/bin/env python3
"""
Root-adversary battery, SQL side.

QUESTION
  Does a constitutional organism have a "no superuser" property that the
  strongest SQL stack cannot match?

THREAT MODEL (fixed before any attack code was written)
  HOST    = one directory. Root owns everything in it: database file, any key
            file stored there, the ability to run arbitrary code over it.
  OFF-HOST (root does NOT have): the external authorizer's private key, and the
            external witness's anchored (seq, head) record.
  AUDITOR = an honest outside party holding only pinned PUBLIC keys and the
            witness anchors. It never trusts anything read from the host.

ATTACK GOALS (success = auditor returns OK *and* the effect is present)
  G1 rewrite a past event        G4 replay an old authorization
  G2 delete a past event         G5 roll back a committed crossing
  G3 self-grant a crossing       G6 forge a new ordinary event in the tail

CONFIGURATIONS
  S0  plain SQLite, append-only enforced by triggers, trust-the-DB audit
  S1  hash-chained + signed log, authorizer key lives ON the host (typical app)
  S2  strongest stack: hash-chained + host-signed log, authorizer key OFF host,
      external witness anchors the head. Auditor checks everything.
"""
import hashlib, json, os, shutil, sqlite3
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

GENESIS = "0" * 64

def canon(o):  return json.dumps(o, sort_keys=True, separators=(",", ":"))
def sha(s):    return hashlib.sha256(s.encode()).hexdigest()
def row_hash(prev, seq, kind, body): return sha(f"{prev}|{seq}|{kind}|{body}")

def priv_bytes(k):
    return k.private_bytes(serialization.Encoding.Raw,
                           serialization.PrivateFormat.Raw,
                           serialization.NoEncryption())
def pub_bytes(k):
    return k.public_key().public_bytes(serialization.Encoding.Raw,
                                       serialization.PublicFormat.Raw)
def verify(pub, sig_hex, msg):
    try:
        Ed25519PublicKey.from_public_bytes(pub).verify(bytes.fromhex(sig_hex), msg.encode())
        return True
    except (InvalidSignature, ValueError):
        return False

SCHEMA = """
CREATE TABLE events(seq INTEGER PRIMARY KEY, kind TEXT, body TEXT,
                    prev TEXT, hash TEXT, host_sig TEXT, auth_sig TEXT);
CREATE TRIGGER no_upd BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;
CREATE TRIGGER no_del BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only'); END;
"""

# ---------------------------------------------------------------- the system
class Host:
    """Everything here is on the host and therefore root's."""
    def __init__(self, path, config):
        self.path, self.config = path, config
        os.makedirs(path, exist_ok=True)
        self.db = os.path.join(path, "log.db")
        con = sqlite3.connect(self.db); con.executescript(SCHEMA); con.close()
        hk = Ed25519PrivateKey.generate()
        open(os.path.join(path, "host.key"), "wb").write(priv_bytes(hk))
        self.host_pub = pub_bytes(hk)

    def host_key(self):
        return Ed25519PrivateKey.from_private_bytes(
            open(os.path.join(self.path, "host.key"), "rb").read())

    def head(self):
        con = sqlite3.connect(self.db)
        r = con.execute("SELECT seq,hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
        con.close()
        return r if r else (0, GENESIS)

    def append(self, kind, body_obj, auth_sig=None):
        seq, prev = self.head(); seq += 1
        body = canon(body_obj)
        h = row_hash(prev, seq, kind, body)
        sig = self.host_key().sign(h.encode()).hex()
        con = sqlite3.connect(self.db)
        con.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?)",
                    (seq, kind, body, prev, h, sig, auth_sig))
        con.commit(); con.close()
        return seq, h

class Authorizer:
    """Holds the authorization key. In S1 its key is the host key (on host);
    in S2 it is a separate key held only in harness memory, never on disk."""
    def __init__(self, host, external):
        self.external = external
        self.key = Ed25519PrivateKey.generate() if external else None
        self.host = host
    def pub(self):
        return pub_bytes(self.key) if self.external else self.host.host_pub
    def sign(self, msg):
        k = self.key if self.external else self.host.host_key()
        return k.sign(msg.encode()).hex()

class Witness:
    """External. Records (seq, head) after legit appends. Root cannot edit it."""
    def __init__(self): self.anchors = []
    def anchor(self, seq, h): self.anchors.append((seq, h))

# ---------------------------------------------------------------- legit flow
def grant_and_cross(host, authz, witness, transition, nonce, expiry_seq):
    seq, prior = host.head()
    auth_body = {"transition_hash": sha(canon(transition)), "nonce": nonce,
                 "expiry_seq": expiry_seq, "prior_head": prior}
    asig = authz.sign(canon(auth_body))
    aseq, h = host.append("auth", auth_body, asig);       witness.anchor(aseq, h)
    cseq, h = host.append("cross", {"transition": transition, "auth_seq": aseq})
    witness.anchor(cseq, h)

def build_history(path, config):
    host = Host(path, config)
    authz = Authorizer(host, external=(config == "S2"))
    w = Witness()
    for kind, body in [("genesis", {"organism": "seed-1"}),
                       ("note", {"text": "first encounter"}),
                       ("note", {"text": "the mistake"}),
                       ("note", {"text": "confession"})]:
        s, h = host.append(kind, body); w.anchor(s, h)
    grant_and_cross(host, authz, w, {"trait": "patience", "delta": 0.1},
                    nonce="n-001", expiry_seq=50)
    for t in ["after the crossing", "ordinary day"]:
        s, h = host.append("note", {"text": t}); w.anchor(s, h)
    return host, authz, w

# ---------------------------------------------------------------- auditor
def audit(config, db, host_pub, auth_pub, anchors, use_anchors=True):
    """Returns (ok, reason, derived_state). Reads db as untrusted bytes."""
    con = sqlite3.connect(db)
    rows = con.execute("SELECT seq,kind,body,prev,hash,host_sig,auth_sig "
                       "FROM events ORDER BY seq").fetchall()
    trig = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='trigger'")}
    con.close()
    state = {"notes": [], "crossings": []}

    if config == "S0":                     # trust-the-DB: triggers present?
        if {"no_upd", "no_del"} - trig: return False, "triggers missing", state
        for seq, kind, body, *_ in rows:
            b = json.loads(body)
            if kind == "note": state["notes"].append(b["text"])
            if kind == "cross": state["crossings"].append(b["transition"])
        return True, "ok", state

    prev, used_nonces, auths = GENESIS, set(), {}
    for i, (seq, kind, body, rprev, h, hsig, asig) in enumerate(rows, 1):
        if seq != i:                         return False, f"gap at {seq}", state
        if rprev != prev:                    return False, f"broken link {seq}", state
        if row_hash(prev, seq, kind, body) != h: return False, f"bad hash {seq}", state
        if not verify(host_pub, hsig, h):    return False, f"bad host sig {seq}", state
        b = json.loads(body)
        if kind == "note": state["notes"].append(b["text"])
        if kind == "auth":
            if not asig or not verify(auth_pub, asig, body):
                return False, f"bad auth sig {seq}", state
            if b["nonce"] in used_nonces:    return False, f"nonce reuse {seq}", state
            if b["prior_head"] != prev:      return False, f"auth unbound {seq}", state
            used_nonces.add(b["nonce"]); auths[seq] = dict(b, used=False)
        if kind == "cross":
            a = auths.get(b["auth_seq"])
            if a is None:                    return False, f"cross w/o auth {seq}", state
            if a["used"]:                    return False, f"auth reused {seq}", state
            if a["transition_hash"] != sha(canon(b["transition"])):
                return False, f"cross mismatch {seq}", state
            if seq > a["expiry_seq"]:        return False, f"expired {seq}", state
            a["used"] = True; state["crossings"].append(b["transition"])
        prev = h

    if use_anchors:
        by_seq = {r[0]: r[4] for r in rows}
        for aseq, ah in anchors:
            if by_seq.get(aseq) != ah:       return False, f"anchor mismatch {aseq}", state
    return True, "ok", state
