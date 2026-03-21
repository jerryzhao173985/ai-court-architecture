"""Debug Luffa API responses to see what's actually happening."""

import asyncio
import httpx
import json

YOUR_USER_ID = "WYspi9HYaHH"
COURTROOM_GROUP_ID = "Hqvqnvzh4mq"

# Bot credentials
BOTS = {
    "Clerk": {
        "uid": "ORQAZCejHdZELLD",
        "secret": "ta86cbb0bd1f35425bb03b66cdcd49d81e"
    },
    "Prosecution": {
        "uid": "MZIXVYXwSwRx6Vd",
        "secret": "os8dc8ecf0b69b4a37956ad37e66553f30"
    },
    "Defence": {
        "uid": "NGKIEJGGRlKKnAqC",
        "secret": "P5263ab3153044a66ae567773cbea6ca9"
    },
    "Fact Checker": {
        "uid": "GKUPDBfLv23WktAS",
        "secret": "y7b0636260a8740d980f0582ea94cc438"
    },
    "Judge": {
        "uid": "YNLJHNCCsRmLBcvU",
        "secret": "ye9e38b40137248cc841cc97aced744ce"
    }
}


async def debug_send():
    """Debug API send calls."""
    print("\n" + "="*60)
    print("🔍 Debugging Luffa API Responses")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        # Test Clerk bot sending DM
        bot_name = "Clerk"
        bot = BOTS[bot_name]
        
        print(f"Testing {bot_name} bot:")
        print(f"  UID: {bot['uid']}")
        print(f"  Secret: {bot['secret'][:10]}...")
        print()
        
        # Test 1: Send DM
        print("📤 Test 1: Sending DM...")
        
        msg_data = {"text": f"Test from {bot_name} bot"}
        
        payload = {
            "secret": bot["secret"],
            "uid": YOUR_USER_ID,
            "msg": json.dumps(msg_data)
        }
        
        print(f"  Request payload: {json.dumps(payload, indent=2)}")
        print()
        
        response = await client.post(
            "https://apibot.luffa.im/robot/send",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Response status: {response.status_code}")
        print(f"  Response headers: {dict(response.headers)}")
        print(f"  Response body: {response.text}")
        print()
        
        try:
            response_json = response.json()
            print(f"  Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print("  (Could not parse as JSON)")
        
        print()
        
        # Test 2: Receive messages
        print("📥 Test 2: Checking for messages...")
        
        receive_payload = {"secret": bot["secret"]}
        
        response = await client.post(
            "https://apibot.luffa.im/robot/receive",
            json=receive_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Response status: {response.status_code}")
        print(f"  Response body: {response.text}")
        print()
        
        try:
            response_json = response.json()
            print(f"  Response JSON: {json.dumps(response_json, indent=2)}")
            
            if isinstance(response_json, list) and len(response_json) > 0:
                print(f"\n  📬 Found {len(response_json)} envelope(s)")
            else:
                print("\n  📭 No messages")
        except:
            print("  (Could not parse as JSON)")
        
        print()
        
        # Test 3: Send to group
        print("📤 Test 3: Sending to group...")
        
        group_msg_data = {"text": f"Test from {bot_name} to group"}
        
        group_payload = {
            "secret": bot["secret"],
            "uid": COURTROOM_GROUP_ID,
            "msg": json.dumps(group_msg_data),
            "type": "1"
        }
        
        print(f"  Request payload: {json.dumps(group_payload, indent=2)}")
        print()
        
        response = await client.post(
            "https://apibot.luffa.im/robot/sendGroup",
            json=group_payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"  Response status: {response.status_code}")
        print(f"  Response body: {response.text}")
        print()
        
        try:
            response_json = response.json()
            print(f"  Response JSON: {json.dumps(response_json, indent=2)}")
        except:
            print("  (Could not parse as JSON)")
    
    print()
    print("="*60)
    print("Analysis:")
    print("="*60)
    print()
    print("If response shows 'code': 0 or 'success': true:")
    print("  → API accepts the request")
    print("  → But messages may not deliver if:")
    print("    • Bot credentials are invalid")
    print("    • Bot is not activated/enabled")
    print("    • Recipient has blocked bots")
    print("    • Bot needs to be friends with recipient first")
    print()
    print("Check the response JSON above for error codes or messages.")
    print()


if __name__ == "__main__":
    asyncio.run(debug_send())
