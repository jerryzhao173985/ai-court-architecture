"""Multi-bot Luffa client using direct HTTP calls.

Uses direct HTTP calls to https://apibot.luffa.im/robot endpoints.
Each bot has its own secret key, eliminating race conditions from shared global state.

CRITICAL: The Luffa API returns HTTP 200 even on auth failure.
The actual error is in the JSON body: {"code": 500, "msg": "Robot verification failed"}.
We must check the "code" field, not just HTTP status.
"""

import asyncio
import json
import logging
from typing import Optional
from collections import OrderedDict

import aiohttp

from config import LuffaConfig

logger = logging.getLogger("veritas")


class LuffaAPIError(Exception):
    """Raised when Luffa API returns an error in the response body."""
    def __init__(self, endpoint: str, code: int, msg: str):
        self.endpoint = endpoint
        self.code = code
        self.api_msg = msg
        super().__init__(f"Luffa API {endpoint}: code={code} msg={msg}")


class MultiBotSDKClient:
    """
    Manages multiple Luffa bots using direct HTTP calls.

    Each trial agent (Clerk, Prosecution, Defence, Fact Checker, Judge)
    is a separate bot with its own secret key.

    API pattern (Luffa Bot API):
      POST https://apibot.luffa.im/robot/receive   -> {secret}
      POST https://apibot.luffa.im/robot/send       -> {secret, uid, msg}
      POST https://apibot.luffa.im/robot/sendGroup   -> {secret, uid, msg, type}

    Response format:
      Success: {"code": 200, "data": [...], "msg": "ok"} or raw array
      Failure: {"code": 500, "msg": "Robot verification failed"} (HTTP 200!)
    """

    def __init__(self, config: LuffaConfig):
        self.config = config
        self.base_url = config.api_base_url.rstrip("/")
        self.bot_secrets: dict[str, str] = {}
        self.bot_uids: set[str] = set()
        self.session: Optional[aiohttp.ClientSession] = None
        self.seen_message_ids: OrderedDict = OrderedDict()
        self._max_seen_ids = 5000
        self._auth_verified: dict[str, bool] = {}
        self._initialize_bots()

    def _initialize_bots(self):
        """Map bot roles to their secret keys."""
        bot_map = {
            "clerk": self.config.clerk_bot,
            "prosecution": self.config.prosecution_bot,
            "defence": self.config.defence_bot,
            "fact_checker": self.config.fact_checker_bot,
            "judge": self.config.judge_bot,
        }
        for role, bot in bot_map.items():
            if bot and bot.enabled:
                self.bot_secrets[role] = bot.secret
                self.bot_uids.add(bot.uid)
                logger.info(f"Registered {role} bot (UID: {bot.uid})")

        for juror_id, bot_cfg in self.config.juror_bots.items():
            if bot_cfg.enabled:
                self.bot_secrets[juror_id] = bot_cfg.secret
                self.bot_uids.add(bot_cfg.uid)
                logger.info(f"Registered {juror_id} bot (UID: {bot_cfg.uid})")

    async def _ensure_session(self):
        """Create aiohttp session if not already open."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}
            )

    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _make_request(self, endpoint: str, data: dict, timeout: int = 30):
        """
        Make HTTP POST request to Luffa Bot API.

        CRITICAL: Luffa returns HTTP 200 even on errors like auth failure.
        The real status is in the JSON body's "code" field.
        """
        await self._ensure_session()
        url = f"{self.base_url}{endpoint}"

        try:
            async with self.session.post(
                url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=timeout),
            ) as response:
                body_text = await response.text()

                # Check HTTP status first
                if not response.ok:
                    raise LuffaAPIError(endpoint, response.status, body_text[:200])

                # /send and /sendGroup may return empty body on success
                if not body_text or not body_text.strip():
                    return {"code": 200, "msg": "ok"}

                # Parse JSON response
                try:
                    result = json.loads(body_text)
                except json.JSONDecodeError:
                    # Some successful responses are plain text like "ok"
                    if response.ok:
                        return {"code": 200, "msg": body_text.strip()}
                    raise LuffaAPIError(endpoint, -1, f"Invalid JSON: {body_text[:200]}")

                # CRITICAL: Check the "code" field in the response body.
                # Luffa returns HTTP 200 even for auth failures!
                # Error format: {"code": 500, "msg": "Robot verification failed"}
                if isinstance(result, dict):
                    api_code = result.get("code")
                    if api_code is not None and api_code != 200:
                        api_msg = result.get("msg", "Unknown error")
                        raise LuffaAPIError(endpoint, api_code, api_msg)

                return result

        except asyncio.TimeoutError:
            logger.error(f"Luffa API request timed out: {endpoint}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Luffa API connection failed: {e}")
            raise

    async def verify_bot_auth(self, agent_role: str) -> bool:
        """
        Verify a bot's secret is valid by making a test receive call.
        Returns True if auth succeeds, False if it fails.
        """
        secret = self.get_bot_secret(agent_role)
        if not secret:
            logger.error(f"No secret configured for {agent_role}")
            return False

        try:
            await self._make_request("/receive", {"secret": secret})
            self._auth_verified[agent_role] = True
            logger.info(f"✓ {agent_role} bot auth verified")
            return True
        except LuffaAPIError as e:
            if "verification failed" in e.api_msg.lower():
                logger.error(
                    f"✗ {agent_role} bot auth FAILED: {e.api_msg}. "
                    f"Secret may be expired — regenerate at https://robot.luffa.im"
                )
            else:
                logger.error(f"✗ {agent_role} bot auth error: {e}")
            self._auth_verified[agent_role] = False
            return False
        except Exception as e:
            logger.error(f"✗ {agent_role} bot connection error: {e}")
            self._auth_verified[agent_role] = False
            return False

    async def verify_all_bots(self) -> dict[str, bool]:
        """Verify auth for all configured bots. Returns {role: success}."""
        results = {}
        for role in self.bot_secrets:
            results[role] = await self.verify_bot_auth(role)
        return results

    def get_bot_secret(self, agent_role: str) -> Optional[str]:
        return self.bot_secrets.get(agent_role)

    async def send_as_agent(
        self,
        agent_role: str,
        group_id: str,
        message: str,
        buttons: Optional[list[dict]] = None,
        confirm: Optional[list[dict]] = None,
        is_dm: bool = False,
        dismiss_type: str = "select",
        session_id: Optional[str] = None,
    ) -> bool:
        """
        Send message as specific agent bot with retry and failover logic.

        API format (Luffa Bot API):
          /send      -> {secret, uid, msg: JSON.stringify({text})}
          /sendGroup -> {secret, uid, msg: JSON.stringify({text}), type: "1"|"2"}
        
        Task 27.2: On HTTP error or empty response, retry once after 1s.
        If retry fails and role != "clerk", fallback to clerk bot with role prefix.
        """
        secret = self.get_bot_secret(agent_role)
        if not secret:
            logger.error(f"Cannot send as {agent_role}: no secret configured")
            return False

        async def _attempt_send() -> tuple[bool, Optional[str]]:
            """Attempt to send message. Returns (success, error_msg)."""
            try:
                if is_dm:
                    # DM — POST /robot/send
                    msg_json = json.dumps({"text": message})
                    result = await self._make_request(
                        "/send",
                        {"secret": secret, "uid": group_id, "msg": msg_json},
                    )
                    # Check for empty response
                    if not result or (isinstance(result, dict) and not result.get("msg")):
                        return False, "Empty response from API"
                    logger.info(f"Sent DM as {agent_role} to {group_id}")
                    return True, None
                else:
                    # Group — POST /robot/sendGroup
                    msg_obj = {"text": message}
                    msg_type = "1"  # 1=text only, 2=with buttons

                    if buttons or confirm:
                        msg_type = "2"
                        if buttons:
                            msg_obj["button"] = buttons
                        if confirm:
                            msg_obj["confirm"] = confirm
                        msg_obj["dismissType"] = dismiss_type

                    msg_json = json.dumps(msg_obj)
                    result = await self._make_request(
                        "/sendGroup",
                        {
                            "secret": secret,
                            "uid": group_id,
                            "msg": msg_json,
                            "type": msg_type,
                        },
                    )
                    # Check for empty response
                    if not result or (isinstance(result, dict) and not result.get("msg")):
                        return False, "Empty response from API"
                    logger.info(f"Sent group message as {agent_role} to {group_id}")
                    return True, None

            except LuffaAPIError as e:
                if "verification failed" in e.api_msg.lower():
                    error_msg = f"AUTH FAILED: {e.api_msg}"
                    logger.error(
                        f"{error_msg} for {agent_role} — "
                        f"regenerate secret at https://robot.luffa.im"
                    )
                else:
                    error_msg = f"Luffa API error: {e}"
                    logger.error(f"{error_msg} sending as {agent_role}")
                return False, error_msg
            except Exception as e:
                error_msg = f"Exception: {e}"
                logger.error(f"Failed to send as {agent_role}: {e}")
                return False, error_msg

        # First attempt
        success, error = await _attempt_send()
        if success:
            return True

        # Retry after 1 second
        logger.warning(f"First attempt failed for {agent_role}: {error}. Retrying in 1s...")
        await asyncio.sleep(1)
        success, error = await _attempt_send()
        if success:
            return True

        # Both attempts failed
        logger.error(f"Both attempts failed for {agent_role}: {error}")

        # Failover to clerk bot if not already clerk
        if agent_role != "clerk" and self.has_bot_for_role("clerk"):
            logger.warning(
                f"Failing over to clerk bot for {agent_role} message. "
                f"Original error: {error}"
            )
            
            # Track failover in metrics if session_id provided
            if session_id:
                from metrics import get_metrics_collector
                metrics = get_metrics_collector()
                await metrics.record_bot_failover(session_id)
            
            # Prefix message with role
            prefixed_message = f"[{agent_role.title()}] {message}"
            
            # Send via clerk bot (no buttons/confirm in failover)
            return await self.send_as_agent(
                agent_role="clerk",
                group_id=group_id,
                message=prefixed_message,
                is_dm=is_dm,
                session_id=session_id,
            )

        return False

    async def poll_messages(self, agent_role: str) -> list[dict]:
        """
        Poll for messages received by specific agent bot.

        API format (Luffa Bot API):
          POST /receive -> {secret}
          Response: {"code": 200, "data": [...]} or raw array
          Each envelope: {uid, count, type (0=DM,1=group), message: [...]}
          Each message string: {"text", "msgId", "uid", "atList", "urlLink"}
        """
        secret = self.get_bot_secret(agent_role)
        if not secret:
            return []

        try:
            response = await self._make_request("/receive", {"secret": secret})

            # Extract conversations from response.
            # Format varies: raw array OR {"code":200, "data":[...]}
            conversations = []
            if isinstance(response, list):
                conversations = response
            elif isinstance(response, dict):
                data = response.get("data")
                if isinstance(data, list):
                    conversations = data

            # Parse messages from each conversation envelope
            messages = []
            for convo in conversations:
                if not isinstance(convo, dict):
                    continue

                # type can be int (0/1) or string ("0"/"1") depending on API version
                try:
                    convo_type = int(convo.get("type", 0))
                except (TypeError, ValueError):
                    convo_type = 0
                convo_uid = convo.get("uid")
                raw_messages = convo.get("message", [])

                if not isinstance(raw_messages, list):
                    continue

                for raw in raw_messages:
                    try:
                        # Parse JSON message string (SDK does same with _coerce_to_dict)
                        if isinstance(raw, str):
                            parsed = json.loads(raw)
                            # Handle double-encoded JSON (SDK handles this too)
                            if isinstance(parsed, str):
                                parsed = json.loads(parsed)
                        elif isinstance(raw, dict):
                            parsed = raw
                        else:
                            continue

                        if not isinstance(parsed, dict):
                            continue

                        # Extract msgId (SDK tries: msgId, msgid, mid, message_id, id)
                        msg_id = (
                            parsed.get("msgId")
                            or parsed.get("msgid")
                            or parsed.get("mid")
                            or parsed.get("message_id")
                            or parsed.get("id")
                        )

                        # Deduplicate
                        if msg_id and msg_id in self.seen_message_ids:
                            continue
                        if msg_id:
                            self.seen_message_ids[msg_id] = None
                            while len(self.seen_message_ids) > self._max_seen_ids:
                                self.seen_message_ids.popitem(last=False)

                        # Extract text (SDK tries: text, msg, content, message, urlLink)
                        text = (
                            parsed.get("text")
                            or parsed.get("msg")
                            or parsed.get("content")
                            or parsed.get("message")
                            or parsed.get("urlLink")
                            or ""
                        )

                        messages.append({
                            "uid": convo_uid,
                            "gid": convo_uid if convo_type == 1 else None,
                            "type": convo_type,
                            "text": text,
                            "msgId": msg_id,
                            "sender_uid": parsed.get("uid") if convo_type == 1 else convo_uid,
                            "atList": parsed.get("atList", []),
                            "urlLink": parsed.get("urlLink"),
                        })

                    except (json.JSONDecodeError, TypeError) as e:
                        logger.warning(f"Failed to parse message: {e}")

            return messages

        except LuffaAPIError as e:
            if "verification failed" in e.api_msg.lower():
                logger.error(
                    f"AUTH FAILED polling as {agent_role}: {e.api_msg} — "
                    f"regenerate secret at https://robot.luffa.im"
                )
            else:
                logger.error(f"Luffa API error polling as {agent_role}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to poll messages for {agent_role}: {e}")
            return []

    async def broadcast_stage_announcement(
        self,
        group_id: str,
        stage_name: str,
        stage_description: str,
        buttons: Optional[list[dict]] = None,
    ) -> bool:
        """Broadcast stage announcement from Clerk bot."""
        message = f"⚖️ **{stage_name}**\n\n{stage_description}"
        return await self.send_as_agent("clerk", group_id, message, buttons=buttons)

    def has_bot_for_role(self, agent_role: str) -> bool:
        return agent_role in self.bot_secrets

    def get_configured_roles(self) -> list[str]:
        return list(self.bot_secrets.keys())


# Alias for backward compatibility
MultiBotClient = MultiBotSDKClient
