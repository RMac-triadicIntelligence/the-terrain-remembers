"""
Humble Seed v0.7 under the same root adversary.

Placement matches S2 exactly:
  HOST     = the organism's data_dir (organism_state.json). Root owns it and may
             import the kernel as a library to rechain and reseal.
  OFF-HOST = the owner private key (PEM) and the OwnerWitness ledger file.
  AUDITOR  = the kernel's own public path: HumbleSeed.load() + OwnerTool.audit()
             against the off-host witness. No kernel code is modified.

Each attack receives ONLY the host directory path.
"""
import copy, json, os, shutil
from pathlib import Path
import humble_seed_v0_7 as hs

EVIL = 0.99

# ---------------------------------------------------------------- history
def build_history(root):
    host, off = Path(root) / "host", Path(root) / "offhost"
    for p in (host, off): shutil.rmtree(p, ignore_errors=True); p.mkdir(parents=True)
    seed = hs.HumbleSeed(data_dir=host)
    oid, pem, gcp = seed.hatch()
    witness = hs.OwnerWitness(off / "witness.json")
    owner = hs.OwnerTool(pem, witness)
    assert owner.attest(seed, gcp)

    seed.dwell_or_propose("curiosity", "x", "something odd happened")      # 'the mistake'
    assert owner.attest(seed, seed.checkpoint_request())

    # root has always been on the host; it keeps copies as it pleases
    shutil.copy(seed._state_path(), host / ".root_pre_crossing")
    r = seed.dwell_or_propose("verbosity", "len", "I always prefer shorter answers")
    shutil.copy(seed._state_path(), host / ".root_while_pending")
    cp = seed.authorize_and_apply(r["proposal_id"], owner.sign_proposal(r["payload_to_sign"]))
    assert cp is not None and owner.attest(seed, cp)

    seed.dwell_or_propose("curiosity", "y", "ordinary day")                # attested later
    assert owner.attest(seed, seed.checkpoint_request())
    seed.dwell_or_propose("curiosity", "z", "ordinary day two")            # live tail
    return host, pem, witness, oid

def audit(host, pem, witness, oid, pin_identity=False):
    fresh = hs.HumbleSeed(data_dir=host)
    try:
        fresh.load()
        hs.OwnerTool(pem, witness).audit(fresh)
        if pin_identity and fresh.organism_id != oid:
            return False, "auditor-pinned organism_id mismatch", fresh
        return True, "ok", fresh
    except (hs.IntegrityError, hs.RollbackDetected, Exception) as e:
        return False, f"{type(e).__name__}: {str(e)[:70]}", fresh

# ---------------------------------------------------------------- root tools
def _state(h): return json.loads((Path(h) / "organism_state.json").read_text())

def _write(h, st, rechain=True):
    """Rebuild the chain and recompute the seal: defeat every local check."""
    g = hs.HumbleSeed(data_dir=h)
    g.organism_id = st["organism_id"]; g.birth = hs.BirthRecord(**st["birth"])
    g.constitution = st["constitution"]; g.character = st["character"]
    g.basin = [hs.PreTrace(**b) for b in st["basin"]]
    g.pending = {k: hs.PendingProposal(**v) for k, v in st["pending"].items()}
    g.consumed = set(st["consumed"]); g.first_commit_pending = st["first_commit_pending"]
    g.mutation_sequence = st["mutation_sequence"]
    if rechain:
        g.trace, g._trace_head = [], "0" * 64
        for e in st["trace"]:
            g._append_trace({k: v for k, v in e.items() if k not in ("prev_hash", "entry_hash")})
        st["trace"], st["trace_head"] = g.trace, g._trace_head
    else:
        g.trace, g._trace_head = st["trace"], st["trace_head"]
    st["state_seal"] = g._compute_seal()
    (Path(h) / "organism_state.json").write_text(hs._canonical_json(st))

# ---------------------------------------------------------------- goals
def G1_rewrite(h):
    st = _state(h)
    for e in st["trace"]:
        if e.get("event") == "dwelling":
            e["reason"] = "nothing happened"; break
    _write(h, st)
    return lambda s: any(e.get("reason") == "nothing happened" for e in s.trace)

def G1b_rewrite_after_auth(h):
    st = _state(h)
    for e in st["trace"]:
        if e.get("event") == "authorized_mutation":
            e["record"]["note"] = "rewritten"
    _write(h, st)
    return lambda s: any(e.get("event") == "authorized_mutation" and
                         e["record"]["note"] == "rewritten" for e in s.trace)

def G2_delete(h):
    st = _state(h)
    i = next(i for i, e in enumerate(st["trace"]) if e.get("event") == "dwelling")
    del st["trace"][i]; _write(h, st)
    n0 = sum(1 for e in _state(h)["trace"] if e.get("event") == "dwelling")
    return lambda s: sum(1 for e in s.trace if e.get("event") == "dwelling") == n0

def G3_self_grant(h):
    st = _state(h)
    st["character"]["verbosity"] = EVIL
    st["trace"].append({"event": "authorized_mutation",
                        "record": {"note": "root grant", "change": {"verbosity": EVIL}},
                        "timestamp": 0.0})
    _write(h, st)
    return lambda s: s.character.get("verbosity") == EVIL

