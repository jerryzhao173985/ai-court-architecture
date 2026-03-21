"""Multi-bot Luffa client for orchestrating multiple bots in group chat."""

import asyncio
import logging
from typing import Optional, Literal
from datetime import datetime

from luffa_client import LuffaBotAPIClient
from config import LuffaConfig, LuffaBotConfig

logger = logging.getLogger("veritas")


class MultiBotClient:
    """
    Manages multiple Luffa bots for realistic courtroom group chat.
    
    Each trial agent (Clerk, Prosecution, Defence, Fact Checker, Judge)
    can be a separate bot, creating a realistic multi-participant experience.
    """
    
    def __init__(self, config: LuffaConfig):
        """
        Initialize multi-bot client.
        
        Args:
            config: Luffa configuration with bot credentials
        """
        self.config = config
        self.clients: dict[str, LuffaBotAPIClient] = {}
        self._initialize_clients()
    
    def _create_bot_config(self, bot_config: LuffaBotConfig) -> LuffaConfig:
        """Create a LuffaConfig for a specific bot."""
        return LuffaConfig(
            apiBaseUrl=self.config.api_base_url,
            apiKey=bot_config.secret,
            botEnabled=bot_config.enabled,
            superboxEnabled=self.config.superbox_enabled,
            channelEnabled=self.config.channel_enabled
        )
    
    def _initialize_clients(self):
        """Initialize Luffa API clients for each configured bot."""
        # Initialize trial agent bots
        if self.config.clerk_bot and self.config.clerk_bot.enabled:
            bot_config = self._create_bot_config(self.config.clerk_bot)
            self.clients["clerk"] = LuffaBotAPIClient(bot_config)
            logger.info("Initialized Clerk bot")
        
        if self.config.prosecution_bot and self.config.prosecution_bot.enabled:
            bot_config = self._create_bot_config(self.config.prosecution_bot)
            self.clients["prosecution"] = LuffaBotAPIClient(bot_config)
            logger.info("Initialized Prosecution bot")
        
        if self.config.defence_bot and self.config.defence_bot.enabled:
            bot_config = self._create_bot_config(self.config.defence_bot)
            self.clients["defence"] = LuffaBotAPIClient(bot_config)
            logger.info("Initialized Defence bot")
        
        if self.config.fact_checker_bot and self.config.fact_checker_bot.enabled:
            bot_config = self._create_bot_config(self.config.fact_checker_bot)
            self.clients["fact_checker"] = LuffaBotAPIClient(bot_config)
            logger.info("Initialized Fact Checker bot")
        
        if self.config.judge_bot and self.config.judge_bot.enabled:
            bot_config = self._create_bot_config(self.config.judge_bot)
            self.clients["judge"] = LuffaBotAPIClient(bot_config)
            logger.info("Initialized Judge bot")
        
        # Initialize juror bots if configured
        for juror_id, bot_cfg in self.config.juror_bots.items():
            if bot_cfg.enabled:
                bot_config = self._create_bot_config(bot_cfg)
                self.clients[juror_id] = LuffaBotAPIClient(bot_config)
                logger.info(f"Initialized {juror_id} bot")
        
        # Legacy fallback: single bot for all agents
        if not self.clients and self.config.api_key:
            logger.warning("No individual bots configured, using legacy single-bot mode")
            self.clients["default"] = LuffaBotAPIClient(self.config)
    
    def get_client(self, agent_role: str) -> Optional[LuffaBotAPIClient]:
        """
        Get Luffa client for specific agent role.
        
        Args:
            agent_role: Role of the agent (clerk, prosecution, defence, fact_checker, judge, juror_1, etc.)
            
        Returns:
            LuffaBotAPIClient for that agent, or default client, or None
        """
        # Try to get specific client for this role
        if agent_role in self.clients:
            return self.clients[agent_role]
        
        # Fallback to default client if available
        if "default" in self.clients:
            return self.clients["default"]
        
        logger.warning(f"No Luffa client configured for {agent_role}")
        return None
    
    async def send_as_agent(
        self,
        agent_role: str,
        group_id: str,
        message: str,
        button: Optional[list[dict]] = None,
        confirm: Optional[list[dict]] = None,
        is_dm: bool = False
    ) -> bool:
        """
        Send message to group or DM as specific agent bot.
        
        Args:
            agent_role: Role of the agent sending the message
            group_id: Luffa group ID or user ID (for DMs)
            message: Message content
            button: Optional regular buttons
            confirm: Optional confirm buttons
            is_dm: If True, send as DM instead of group message
            
        Returns:
            True if sent successfully, False otherwise
        """
        client = self.get_client(agent_role)
        if not client:
            logger.error(f"Cannot send message as {agent_role}: no client configured")
            return False
        
        try:
            # Use async context manager
            async with client:
                if is_dm:
                    # Send direct message
                    result = await client.send_dm(
                        recipient_uid=group_id,
                        text=message
                    )
                else:
                    # Send group message
                    result = await client.send_group_message(
                        group_id=group_id,
                        text=message,
                        button=button,
                        confirm=confirm
                    )
                
                if result.get("success"):
                    msg_type = "DM" if is_dm else "group message"
                    logger.info(f"Sent {msg_type} as {agent_role} to {group_id}")
                    return True
                else:
                    logger.error(f"Failed to send as {agent_role}: {result.get('error')}")
                    return False
        except Exception as e:
            logger.error(f"Failed to send message as {agent_role}: {e}")
            return False
    
    async def poll_messages(self, agent_role: str) -> list[dict]:
        """
        Poll for messages received by specific agent bot.
        
        Args:
            agent_role: Role of the agent to poll for
            
        Returns:
            List of messages
        """
        client = self.get_client(agent_role)
        if not client:
            return []
        
        try:
            async with client:
                return await client.receive_messages()
        except Exception as e:
            logger.error(f"Failed to poll messages for {agent_role}: {e}")
            return []
    
    async def broadcast_stage_announcement(
        self,
        group_id: str,
        stage_name: str,
        stage_description: str,
        button: Optional[list[dict]] = None
    ) -> bool:
        """
        Broadcast stage announcement from Clerk bot.
        
        Args:
            group_id: Luffa group ID
            stage_name: Name of the trial stage
            stage_description: Description of what happens in this stage
            button: Optional interactive buttons
            
        Returns:
            True if sent successfully
        """
        message = f"⚖️ **{stage_name}**\n\n{stage_description}"
        return await self.send_as_agent("clerk", group_id, message, button=button)
    
    def has_bot_for_role(self, agent_role: str) -> bool:
        """
        Check if a bot is configured for specific role.
        
        Args:
            agent_role: Role to check
            
        Returns:
            True if bot configured for this role
        """
        return agent_role in self.clients or "default" in self.clients
    
    def get_configured_roles(self) -> list[str]:
        """
        Get list of all configured bot roles.
        
        Returns:
            List of agent roles with configured bots
        """
        return [role for role in self.clients.keys() if role != "default"]
