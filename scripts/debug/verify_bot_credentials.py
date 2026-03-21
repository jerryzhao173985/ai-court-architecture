"""Verify each bot's credentials individually."""

import asyncio
import httpx
import json

YOUR_USER_ID = "WYspi9HYaHH"

# Bot credentials from your .env
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


async def verify_credentials():
    """Verify each bot's credentials."""
    print("\n" + "="*60)
    print("🔐 Verifying Bot Credentials")
    print("="*60 + "\n")
    
    async with httpx.AsyncClient() as client:
        for bot_name, bot in BOTS.items():
            print(f"Testing {bot_name}:")
            print(f"  UID: {bot['uid']}")
            print(f"  Secret: {bot['secret']}")
            print()
            
            # Try to receive messages (simplest verification)
            payload = {"secret": bot["secret"]}
            
            try:
                response = await client.post(
                    "https://apibot.luffa.im/robot/receive",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )
                
                response_data = response.json()
                
                if response_data.get("code") == 500:
                    print(f"  ❌ FAILED: {response_data.get('msg')}")
                    print(f"     → Bot credentials are INVALID or bot is not activated")
                elif response_data.get("code") == 0 or isinstance(response_data, list):
                    print(f"  ✅ SUCCESS: Bot credentials are valid")
                else:
                    print(f"  ⚠️  UNKNOWN: {json.dumps(response_data)}")
                
            except Exception as e:
                print(f"  ❌ ERROR: {e}")
            
            print()
    
    print("="*60)
    print("🔍 Diagnosis:")
    print("="*60)
    print()
    print("If ALL bots show 'Robot verification failed':")
    print("  → The secret keys are incorrect")
    print("  → OR the bots are not activated in Luffa platform")
    print()
    print("Please verify:")
    print("  1. Go to Luffa Bot management panel")
    print("  2. Check each bot's actual secret key")
    print("  3. Ensure bots are 'Active' or 'Enabled'")
    print("  4. Copy the EXACT secret keys (case-sensitive)")
    print()
    print("The UIDs you provided:")
    for bot_name, bot in BOTS.items():
        print(f"  • {bot_name}: {bot['uid']}")
    print()
    print("Are these the FULL UIDs from the Luffa platform?")
    print("(UIDs might be longer or have different format)")
    print()


if __name__ == "__main__":
    asyncio.run(verify_credentials())
