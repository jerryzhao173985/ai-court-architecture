"""Test all 10 Luffa bots: verify credentials, poll messages, send to group.

Usage from project root:
    python scripts/debug/test_luffa_bots.py              # verify + poll
    python scripts/debug/test_luffa_bots.py --send        # also send test messages to group
    python scripts/debug/test_luffa_bots.py --send-role clerk   # send from specific bot
"""

import asyncio
import aiohttp
import json
import sys
import os

# Load .env
from pathlib import Path
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

BASE = os.environ.get("LUFFA_API_ENDPOINT", "https://apibot.luffa.im/robot")
GROUP_ID = os.environ.get("LUFFA_GROUP_ID", "Ad1MkyuxDLd")

BOTS = {
    "clerk":        {"uid": os.environ.get("LUFFA_BOT_CLERK_UID", ""),        "secret": os.environ.get("LUFFA_BOT_CLERK_SECRET", "")},
    "prosecution":  {"uid": os.environ.get("LUFFA_BOT_PROSECUTION_UID", ""),  "secret": os.environ.get("LUFFA_BOT_PROSECUTION_SECRET", "")},
    "defence":      {"uid": os.environ.get("LUFFA_BOT_DEFENCE_UID", ""),      "secret": os.environ.get("LUFFA_BOT_DEFENCE_SECRET", "")},
    "fact_checker": {"uid": os.environ.get("LUFFA_BOT_FACT_CHECKER_UID", ""), "secret": os.environ.get("LUFFA_BOT_FACT_CHECKER_SECRET", "")},
    "judge":        {"uid": os.environ.get("LUFFA_BOT_JUDGE_UID", ""),        "secret": os.environ.get("LUFFA_BOT_JUDGE_SECRET", "")},
    "witness_1":    {"uid": os.environ.get("LUFFA_BOT_WITNESS_1_UID", ""),    "secret": os.environ.get("LUFFA_BOT_WITNESS_1_SECRET", "")},
    "witness_2":    {"uid": os.environ.get("LUFFA_BOT_WITNESS_2_UID", ""),    "secret": os.environ.get("LUFFA_BOT_WITNESS_2_SECRET", "")},
    "juror_1":      {"uid": os.environ.get("LUFFA_BOT_JUROR_1_UID", ""),      "secret": os.environ.get("LUFFA_BOT_JUROR_1_SECRET", "")},
    "juror_2":      {"uid": os.environ.get("LUFFA_BOT_JUROR_2_UID", ""),      "secret": os.environ.get("LUFFA_BOT_JUROR_2_SECRET", "")},
    "defendant":    {"uid": os.environ.get("LUFFA_BOT_DEFENDANT_UID", ""),    "secret": os.environ.get("LUFFA_BOT_DEFENDANT_SECRET", "")},
}

# Filter out unconfigured bots
BOTS = {k: v for k, v in BOTS.items() if v["secret"]}


async def verify_auth(session, role, secret):
    """Verify bot credentials. Returns (role, success, message)."""
    try:
        async with session.post(f"{BASE}/receive", json={"secret": secret}, timeout=aiohttp.ClientTimeout(total=30)) as r:
            body = await r.text()
            if not body.strip() or body.strip() == "[]":
                return role, True, "OK (empty queue)"
            result = json.loads(body)
            if isinstance(result, dict) and result.get("code", 200) != 200:
                return role, False, result.get("msg", "unknown error")
            if isinstance(result, list):
                return role, True, f"OK ({sum(c.get('count', 0) for c in result)} pending messages)"
            return role, True, "OK"
    except Exception as e:
        return role, False, str(e)


async def poll_messages(session, role, secret):
    """Poll and display messages for a bot."""
    try:
        async with session.post(f"{BASE}/receive", json={"secret": secret}, timeout=aiohttp.ClientTimeout(total=30)) as r:
            body = await r.text()
            if not body.strip() or body.strip() == "[]":
                return []
            data = json.loads(body)
            convos = data if isinstance(data, list) else data.get("data", [])
            msgs = []
            for convo in convos:
                convo_type = int(convo.get("type", 0))
                for raw in convo.get("message", []):
                    msg = json.loads(raw) if isinstance(raw, str) else raw
                    msgs.append({
                        "role": role,
                        "type": "GROUP" if convo_type == 1 else "DM",
                        "sender": msg.get("uid", convo.get("uid")),
                        "text": msg.get("text", "")[:80],
                        "msgId": msg.get("msgId", "")[:12],
                    })
            return msgs
    except Exception as e:
        print(f"  {role}: poll error — {e}")
        return []


async def send_to_group(session, role, secret, text):
    """Send a message to the group from a specific bot."""
    try:
        msg = json.dumps({"text": text})
        async with session.post(
            f"{BASE}/sendGroup",
            json={"secret": secret, "uid": GROUP_ID, "msg": msg, "type": "1"},
            timeout=aiohttp.ClientTimeout(total=30)
        ) as r:
            body = await r.text()
            if body.strip():
                result = json.loads(body)
                if isinstance(result, dict) and result.get("code", 200) != 200:
                    return False, result.get("msg", "")
            return True, "sent"
    except Exception as e:
        return False, str(e)


async def main():
    send_mode = "--send" in sys.argv
    send_role = None
    if "--send-role" in sys.argv:
        idx = sys.argv.index("--send-role")
        send_role = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None

    async with aiohttp.ClientSession(headers={"Content-Type": "application/json"}) as session:
        # 1. Verify all bots
        print(f"=== Verify {len(BOTS)} bots ({BASE}) ===\n")
        for role, bot in BOTS.items():
            _, ok, msg = await verify_auth(session, role, bot["secret"])
            status = "OK" if ok else "FAIL"
            print(f"  {role:15s} {bot['uid']:15s} {status:4s}  {msg}")
        print()

        # 2. Poll all bots
        print(f"=== Poll all bots ===\n")
        total = 0
        for role, bot in BOTS.items():
            msgs = await poll_messages(session, role, bot["secret"])
            total += len(msgs)
            for m in msgs:
                print(f"  [{m['role']:12s}] {m['type']:5s} sender={m['sender']:15s} {m['text']}")
        if total == 0:
            print("  (no messages)")
        print()

        # 3. Send to group
        if send_mode or send_role:
            print(f"=== Send to group {GROUP_ID} ===\n")
            for role, bot in BOTS.items():
                if send_role and role != send_role:
                    continue
                ok, msg = await send_to_group(session, role, bot["secret"], f"{role.replace('_', ' ').title()} reporting for duty.")
                print(f"  {role:15s} {'sent' if ok else 'FAIL':4s}  {msg}")
                await asyncio.sleep(0.5)
            print()


if __name__ == "__main__":
    asyncio.run(main())
