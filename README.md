# Slack Channel Membership Bot

Build a small Slack bot where a **channel owner** can request to **add or remove a member** through one simple form.
The bot **checks the requester really owns the channel**, makes the change, tells the requester, and saves a **permanent audit record**.

![Final demo](docs/screenshots/03-owner-submit-visible.png)

---

## Contents
1. [How it works](#1-how-it-works)
2. [What the demo includes (and what it does not)](#2-what-the-demo-includes-and-what-it-does-not)
3. [Part A: Set up Slack](#part-a-set-up-slack-steps-1-5)
4. [Part B: Build the bot](#part-b-build-the-bot-steps-6-11)
5. [Part C: Run the full demo](#part-c-run-the-full-demo-step-12)
6. [Part D: Publish on GitHub](#part-d-publish-on-github-step-13)
7. [Troubleshooting](#troubleshooting)

---

## 1. How it works

Think of a clubhouse with a door guard:

1. You open the form with `/access`.
2. You choose **add or remove**, the **channel**, the **person**, and write a **reason**.
3. The guard (the bot) checks that **you own that channel**.
4. If yes, the door opens (Slack is updated). If no, nothing changes.
5. Either way, the result is written in a diary that **cannot be erased**.

```mermaid
flowchart LR
    A[User types /access] --> B[Fills the form]
    B --> C{Channel picked:<br/>is requester the owner?}
    C -- No --> D[Submit hidden]
    C -- Yes --> E[Submit appears]
    E --> F{Server re-checks<br/>owner + reason filled?}
    F -- No --> G[DENIED: logged, requester told]
    F -- Yes --> H[Slack adds or removes member]
    H --> I[Save audit record + message requester]
```

## 2. What the demo includes (and what it does not)

| Feature | Full proposal | This free-plan demo |
|---|---|---|
| Request form in Slack | Yes | **Yes** (`/access`) |
| Mandatory business reason | Yes | **Yes** |
| Owner check on the server (fail-closed) | Yes | **Yes** |
| Submit only for owners | Yes | **Yes** (button is hidden) |
| Add / remove member | Yes | **Yes** |
| Append-only audit log | Yes | **Yes** (SQLite) |
| Result message to requester (+ optional audit channel) | Yes | **Yes** |
| Jira tickets, email alerts, retry queue | Yes | Not in demo (Phase 3) |
| Guests / Slack Connect rules | Yes | Not in demo |

**How "owner" is decided in the demo:** the person who **created the channel**, or anyone listed in `OWNER_ALLOWLIST`
(a stand-in for workspace admins). Slack's separate *Channel Manager* role may not be available on free workspaces, so the demo does not depend on it.
In production, map this rule to your real definition (creator vs. manager vs. admin).

**About "grayed out":** Slack modals cannot show a *disabled* Submit button. The demo hides Submit until the bot confirms you own the selected channel,
and the **server checks again on submit**, so the hidden button is never the only protection.

**Free-plan limits:** on a free workspace you can view the last 90 days of messages and add up to 10 third-party or custom apps. Enough for this demo.
Check Slack's "Usage limits for free workspaces" page if anything has changed.

**You need:** a free Slack workspace, Python 3.9+, Git, a free GitHub account, and a **second Slack account** (another email) to show the "not an owner" case.

---

# Part A: Set up Slack (Steps 1 to 5)

## Step 1: Create (or choose) a free workspace
Go to https://slack.com, create a free workspace (slack-integration-lab.slack.com), and sign in as **shruti@shrsa.onmicrosoft.com**.
<img width="953" height="468" alt="image" src="https://github.com/user-attachments/assets/ef25f8ba-ed46-406a-90d1-ee55ccebf632" />

## Step 2: Invite a second person
Invite **Account B** (another email) to the workspace. You will use it for the "denied" demo.

## Step 3: Create the Slack app from a manifest
1. Open https://api.slack.com/apps and click **Create New App**.
2. Choose **From an app manifest** and pick your free workspace.<img width="1919" height="942" alt="image" src="https://github.com/user-attachments/assets/2e45a368-f27b-42fb-b3a8-22701e288baf" />
3. Paste this YAML (also saved as `manifest.yml`), click **Next**, then **Create**.

```yaml
display_information:
  name: Access Bot
  description: Request to add or remove channel members, with owner checks and an audit log
features:
  bot_user:
    display_name: Access Bot
    always_online: true
  slash_commands:
    - command: /access
      description: Request to add or remove a channel member
      should_escape: false
oauth_config:
  scopes:
    bot:
      - commands
      - chat:write
      - channels:read
      - channels:manage
      - groups:read
      - groups:write
settings:
  interactivity:
    is_enabled: true
  org_deploy_enabled: false
  socket_mode_enabled: true
  token_rotation_enabled: false
```

This creates the bot user, the `/access` command, the permissions, and **Socket Mode** (so you need **no public URL and no ngrok**).

<img width="1809" height="914" alt="image" src="https://github.com/user-attachments/assets/4c97d1a5-0275-4fde-b1c2-45640c13b160" />


## Step 4: Create the app-level token
1. In your app, open **Basic Information** and scroll to **App-Level Tokens**. <img width="1742" height="971" alt="image" src="https://github.com/user-attachments/assets/8eff7df7-f105-4cbf-b39e-2a6398451f5d" />
2. Click **Generate Token and Scopes**, name it `socket`, add the scope **`connections:write`**, then **Generate**. <img width="478" height="370" alt="image" src="https://github.com/user-attachments/assets/e3250e13-0021-4495-a85e-9869b080c75f" /> <img width="470" height="363" alt="image" src="https://github.com/user-attachments/assets/90fbd45f-0220-4602-9c27-6739ccd9c947" />  <img width="967" height="453" alt="image" src="https://github.com/user-attachments/assets/122002e5-1236-4e4e-b226-483f43d89e03" />
3. Copy the token (starts with `xapp-`). Keep it private. <img width="943" height="459" alt="image" src="https://github.com/user-attachments/assets/08ab6fab-2ede-432a-93dc-d6559f4b7d9f" />


## Step 5: Install the app and copy the bot token
1. Open **Install App**, click **Install to Workspace**, then **Allow**. <img width="1805" height="630" alt="image" src="https://github.com/user-attachments/assets/ab1b8446-f944-45df-909b-3f43e4a11ad7" />
2. Copy the **Bot User OAuth Token** (starts with `xoxb-`). Keep it private.
<img width="951" height="451" alt="image" src="https://github.com/user-attachments/assets/b3117628-1890-476a-a11c-53798e8761e3" />


---

# Part B: Build the bot (Steps 6 to 11)

## Step 6: Create the project
```bash
mkdir slack-channel-membership-bot
cd slack-channel-membership-bot
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

Create `requirements.txt`:
```
slack_bolt>=1.18
python-dotenv>=1.0
```
```bash
pip install -r requirements.txt
```

Create `.gitignore` (keeps secrets and the database out of GitHub):
```
.env
*.db
__pycache__/
.venv/
```

Create `.env.example` (a template that is safe to publish):
```
# Copy to .env and fill in. NEVER commit .env
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-level-token
# Optional: comma-separated Slack user IDs treated as owners of every channel (stand-in for workspace admins)
OWNER_ALLOWLIST=
# Optional: channel ID where every result is also posted (e.g. #access-audit)
AUDIT_CHANNEL_ID=
AUDIT_DB=audit.db
# Demo only: set to 1 to show Submit to everyone (proves the server-side DENIED path). Keep 0 normally.
DEMO_FORCE_SUBMIT=0
```

Now create your real secrets file and paste the two tokens from Steps 4 and 5:
```bash
cp .env.example .env
```
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
```

## Step 7: Write `logic.py` (the brain)
`logic.py` holds the three important ideas. Create the file and add the four blocks below **in order**.

**7a. Imports and settings**
```python
"""Core logic for the demo: owner check, audit log, and the request form (modal)."""
import os
import sqlite3
from datetime import datetime, timezone

# Demo-only switch: show Submit to everyone so you can prove the SERVER still denies non-owners.
DEMO_FORCE_SUBMIT = os.getenv("DEMO_FORCE_SUBMIT") == "1"
OWNER_ALLOWLIST = {u.strip() for u in os.getenv("OWNER_ALLOWLIST", "").split(",") if u.strip()}
```

**7b. The audit log:** a diary that can only be added to. Database triggers refuse edits and deletes.
```python
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
```

**7c. The owner check:** *fail-closed*. If the bot is not sure, the answer is no.
```python
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
```

**7d. The request form:** the Submit button only exists when `allowed` is true.
```python
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
```

**Check it offline (no Slack needed).** Run this to prove the rules work:
```bash
python - <<'PY'
import os, sqlite3, tempfile
os.environ["OWNER_ALLOWLIST"] = "UADMIN"
import logic

class FakeSlack:
    def __init__(self, creator=None, fail=False): self.c, self.f = creator, fail
    def conversations_info(self, channel):
        if self.f: raise RuntimeError("api down")
        return {"channel": {"creator": self.c}}

assert logic.is_owner(FakeSlack("U1"), "U1", "C1") is True      # creator is owner
assert logic.is_owner(FakeSlack("U1"), "U2", "C1") is False     # someone else is not
assert logic.is_owner(FakeSlack(fail=True), "U1", "C1") is False  # fail-closed
assert "submit" not in logic.build_modal(allowed=False)         # hidden for non-owner
assert "submit" in logic.build_modal(allowed=True)              # shown for owner

db = tempfile.mktemp(); logic.init_db(db)
logic.log_event(db, "REQ-1", "U1", "add", "C1", "U2", "why", "APPROVED", "ok")
try: sqlite3.connect(db).execute("DELETE FROM audit"); print("FAILED")
except sqlite3.IntegrityError: print("all checks passed")
PY
```
> Screenshot to take: `11-offline-tests.png` (terminal showing `all checks passed`).

## Step 8: Write `app.py` part 1: open the form
This connects to Slack and opens the form when someone types `/access`. (Some imports are used in later steps.)

```python
"""Slack Channel Membership Bot: free-plan demo (Bolt for Python + Socket Mode)."""
import logging
import os
import uuid

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError

load_dotenv()
import logic  # noqa: E402  (after load_dotenv so OWNER_ALLOWLIST is read)

logging.basicConfig(level=logging.INFO)
DB_PATH = os.getenv("AUDIT_DB", "audit.db")
AUDIT_CHANNEL_ID = os.getenv("AUDIT_CHANNEL_ID", "").strip()
app = App(token=os.environ["SLACK_BOT_TOKEN"])


def read_form(view):
    v = view["state"]["values"]
    return {
        "action": v["action_b"]["action_a"]["selected_option"]["value"],
        "channel": v["channel_b"]["channel_a"].get("selected_conversation"),
        "user": v["member_b"]["member_a"].get("selected_user"),
        "reason": (v["reason_b"]["reason_a"].get("value") or "").strip(),
    }

@app.command("/access")
def open_form(ack, body, client):
    ack()
    client.views_open(trigger_id=body["trigger_id"], view=logic.build_modal())

if __name__ == "__main__":
    logic.init_db(DB_PATH)
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```

**Run it:**
```bash
python app.py
```
**Check:** in Slack type `/access`. The form opens with **no Submit button** and a hint that Submit appears only for owners.

> Screenshots to take: `01-slash-command.png` (typing `/access`) and `02-form-no-channel.png` (the empty form).

## Step 9: Add `app.py` part 2: show or hide Submit
Stop the bot (`Ctrl+C`). **Paste this above the `if __name__ == "__main__":` line** in `app.py`:

```python
@app.action("channel_a")
def on_channel_selected(ack, body, client):
    """When a channel is picked: check ownership, then show or hide the Submit button."""
    ack()
    view, form = body["view"], read_form(body["view"])
    allowed = logic.is_owner(client, body["user"]["id"], form["channel"]) if form["channel"] else None
    client.views_update(
        view_id=view["id"],
        view=logic.build_modal(form["action"], form["channel"], form["user"], form["reason"], allowed),
    )
```

Start the bot again (`python app.py`).

**Prepare a test channel first:**
1. As **Account A**, create `#project-apollo` (you become its owner in this demo).
2. In it, type `/invite @Access Bot` so the bot can add and remove members.
3. Optional: create `#access-audit`, invite the bot, copy its Channel ID (channel name, then **About**), and set `AUDIT_CHANNEL_ID` in `.env`.

**Check:** type `/access`, pick `#project-apollo`. A green check appears **and Submit shows up**.
Now switch to a channel you did not create: Submit **disappears** again.

> Screenshots to take: `03-owner-submit-visible.png` (owner sees Submit).

## Step 10: Add `app.py` part 3: handle the submission
Stop the bot. **Paste this above the `if __name__ == "__main__":` line**, below the block from Step 9:

```python
@app.view("membership_modal")
def on_submit(ack, body, client, view):
    form, requester = read_form(view), body["user"]["id"]
    if not form["reason"]:
        ack(response_action="errors", errors={"reason_b": "A business justification is required."})
        return
    ack()

    req_id = "REQ-" + uuid.uuid4().hex[:6].upper()
    verb = "add" if form["action"] == "add" else "remove"

    # Server-side re-check: never trust the form alone.
    if not logic.is_owner(client, requester, form["channel"]):
        status, detail = "DENIED", "Requester is not a channel owner"
    else:
        try:
            if form["action"] == "add":
                client.conversations_invite(channel=form["channel"], users=form["user"])
            else:
                client.conversations_kick(channel=form["channel"], user=form["user"])
            status, detail = "APPROVED", ("Member added" if verb == "add" else "Member removed")
        except SlackApiError as e:
            status, detail = "FAILED", e.response.get("error", "slack_api_error")

    logic.log_event(DB_PATH, req_id, requester, form["action"], form["channel"],
                    form["user"], form["reason"], status, detail)

    text = (f"*{status}*  `{req_id}`\n"
            f"Request to {verb} <@{form['user']}> in <#{form['channel']}> by <@{requester}>.\n"
            f"Reason: {form['reason']}\nResult: {detail}")
    client.chat_postMessage(channel=requester, text=text)
    if AUDIT_CHANNEL_ID:
        client.chat_postMessage(channel=AUDIT_CHANNEL_ID, text=text)
```

What it does, in order: requires a **reason**, **re-checks ownership on the server**, adds or removes the member, **writes the audit record**, then messages the requester (and the audit channel if set).

Your finished `app.py` is: Step 8 code, with the Step 9 block and the Step 10 block inserted above the last `if __name__` lines.

Start the bot again.

**Check:**
1. Open `/access`, pick `#project-apollo`, pick Account B, leave the reason **empty**, press Submit. You get: *"A business justification is required."*
2. Write a reason and press Submit. The bot sends you a DM saying **APPROVED** with a request ID, and Account B is now in the channel.

> Screenshots to take: `05-missing-reason-error.png`, `06-approved-dm.png`, `09-member-added.png`.

## Step 11: Look at the audit log
```bash
sqlite3 audit.db "select ts, request_id, requester, action, channel, target, status, detail from audit;"
```
No `sqlite3` installed? Use:
```bash
python -c "import sqlite3;[print(r) for r in sqlite3.connect('audit.db').execute('select * from audit')]"
```
Try to cheat the diary. It refuses:
```bash
sqlite3 audit.db "delete from audit;"
# Error: audit log is append-only
```
> Screenshot to take: `08-audit-log.png`.

---

# Part C: Run the full demo (Step 12)

## Step 12: Show the "not an owner" cases

**12a. Non-owner sees no Submit.** Sign in as **Account B**, type `/access`, pick `#project-apollo` (Account A created it).
You see a red "not an owner" note and **no Submit button**.
> Screenshot: `04-non-owner-no-submit.png`.

**12b. Prove the server also says no.** The hidden button is only the first guard. To see the second guard:
1. In `.env` set `DEMO_FORCE_SUBMIT=1` and restart `python app.py`. Submit now shows for everyone.
2. As **Account B**, fill the form for `#project-apollo` and press Submit.
3. The bot replies **DENIED** ("Requester is not a channel owner"). Nothing changes in the channel, and the audit log records it.
4. Set `DEMO_FORCE_SUBMIT=0` again and restart. This switch is for demos only.

> Screenshot: `07-denied-dm.png`.

### Screenshot checklist

| File | What it shows |
|---|---|
| `01-slash-command.png` | Typing `/access` |
| `02-form-no-channel.png` | Empty form, no Submit |
| `03-owner-submit-visible.png` | Owner picks channel, Submit appears |
| `04-non-owner-no-submit.png` | Non-owner, red note, no Submit |
| `05-missing-reason-error.png` | Reason is required |
| `06-approved-dm.png` | APPROVED message |
| `07-denied-dm.png` | DENIED message |
| `08-audit-log.png` | Audit table |
| `09-member-added.png` | Member added in channel |
| `10-app-created.png` | Slack app page |
| `11-offline-tests.png` | Offline tests passed |

Hide or crop anything private (tokens, personal emails) before saving.

---

# Part D: Publish on GitHub (Step 13)

## Step 13: Push to a free GitHub repository
1. On https://github.com click **New repository**, name it `slack-channel-membership-bot`, choose **Public**, and **do not** tick "Add a README" (you already have files).
2. Save this guide as `README.md` in your project folder, and put screenshots in `docs/screenshots/` using the names above.
3. **Check no secrets will be uploaded:**
   ```bash
   git init
   git add .
   git status
   ```
   The list must **not** contain `.env`, `audit.db` or `.venv`. If it does, fix `.gitignore` and run `git rm --cached <file>`.
4. Commit and push:
   ```bash
   git commit -m "Slack channel membership bot demo"
   git branch -M main
   git remote add origin https://github.com/<your-username>/slack-channel-membership-bot.git
   git push -u origin main
   ```
5. On GitHub, click **Add file, Create new file**, name it `LICENSE`, and use the **Choose a license template** button (MIT is a common choice).
6. Optional: add topics like `slack-bot`, `python`, `bolt`, `access-management` in the repo's **About** box.

If you ever commit a token by mistake, **revoke it in your Slack app settings immediately**; deleting the commit is not enough.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `/access` says `dispatch_failed` or does nothing | Is `python app.py` running? Check both tokens in `.env`. |
| `KeyError: SLACK_BOT_TOKEN` | `.env` is missing (Step 6). |
| Result says **FAILED** with `not_in_channel` | Run `/invite @Access Bot` in that channel. |
| **FAILED** with `cant_invite_self`, `cant_kick_self` or `cant_kick_from_general` | Slack does not allow that action. Pick another person or channel. |
| Submit never appears on a channel you created | Someone else may have created it. Add your user ID to `OWNER_ALLOWLIST` (profile, **More**, **Copy member ID**) and restart. |
| Changed scopes but nothing changes | Reinstall the app (Install App, **Reinstall to Workspace**) and update the bot token. |

## Security notes
- Tokens live only in `.env` (git-ignored).
- **Fail-closed:** if the bot cannot confirm ownership, the answer is **no**.
- Permissions are limited to what the demo needs.
- The audit database blocks `UPDATE` and `DELETE` with database triggers.

## Roadmap (from the proposal)
1. **Phase 1:** Confirm owner rule, channel types, guest policy.
2. **Phase 2:** MVP (this demo, hardened).
3. **Phase 3:** Jira tickets, email alerts, retry queue, monitoring.
4. **Phase 4:** Security review, pilot channels, production rollout.
