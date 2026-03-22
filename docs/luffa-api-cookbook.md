# Luffa Bot API Cookbook

Practical code snippets for interacting with the Luffa Bot API. All examples use `aiohttp` and run from the project root.

## Setup

```python
import asyncio, aiohttp, json

BASE = "https://apibot.luffa.im/robot"
SECRET = "your_bot_secret"
GROUP_ID = "Ad1MkyuxDLd"
USER_UID = "WYspi9HYaHH"
```

## 1. Verify Bot Credentials

```python
async with aiohttp.ClientSession() as s:
    async with s.post(f"{BASE}/receive", json={"secret": SECRET}, timeout=aiohttp.ClientTimeout(total=30)) as r:
        body = await r.text()
        result = json.loads(body) if body.strip() else []
        # Success: [] or {"code": 200, "data": [...]}
        # Failure: {"code": 500, "msg": "Robot verification failed"}
        if isinstance(result, dict) and result.get("code", 200) != 200:
            print(f"AUTH FAILED: {result['msg']}")
```

**Gotcha**: HTTP status is always 200. Check `code` field in body.

## 2. Poll for Messages (Receive)

```python
async with s.post(f"{BASE}/receive", json={"secret": SECRET}, timeout=aiohttp.ClientTimeout(total=30)) as r:
    data = await r.json()
    # Response: [{"uid":"group_or_user_id", "type":1, "count":2, "message":["json_str",...]}]
    # type 0 = DM, type 1 = group
    conversations = data if isinstance(data, list) else data.get("data", [])
    for convo in conversations:
        for raw in convo.get("message", []):
            msg = json.loads(raw)
            print(f"sender={msg.get('uid')} text={msg.get('text')} msgId={msg.get('msgId')}")
```

**Gotcha**: `type` may be int or string. Always `int(convo.get("type", 0))`.
**Gotcha**: Each bot has its own queue. Poll ALL bots to get all group messages.

## 3. Send DM

```python
msg = json.dumps({"text": "Hello from bot"})
async with s.post(f"{BASE}/send", json={"secret": SECRET, "uid": USER_UID, "msg": msg}) as r:
    # Success: empty body (not JSON)
    # Failure: {"code": 500, "msg": "id does not exist"}
    pass
```

**Gotcha**: Returns empty body on success. Don't try to parse JSON.
**Gotcha**: "id does not exist" means bot has no connection with that user yet.

## 4. Send Group Message (Text)

```python
msg = json.dumps({"text": "Message to group"})
async with s.post(f"{BASE}/sendGroup", json={"secret": SECRET, "uid": GROUP_ID, "msg": msg, "type": "1"}) as r:
    pass  # empty body on success
```

## 5. Send Group Message (With Buttons)

```python
msg = json.dumps({
    "text": "Choose one:",
    "button": [
        {"name": "Option A", "selector": "/choose_a", "isHidden": "0"},
        {"name": "Option B", "selector": "/choose_b", "isHidden": "1"}  # hidden = private click
    ],
    "dismissType": "dismiss"  # "dismiss" = disappear after click, "select" = persist
})
async with s.post(f"{BASE}/sendGroup", json={"secret": SECRET, "uid": GROUP_ID, "msg": msg, "type": "2"}) as r:
    pass
```

`type: "1"` = text only, `type: "2"` = with buttons.

## 6. Verify All 10 Bots

```python
BOTS = {
    "clerk":        "1302a374b76e4e5c83247923e6c3e368",
    "prosecution":  "87e1b9c671374f8ebd3e59f1f8c61e0a",
    "defence":      "2023fec7dbf9476a918722cd45a0c5e8",
    "fact_checker": "1c8e7648da144160b0b3c6029455f52c",
    "judge":        "66a8d80edcd54204bb72b656a9d3ad47",
    "witness_1":    "86cbb0bd1f35425bb03b66cdcd49d81e",
    "witness_2":    "8dc8ecf0b69b4a37956ad37e66553f30",
    "juror_1":      "5263ab3153044a66ae567773cbea6ca9",
    "juror_2":      "7b0636260a8740d980f0582ea94cc438",
    "defendant":    "e9e38b40137248cc841cc97aced744ce",
}

async with aiohttp.ClientSession() as s:
    for role, secret in BOTS.items():
        async with s.post(f"{BASE}/receive", json={"secret": secret}, timeout=aiohttp.ClientTimeout(total=30)) as r:
            body = await r.text()
            result = json.loads(body) if body.strip() else {"code": 200}
            ok = not (isinstance(result, dict) and result.get("code", 200) != 200)
            print(f"{role}: {'OK' if ok else 'FAIL'}")
```

## 7. Poll All Bots and Filter

```python
BOT_UIDS = {"MDxaEfAbC8J", "2fPGmAnhowc", "JTNTR5vjhSd", "hFawR8U4iX1", "h3xYBbwhx9d",
             "ejHdZELLDta", "XwSwRx6Vdos", "GGR1KKnAqCP", "fLv23WktASy", "CCsRmLBcvUy"}
seen = set()

for role, secret in BOTS.items():
    async with s.post(f"{BASE}/receive", json={"secret": secret}) as r:
        data = await r.json()
        convos = data if isinstance(data, list) else data.get("data", [])
        for convo in convos:
            for raw in convo.get("message", []):
                msg = json.loads(raw)
                msg_id = msg.get("msgId")
                sender = msg.get("uid") if int(convo.get("type", 0)) == 1 else convo.get("uid")

                if msg_id in seen:           continue  # dedup across bots
                if sender in BOT_UIDS:       continue  # skip bot echo
                seen.add(msg_id)
                print(f"[{role}] {sender}: {msg.get('text')}")
```

**Key patterns**:
- Each bot gets its own copy of group messages → poll all, dedup by `msgId`
- Bot A's messages appear in Bot B's poll → filter by `sender_uid` in `BOT_UIDS`
- `convo["uid"]` = group ID for group messages, not the sender
- `msg["uid"]` inside the message JSON = actual sender

## 8. New Bot Onboarding Flow

```
1. Create bot at https://robot.luffa.im → get UID + secret
2. Verify credentials: POST /receive with {secret} → check code != 500
3. User sends friend request to bot on Luffa app
4. Poll bot: POST /receive → consume join notification
5. User adds bot to group on Luffa app
6. Poll bot again → consume group join notification ("自己入群消息")
7. Bot can now sendGroup to that group
```

Steps 4 and 6 (polling after join) are required — the bot must consume the notification before it can interact.

## 9. Message Format Reference

**Incoming envelope** (from `/receive`):
```json
{"uid": "group_or_user_id", "type": 1, "count": 2, "message": ["json_str", ...]}
```

**Incoming message** (parsed from `message` array):
```json
{"msgId": "unique_id", "uid": "sender_uid", "text": "message text", "atList": [], "urlLink": null}
```

**Outgoing DM** (`/send`):
```json
{"secret": "...", "uid": "recipient_uid", "msg": "{\"text\": \"hello\"}"}
```

**Outgoing group** (`/sendGroup`):
```json
{"secret": "...", "uid": "group_id", "msg": "{\"text\": \"hello\"}", "type": "1"}
```

**Outgoing group with buttons** (`/sendGroup`):
```json
{"secret": "...", "uid": "group_id", "type": "2", "msg": "{\"text\":\"Pick:\",\"button\":[{\"name\":\"A\",\"selector\":\"/a\",\"isHidden\":\"0\"}],\"dismissType\":\"select\"}"}
```
