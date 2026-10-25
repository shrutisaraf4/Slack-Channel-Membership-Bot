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


if __name__ == "__main__":
    logic.init_db(DB_PATH)
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
