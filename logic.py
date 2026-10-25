"""Core logic for the demo: owner check, audit log, and the request form (modal)."""
import os
import sqlite3
from datetime import datetime, timezone

# Demo-only switch: show Submit to everyone so you can prove the SERVER still denies non-owners.
DEMO_FORCE_SUBMIT = os.getenv("DEMO_FORCE_SUBMIT") == "1"
OWNER_ALLOWLIST = {u.strip() for u in os.getenv("OWNER_ALLOWLIST", "").split(",") if u.strip()}


# ---------- Audit log (append-only) ----------
def init_db(path):
    con = sqlite3.connect(path)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            request_id TEXT NOT NULL,
            requester TEXT NOT NULL,
            action TEXT NOT NULL,
            channel TEXT NOT NULL,
            target TEXT NOT NULL,
            reason TEXT NOT NULL,
            status TEXT NOT NULL,
            detail TEXT NOT NULL
        );
        CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit
        BEGIN SELECT RAISE(ABORT, 'audit log is append-only'); END;
        CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit
        BEGIN SELECT RAISE(ABORT, 'audit log is append-only'); END;
        """
    )
    con.commit()
    con.close()


def log_event(path, request_id, requester, action, channel, target, reason, status, detail):
    con = sqlite3.connect(path)
    con.execute(
        "INSERT INTO audit (ts, request_id, requester, action, channel, target, reason, status, detail)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(timespec="seconds"), request_id, requester,
         action, channel, target, reason, status, detail),
    )
    con.commit()
    con.close()


# ---------- Authorization (fail-closed) ----------
def is_owner(client, user_id, channel_id):
    """True only if we can PROVE the user owns the channel. Any doubt means False."""
    if user_id in OWNER_ALLOWLIST:
        return True
    try:
        info = client.conversations_info(channel=channel_id)
        return info["channel"].get("creator") == user_id
    except Exception:
        return False


# ---------- The request form ----------
def _opt(text, value):
    return {"text": {"type": "plain_text", "text": text}, "value": value}


def build_modal(action="add", channel=None, user=None, reason="", allowed=None):
    """Submit button exists ONLY when allowed is True (Slack modals cannot gray out Submit)."""
    add, remove = _opt("Add member", "add"), _opt("Remove member", "remove")
    channel_el = {
        "type": "conversations_select", "action_id": "channel_a",
        "placeholder": {"type": "plain_text", "text": "Choose a channel"},
        "filter": {"include": ["public", "private"], "exclude_bot_users": True,
                   "exclude_external_shared_channels": True},
    }
    if channel:
        channel_el["initial_conversation"] = channel
    user_el = {"type": "users_select", "action_id": "member_a",
               "placeholder": {"type": "plain_text", "text": "Choose a person"}}
    if user:
        user_el["initial_user"] = user
    reason_el = {"type": "plain_text_input", "action_id": "reason_a", "multiline": True}
    if reason:
        reason_el["initial_value"] = reason

    if allowed is None:
        status = "Pick a channel. *Submit* appears only if you are its owner."
    elif allowed:
        status = ":white_check_mark: You are an owner of this channel. You can submit."
    else:
        status = ":no_entry: You are not an owner of this channel, so *Submit* is hidden."

    label = lambda t: {"type": "plain_text", "text": t}
    view = {
        "type": "modal", "callback_id": "membership_modal",
        "title": label("Membership Request"), "close": label("Cancel"),
        "blocks": [
            {"type": "input", "block_id": "action_b", "label": label("Action"),
             "element": {"type": "radio_buttons", "action_id": "action_a",
                         "initial_option": remove if action == "remove" else add,
                         "options": [add, remove]}},
            {"type": "input", "block_id": "channel_b", "dispatch_action": True,
             "label": label("Channel"), "element": channel_el},
            {"type": "section", "block_id": "status_b",
             "text": {"type": "mrkdwn", "text": status}},
            {"type": "input", "block_id": "member_b", "label": label("Member"), "element": user_el},
            {"type": "input", "block_id": "reason_b",
             "label": label("Business justification (required)"), "element": reason_el},
        ],
    }
    if allowed is True or DEMO_FORCE_SUBMIT:
        view["submit"] = label("Submit")
    return view