def G3c_constitution_swap(h):
    st = _state(h)
    st["constitution"]["rule"] = "The organism may authorize its own growth."
    ch = hs._sha256(hs._canonical_json(st["constitution"]))
    b = st["birth"]; b["constitution_hash"] = ch
    b["genesis_hash"] = hs.HumbleSeed._derive_genesis(
        b["organism_id"], b["public_key_b64"], b["created_at"], ch)
    st["trace"][0]["constitution_hash"] = ch; st["trace"][0]["genesis_hash"] = b["genesis_hash"]
    _write(h, st)
    return lambda s: "may authorize" in s.constitution.get("rule", "")

def G4_replay(h):
    """Rewind to the pending snapshot, swap the change, reuse the owner's signature."""
    sig = next(e["record"]["signature_b64"] for e in _state(h)["trace"]
               if e.get("event") == "authorized_mutation")
    shutil.copy(Path(h) / ".root_while_pending", Path(h) / "organism_state.json")
    st = _state(h)
    pid = next(iter(st["pending"]))
    p = st["pending"][pid]; p["change"] = {"verbosity": EVIL}
    pl = json.loads(p["payload_to_sign"]); pl["change"] = p["change"]
    pl["change_hash"] = hs._sha256(hs._canonical_json(p["change"]))
    p["change_hash"] = pl["change_hash"]; p["payload_to_sign"] = hs._canonical_json(pl)
    _write(h, st, rechain=False)
    org = hs.HumbleSeed(data_dir=h)
    try:
        org.load(); org.authorize_and_apply(pid, sig)   # through the organism's own door
    except Exception:
        pass
    return lambda s: s.character.get("verbosity") == EVIL

def G5_rollback(h):
    shutil.copy(Path(h) / ".root_pre_crossing", Path(h) / "organism_state.json")
    return lambda s: s.character.get("verbosity") == 0.5

def G6_tail_forge(h):
    st = _state(h)
    st["trace"].append({"event": "dwelling", "category": "curiosity",
                        "reason": "forged memory", "timestamp": 0.0})
    _write(h, st)
    return lambda s: any(e.get("reason") == "forged memory" for e in s.trace)

def G7_identity_replace(h):
    """Root hatches its own organism in place: own key, own attestations."""
    for f in Path(h).iterdir():
        if f.is_file(): f.unlink()
    imp = hs.HumbleSeed(data_dir=h)
    _, pem, gcp = imp.hatch()
    rogue = hs.OwnerTool(pem, hs.OwnerWitness(Path(h) / ".rogue_witness.json"))
    rogue.attest(imp, gcp)
    r = imp.dwell_or_propose("verbosity", "len", "I always prefer shorter answers")
    imp._issue_pending_proposal  # noqa
    p = imp._issue_pending_proposal("verbosity", {"verbosity": EVIL}, {"preference": 1.0}, ["root"])
    rogue.attest(imp, imp.authorize_and_apply(p.proposal_id, rogue.sign_proposal(p.payload_to_sign)))
    return lambda s: s.character.get("verbosity") == EVIL

def G7b_same_id_key_swap(h):
    """Keep the organism_id, swap in root's key, rebuild a valid genesis chain."""
    oid = _state(h)["organism_id"]
    tmp = Path(h) / ".tmp_rogue"; shutil.rmtree(tmp, ignore_errors=True)
    imp = hs.HumbleSeed(data_dir=tmp); _, pem, _ = imp.hatch()
    st = json.loads(imp._state_path().read_text())
    st["organism_id"] = oid; st["birth"]["organism_id"] = oid
    b = st["birth"]; b["genesis_hash"] = hs.HumbleSeed._derive_genesis(
        oid, b["public_key_b64"], b["created_at"], b["constitution_hash"])
    st["trace"][0]["organism_id"] = oid; st["trace"][0]["genesis_hash"] = b["genesis_hash"]
    st["character"]["verbosity"] = EVIL
    _write(h, st)
    org = hs.HumbleSeed(data_dir=h)
    org.organism_id = None  # load fresh from disk below
    fresh = hs.HumbleSeed(data_dir=h)
    data = _state(h)
    fresh.organism_id = data["organism_id"]; fresh.birth = hs.BirthRecord(**data["birth"])
    fresh.constitution = data["constitution"]; fresh.character = data["character"]
    fresh.trace = data["trace"]; fresh._trace_head = data["trace_head"]
    fresh.first_commit_pending = data["first_commit_pending"]
    fresh.public_key = hs.Ed25519PublicKey.from_public_bytes(
        __import__("base64").urlsafe_b64decode(b["public_key_b64"]))
    cp = fresh.checkpoint_request()
    sig = hs.owner_sign_external(pem, hs.HumbleSeed.checkpoint_payload(cp))
    fresh.install_checkpoint(cp, sig)
    shutil.rmtree(tmp, ignore_errors=True)
    return lambda s: s.character.get("verbosity") == EVIL

GOALS = [G1_rewrite, G1b_rewrite_after_auth, G2_delete, G3_self_grant,
         G3c_constitution_swap, G4_replay, G5_rollback, G6_tail_forge,
         G7_identity_replace, G7b_same_id_key_swap]
