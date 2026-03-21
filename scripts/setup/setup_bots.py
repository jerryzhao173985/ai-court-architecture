#!/usr/bin/env python3
"""
Setup script for configuring Luffa bots for VERITAS courtroom experience.

This script helps you map your Luffa bot credentials to trial agent roles.
"""

import os
from pathlib import Path


def main():
    """Interactive setup for Luffa bots."""
    print("=" * 80)
    print("VERITAS COURTROOM EXPERIENCE - LUFFA BOT SETUP")
    print("=" * 80)
    print()
    print("You have created multiple Luffa bots. Let's map them to courtroom roles.")
    print()
    print("RECOMMENDED ARCHITECTURE: 5 Bots for Trial Agents")
    print("  Bot 1: Clerk (procedural guidance, orchestration)")
    print("  Bot 2: Prosecution Barrister")
    print("  Bot 3: Defence Barrister")
    print("  Bot 4: Fact Checker (intervenes on contradictions)")
    print("  Bot 5: Judge (summing up, legal instructions)")
    print()
    print("Optional: Additional bots for AI jurors (3 active + 4 lightweight)")
    print()
    print("-" * 80)
    print()
    
    # Your bot credentials from robot.luffa.im
    print("Your available bots:")
    print()
    print("1. UID: ORQAZCejHdZELLD, Secret: ta86cbb0bd1f35425bb03b66cdcd49d81e")
    print("2. UID: MZIXVYXwSwRx6Vd, Secret: os8dc8ecf0b69b4a37956ad37e66553f30")
    print("3. UID: NGKIEJGGRlKKnAqC, Secret: P5263ab3153044a66ae567773cbea6ca9")
    print("4. UID: GKUPDBfLv23WktAS, Secret: y7b0636260a8740d980f0582ea94cc438")
    print("5. UID: YNLJHNCCsRmLBcvU, Secret: ye9e38b40137248cc841cc97aced744ce")
    print()
    print("-" * 80)
    print()
    
    # Recommended mapping
    bot_mapping = {
        "CLERK": ("ORQAZCejHdZELLD", "ta86cbb0bd1f35425bb03b66cdcd49d81e"),
        "PROSECUTION": ("MZIXVYXwSwRx6Vd", "os8dc8ecf0b69b4a37956ad37e66553f30"),
        "DEFENCE": ("NGKIEJGGRlKKnAqC", "P5263ab3153044a66ae567773cbea6ca9"),
        "FACT_CHECKER": ("GKUPDBfLv23WktAS", "y7b0636260a8740d980f0582ea94cc438"),
        "JUDGE": ("YNLJHNCCsRmLBcvU", "ye9e38b40137248cc841cc97aced744ce")
    }
    
    print("RECOMMENDED MAPPING:")
    print()
    for role, (uid, secret) in bot_mapping.items():
        print(f"  {role:15} → UID: {uid}, Secret: {secret}")
    print()
    print("-" * 80)
    print()
    
    # Generate .env content
    env_content = """# LLM Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=30

# Luffa Bot Configuration - Multi-Bot Architecture
# Each trial agent is a separate bot for realistic group chat

# Bot 1: Clerk (Procedural guidance and orchestration)
LUFFA_BOT_CLERK_UID=ORQAZCejHdZELLD
LUFFA_BOT_CLERK_SECRET=ta86cbb0bd1f35425bb03b66cdcd49d81e

# Bot 2: Prosecution Barrister
LUFFA_BOT_PROSECUTION_UID=MZIXVYXwSwRx6Vd
LUFFA_BOT_PROSECUTION_SECRET=os8dc8ecf0b69b4a37956ad37e66553f30

# Bot 3: Defence Barrister
LUFFA_BOT_DEFENCE_UID=NGKIEJGGRlKKnAqC
LUFFA_BOT_DEFENCE_SECRET=P5263ab3153044a66ae567773cbea6ca9

# Bot 4: Fact Checker
LUFFA_BOT_FACT_CHECKER_UID=GKUPDBfLv23WktAS
LUFFA_BOT_FACT_CHECKER_SECRET=y7b0636260a8740d980f0582ea94cc438

# Bot 5: Judge
LUFFA_BOT_JUDGE_UID=YNLJHNCCsRmLBcvU
LUFFA_BOT_JUDGE_SECRET=ye9e38b40137248cc841cc97aced744ce

# Luffa API Configuration
LUFFA_API_ENDPOINT=https://api.luffa.im
LUFFA_BOT_ENABLED=true

# Application Configuration
SESSION_TIMEOUT_HOURS=24
MAX_EXPERIENCE_MINUTES=20
"""
    
    print("GENERATED .env CONFIGURATION:")
    print()
    print(env_content)
    print()
    print("-" * 80)
    print()
    
    # Ask if user wants to write to .env
    response = input("Write this configuration to .env file? (yes/no): ").strip().lower()
    
    if response in ["yes", "y"]:
        env_path = Path(".env")
        
        # Backup existing .env if it exists
        if env_path.exists():
            backup_path = Path(".env.backup")
            print(f"Backing up existing .env to {backup_path}")
            env_path.rename(backup_path)
        
        # Write new .env
        env_path.write_text(env_content)
        print(f"✓ Configuration written to {env_path}")
        print()
        print("NEXT STEPS:")
        print("  1. Update OPENAI_API_KEY in .env with your actual API key")
        print("  2. Add all 5 bots to the same Luffa group chat")
        print("  3. Run: python src/luffa_bot_service.py")
        print("  4. In the group chat, send: /start")
        print()
    else:
        print("Configuration not written. You can manually copy the content above to your .env file.")
        print()


if __name__ == "__main__":
    main()
