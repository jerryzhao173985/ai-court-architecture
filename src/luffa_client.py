"""Client for Luffa Bot API integration."""

import asyncio
import logging
import json
from typing import Optional, Any, List
import aiohttp
from datetime import datetime

from config import LuffaConfig

logger = logging.getLogger("veritas")


class LuffaBotAPIClient:
    """
    Client for interacting with Luffa Bot API (polling-based).
    
    Based on Luffa Bot API at https://apibot.luffa.im/robot
    """

    def __init__(self, config: LuffaConfig):
        """
        Initialize Luffa Bot API client.
        
        Args:
            config: Luffa platform configuration (uses apiKey as bot secret)
        """
        self.config = config
        self.base_url = "https://apibot.luffa.im/robot"
        self.bot_secret = config.api_key
        self.session: Optional[aiohttp.ClientSession] = None
        self.seen_message_ids = set()  # For deduplication

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            headers={"Content-Type": "application/json"}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def _make_request(
        self,
        endpoint: str,
        data: dict,
        timeout: int = 10
    ) -> Any:
        """
        Make HTTP request to Luffa Bot API.
        
        Args:
            endpoint: API endpoint path
            data: Request body data
            timeout: Request timeout in seconds
            
        Returns:
            Response data
            
        Raises:
            Exception: If request fails
        """
        if not self.session:
            raise RuntimeError("Client session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with asyncio.timeout(timeout):
                async with self.session.post(url, json=data) as response:
                    response.raise_for_status()
                    return await response.json()
        
        except asyncio.TimeoutError:
            logger.error(f"Luffa Bot API request timed out: {endpoint}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Luffa Bot API request failed: {e}")
            raise

    # ========================================================================
    # BOT API - Receiving Messages
    # ========================================================================

    async def receive_messages(self) -> List[dict]:
        """
        Poll for new messages (call every 1 second).
        
        Returns:
            List of message objects
        """
        if not self.config.bot_enabled or not self.bot_secret:
            return []
        
        try:
            # Response is a raw array, not wrapped in {code, data}
            messages = await self._make_request(
                endpoint="/receive",
                data={"secret": self.bot_secret}
            )
            
            # Parse and deduplicate messages
            parsed_messages = []
            for msg_obj in messages:
                for msg_str in msg_obj.get("message", []):
                    try:
                        parsed = json.loads(msg_str)
                        msg_id = parsed.get("msgId")
                        
                        # Deduplicate by msgId
                        if msg_id and msg_id not in self.seen_message_ids:
                            self.seen_message_ids.add(msg_id)
                            parsed_messages.append({
                                "uid": msg_obj.get("uid"),  # Sender or group ID
                                "type": msg_obj.get("type"),  # 0=DM, 1=Group
                                "text": parsed.get("text"),
                                "msgId": msg_id,
                                "sender_uid": parsed.get("uid"),  # Only in group messages
                                "atList": parsed.get("atList", []),
                                "urlLink": parsed.get("urlLink")
                            })
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse message: {e}")
            
            return parsed_messages
        
        except Exception as e:
            logger.warning(f"Failed to receive messages: {e}")
            return []

    # ========================================================================
    # BOT API - Sending Messages
    # ========================================================================

    async def send_dm(
        self,
        recipient_uid: str,
        text: str
    ) -> dict:
        """
        Send a direct message.
        
        Args:
            recipient_uid: Recipient's Luffa ID
            text: Message text
            
        Returns:
            API response
        """
        if not self.config.bot_enabled or not self.bot_secret:
            logger.info("Luffa Bot disabled, skipping DM")
            return {"success": True, "skipped": True}
        
        try:
            msg_json = json.dumps({"text": text})
            
            response = await self._make_request(
                endpoint="/send",
                data={
                    "secret": self.bot_secret,
                    "uid": recipient_uid,
                    "msg": msg_json
                }
            )
            
            return {"success": True, "response": response}
        
        except Exception as e:
            logger.warning(f"Failed to send DM: {e}")
            return {"success": False, "error": str(e)}

    async def send_group_message(
        self,
        group_id: str,
        text: str,
        buttons: Optional[List[dict]] = None,
        confirm_buttons: Optional[List[dict]] = None,
        dismiss_type: str = "select"
    ) -> dict:
        """
        Send a group message with optional buttons.
        
        Args:
            group_id: Group ID
            text: Message text
            buttons: Optional list of button objects
            confirm_buttons: Optional list of confirm button objects
            dismiss_type: "select" (persist) or "dismiss" (disappear after click)
            
        Returns:
            API response
        """
        if not self.config.bot_enabled or not self.bot_secret:
            logger.info("Luffa Bot disabled, skipping group message")
            return {"success": True, "skipped": True}
        
        try:
            # Build message object
            msg_obj = {"text": text}
            
            # Type 1: Plain text (no buttons)
            msg_type = "1"
            
            # Type 2: Text with buttons
            if buttons or confirm_buttons:
                msg_type = "2"
                if buttons:
                    msg_obj["button"] = buttons
                if confirm_buttons:
                    msg_obj["confirm"] = confirm_buttons
                msg_obj["dismissType"] = dismiss_type
            
            msg_json = json.dumps(msg_obj)
            
            response = await self._make_request(
                endpoint="/sendGroup",
                data={
                    "secret": self.bot_secret,
                    "uid": group_id,
                    "msg": msg_json,
                    "type": msg_type
                }
            )
            
            return {"success": True, "response": response}
        
        except Exception as e:
            logger.warning(f"Failed to send group message: {e}")
            return {"success": False, "error": str(e)}

    # ========================================================================
    # VERITAS-Specific Helper Methods
    # ========================================================================

    async def send_bot_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[dict] = None,
        recipient_uid: Optional[str] = None,
        group_id: Optional[str] = None
    ) -> dict:
        """
        Send message via Luffa Bot (VERITAS wrapper).
        
        Args:
            session_id: User session ID (stored in metadata)
            message_type: Type of message (greeting, announcement, etc.)
            content: Message content
            metadata: Additional metadata
            recipient_uid: For DMs
            group_id: For group messages
            
        Returns:
            API response
        """
        # Format message with session context
        formatted_text = f"[VERITAS] {content}"
        
        if group_id:
            return await self.send_group_message(group_id, formatted_text)
        elif recipient_uid:
            return await self.send_dm(recipient_uid, formatted_text)
        else:
            logger.warning("No recipient specified for bot message")
            return {"success": False, "error": "No recipient specified"}

    async def send_stage_announcement(
        self,
        group_id: str,
        stage_name: str,
        announcement_text: str
    ) -> dict:
        """
        Send trial stage announcement to group.
        
        Args:
            group_id: Group ID
            stage_name: Name of the trial stage
            announcement_text: Announcement text
            
        Returns:
            API response
        """
        text = f"🎭 {stage_name.upper()}\n\n{announcement_text}"
        return await self.send_group_message(group_id, text)

    async def send_verdict_options(
        self,
        group_id: str,
        user_uid: str
    ) -> dict:
        """
        Send voting buttons to user.
        
        Args:
            group_id: Group ID
            user_uid: User's Luffa ID
            
        Returns:
            API response
        """
        text = "⚖️ TIME TO VOTE\n\nCast your verdict:"
        
        buttons = [
            {
                "name": "✅ GUILTY",
                "selector": "/vote guilty",
                "isHidden": "1"  # Hidden from others
            },
            {
                "name": "❌ NOT GUILTY",
                "selector": "/vote not_guilty",
                "isHidden": "1"  # Hidden from others
            }
        ]
        
        return await self.send_group_message(
            group_id=group_id,
            text=text,
            buttons=buttons,
            dismiss_type="dismiss"  # Disappear after click
        )


# Alias for backward compatibility
LuffaAPIClient = LuffaBotAPIClient
