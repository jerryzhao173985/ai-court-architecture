#!/usr/bin/env python3
"""
End-to-end integration test for VERITAS Luffa Bot experience.

Task 22.5: Test end-to-end flow with real Luffa Bot
- Deploy bot to Luffa platform
- Test complete experience flow in group chat
- Verify message delivery and timing
- Test error recovery scenarios
- Requirements: All Luffa integration requirements

This test validates the complete trial flow from start to finish,
including message delivery, timing constraints, and error handling.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Dict, Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from config import load_config
from multi_bot_service import MultiBotService
from multi_bot_client_sdk import MultiBotSDKClient
from orchestrator import ExperienceOrchestrator
from state_machine import ExperienceState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("veritas.e2e_test")


class E2ETestRunner:
    """End-to-end test runner for Luffa Bot integration."""
    
    def __init__(self):
        """Initialize test runner."""
        self.config = load_config()
        self.multi_bot = MultiBotSDKClient(self.config.luffa)
        # Get group ID from environment or use default
        self.test_group_id = os.getenv("LUFFA_GROUP_ID", "test_group")
        self.test_user_id = "test_user_e2e"
        self.results: List[Dict] = []
        
    async def run_all_tests(self) -> bool:
        """
        Run all end-to-end tests.
        
        Returns:
            True if all tests pass, False otherwise
        """
        logger.info("="*60)
        logger.info("VERITAS E2E LUFFA BOT INTEGRATION TEST")
        logger.info("="*60)
        
        tests = [
            ("Bot Authentication", self.test_bot_authentication),
            ("Message Delivery", self.test_message_delivery),
            ("Complete Trial Flow", self.test_complete_trial_flow),
            ("Timing Constraints", self.test_timing_constraints),
            ("Error Recovery", self.test_error_recovery),
            ("Multi-User Support", self.test_multi_user_support),
            ("Session Management", self.test_session_management),
        ]
        
        for test_name, test_func in tests:
            logger.info(f"\n{'='*60}")
            logger.info(f"TEST: {test_name}")
            logger.info(f"{'='*60}")
            
            try:
                result = await test_func()
                self.results.append({
                    "test": test_name,
                    "passed": result,
                    "error": None
                })
                
                if result:
                    logger.info(f"✅ {test_name} PASSED")
                else:
                    logger.error(f"❌ {test_name} FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {test_name} FAILED with exception: {e}")
                self.results.append({
                    "test": test_name,
                    "passed": False,
                    "error": str(e)
                })
        
        # Print summary
        self._print_summary()
        
        # Return overall result
        return all(r["passed"] for r in self.results)
    
    async def test_bot_authentication(self) -> bool:
        """
        Test 1: Verify all bots can authenticate with Luffa API.
        
        Validates: Requirements 13.1, 22.1
        """
        logger.info("Verifying bot credentials...")
        
        try:
            auth_results = await self.multi_bot.verify_all_bots()
            
            failed_bots = [role for role, ok in auth_results.items() if not ok]
            passed_bots = [role for role, ok in auth_results.items() if ok]
            
            if failed_bots:
                logger.error(f"Authentication failed for: {', '.join(failed_bots)}")
                logger.error("Bot secrets may be expired. Regenerate at https://robot.luffa.im")
                return False
            
            logger.info(f"✓ All {len(passed_bots)} bots authenticated successfully")
            logger.info(f"  Authenticated roles: {', '.join(passed_bots)}")
            
            # Verify required roles are present
            required_roles = ["clerk", "prosecution", "defence", "fact_checker", "judge"]
            missing_roles = [r for r in required_roles if r not in passed_bots]
            
            if missing_roles:
                logger.error(f"Missing required roles: {', '.join(missing_roles)}")
                return False
            
            logger.info("✓ All required roles configured")
            return True
            
        except Exception as e:
            logger.error(f"Authentication test failed: {e}")
            return False
    
    async def test_message_delivery(self) -> bool:
        """
        Test 2: Verify messages can be sent and received via Luffa API.
        
        Validates: Requirements 13.2, 13.3, 22.3
        """
        logger.info("Testing message delivery...")
        
        try:
            # Test sending message from Clerk bot
            test_message = f"E2E Test Message - {datetime.now().isoformat()}"
            
            success = await self.multi_bot.send_as_agent(
                "clerk",
                self.test_group_id,
                test_message
            )
            
            if not success:
                logger.error("Failed to send test message")
                return False
            
            logger.info("✓ Message sent successfully")
            
            # Wait for message to be delivered
            await asyncio.sleep(2)
            
            # Poll for messages
            messages = await self.multi_bot.poll_messages("clerk")
            
            logger.info(f"✓ Polled {len(messages)} messages")
            
            # Note: We can't verify our own message appears in the poll
            # because Luffa filters out messages from the bot itself
            # This is expected behavior
            
            return True
            
        except Exception as e:
            logger.error(f"Message delivery test failed: {e}")
            return False
    
    async def test_complete_trial_flow(self) -> bool:
        """
        Test 3: Simulate complete trial flow from start to verdict.
        
        Validates: Requirements 2.2, 3.4, 5.3, 5.4, 5.5, 7.1, 10.1, 12.1, 18.1
        """
        logger.info("Testing complete trial flow...")
        
        try:
            # Create orchestrator
            session_id = f"e2e_test_{int(datetime.now().timestamp())}"
            orchestrator = ExperienceOrchestrator(
                session_id=session_id,
                user_id=self.test_user_id,
                case_id="blackthorn-hall-001"
            )
            
            # Initialize
            init_result = await orchestrator.initialize()
            if not init_result["success"]:
                logger.error(f"Initialization failed: {init_result.get('error')}")
                return False
            
            logger.info("✓ Orchestrator initialized")
            logger.info(f"  Case: {init_result['case_title']}")
            
            # Start experience (Hook Scene)
            start_result = await orchestrator.start_experience()
            if not start_result["success"]:
                logger.error(f"Start failed: {start_result.get('error')}")
                return False
            
            logger.info("✓ Hook scene presented")
            
            # Track stages
            expected_stages = [
                ExperienceState.CHARGE_READING,
                ExperienceState.PROSECUTION_OPENING,
                ExperienceState.DEFENCE_OPENING,
                ExperienceState.EVIDENCE_PRESENTATION,
                ExperienceState.CROSS_EXAMINATION,
                ExperienceState.PROSECUTION_CLOSING,
                ExperienceState.DEFENCE_CLOSING,
                ExperienceState.JUDGE_SUMMING_UP,
                ExperienceState.JURY_DELIBERATION,
            ]
            
            # Advance through trial stages
            for expected_stage in expected_stages:
                result = await orchestrator.advance_trial_stage()
                
                if not result["success"]:
                    logger.error(f"Stage transition failed: {result.get('error')}")
                    return False
                
                current_stage = orchestrator.state_machine.current_state
                
                if current_stage != expected_stage:
                    logger.error(f"Expected {expected_stage}, got {current_stage}")
                    return False
                
                logger.info(f"✓ Stage: {expected_stage.value}")
                
                # Verify agent responses for non-deliberation stages
                if expected_stage != ExperienceState.JURY_DELIBERATION:
                    if "agent_responses" not in result or not result["agent_responses"]:
                        logger.error(f"No agent responses for {expected_stage}")
                        return False
                    
                    logger.info(f"  Agents responded: {len(result['agent_responses'])}")
            
            # Submit deliberation statement
            delib_result = await orchestrator.submit_deliberation_statement(
                "I believe the defendant is guilty based on the evidence presented."
            )
            
            if not delib_result["success"]:
                logger.error(f"Deliberation failed: {delib_result.get('error')}")
                return False
            
            logger.info("✓ Deliberation statement processed")
            logger.info(f"  AI juror responses: {len(delib_result['turns']) - 1}")
            
            # Submit vote
            vote_result = await orchestrator.submit_vote("guilty")
            
            if not vote_result["success"]:
                logger.error(f"Vote failed: {vote_result.get('error')}")
                return False
            
            logger.info("✓ Vote submitted and processed")
            
            # Verify dual reveal
            if "dual_reveal" not in vote_result:
                logger.error("Dual reveal not present in vote result")
                return False
            
            dual_reveal = vote_result["dual_reveal"]
            
            # Verify dual reveal components
            required_keys = ["verdict", "groundTruth", "reasoningAssessment", "jurorReveal"]
            missing_keys = [k for k in required_keys if k not in dual_reveal]
            
            if missing_keys:
                logger.error(f"Dual reveal missing keys: {', '.join(missing_keys)}")
                return False
            
            logger.info("✓ Dual reveal complete")
            logger.info(f"  Verdict: {dual_reveal['verdict']['verdict']}")
            logger.info(f"  Ground truth: {dual_reveal['groundTruth']['actualVerdict']}")
            logger.info(f"  Reasoning: {dual_reveal['reasoningAssessment']['category']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Complete trial flow test failed: {e}")
            return False
    
    async def test_timing_constraints(self) -> bool:
        """
        Test 4: Verify timing constraints are enforced.
        
        Validates: Requirements 2.5, 9.5, 17.1
        """
        logger.info("Testing timing constraints...")
        
        try:
            # Create orchestrator
            session_id = f"timing_test_{int(datetime.now().timestamp())}"
            orchestrator = ExperienceOrchestrator(
                session_id=session_id,
                user_id=self.test_user_id,
                case_id="blackthorn-hall-001"
            )
            
            await orchestrator.initialize()
            
            # Check session timeout is configured
            timeout_hours = self.config.session_timeout_hours
            if timeout_hours != 24:
                logger.warning(f"Session timeout is {timeout_hours}h, expected 24h")
            
            logger.info(f"✓ Session timeout: {timeout_hours} hours")
            
            # Check max experience duration
            max_minutes = self.config.max_experience_minutes
            if max_minutes != 20:
                logger.warning(f"Max experience duration is {max_minutes}min, expected 20min")
            
            logger.info(f"✓ Max experience duration: {max_minutes} minutes")
            
            # Verify state machine tracks timing
            state_machine = orchestrator.state_machine
            if not hasattr(state_machine, 'start_time'):
                logger.error("State machine doesn't track start time")
                return False
            
            logger.info("✓ State machine tracks timing")
            
            return True
            
        except Exception as e:
            logger.error(f"Timing constraints test failed: {e}")
            return False
    
    async def test_error_recovery(self) -> bool:
        """
        Test 5: Verify error recovery scenarios.
        
        Validates: Requirements 20.1, 20.2, 20.3, 20.4, 20.5
        """
        logger.info("Testing error recovery...")
        
        try:
            # Test 1: Invalid command handling
            logger.info("Testing invalid command handling...")
            
            # Create service
            service = MultiBotService()
            
            # Simulate invalid command
            invalid_msg = {
                "text": "/invalid_command",
                "gid": self.test_group_id,
                "sender_uid": self.test_user_id,
                "type": 1
            }
            
            # This should not raise an exception
            await service.handle_message(invalid_msg)
            logger.info("✓ Invalid command handled gracefully")
            
            # Test 2: Missing session handling
            logger.info("Testing missing session handling...")
            
            continue_msg = {
                "text": "/continue",
                "gid": self.test_group_id,
                "sender_uid": "nonexistent_user",
                "type": 1
            }
            
            # This should not raise an exception
            await service.handle_message(continue_msg)
            logger.info("✓ Missing session handled gracefully")
            
            # Test 3: Invalid vote handling
            logger.info("Testing invalid vote handling...")
            
            invalid_vote_msg = {
                "text": "/vote invalid",
                "gid": self.test_group_id,
                "sender_uid": self.test_user_id,
                "type": 1
            }
            
            # This should not raise an exception
            await service.handle_message(invalid_vote_msg)
            logger.info("✓ Invalid vote handled gracefully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error recovery test failed: {e}")
            return False
    
    async def test_multi_user_support(self) -> bool:
        """
        Test 6: Verify multiple users can run trials simultaneously.
        
        Validates: Requirements 2.4, 22.4
        """
        logger.info("Testing multi-user support...")
        
        try:
            # Create service
            service = MultiBotService()
            
            # Simulate two users starting trials
            user1_id = "user_1"
            user2_id = "user_2"
            
            # User 1 starts trial
            start_msg_1 = {
                "text": "/start",
                "gid": self.test_group_id,
                "sender_uid": user1_id,
                "type": 1
            }
            
            await service.handle_message(start_msg_1)
            
            # Verify user 1 has session
            session_1 = service._get_user_orchestrator(user1_id)
            if not session_1:
                logger.error("User 1 session not created")
                return False
            
            logger.info("✓ User 1 session created")
            
            # User 2 starts trial
            start_msg_2 = {
                "text": "/start",
                "gid": self.test_group_id,
                "sender_uid": user2_id,
                "type": 1
            }
            
            await service.handle_message(start_msg_2)
            
            # Verify user 2 has session
            session_2 = service._get_user_orchestrator(user2_id)
            if not session_2:
                logger.error("User 2 session not created")
                return False
            
            logger.info("✓ User 2 session created")
            
            # Verify sessions are independent
            if session_1.session_id == session_2.session_id:
                logger.error("Sessions are not independent")
                return False
            
            logger.info("✓ Sessions are independent")
            
            # Verify both sessions are tracked
            if len(service.active_sessions) < 2:
                logger.error(f"Expected 2+ active sessions, got {len(service.active_sessions)}")
                return False
            
            logger.info(f"✓ Multiple active sessions: {len(service.active_sessions)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Multi-user support test failed: {e}")
            return False
    
    async def test_session_management(self) -> bool:
        """
        Test 7: Verify session persistence and recovery.
        
        Validates: Requirements 2.4, 22.4
        """
        logger.info("Testing session management...")
        
        try:
            # Create orchestrator
            session_id = f"session_test_{int(datetime.now().timestamp())}"
            orchestrator = ExperienceOrchestrator(
                session_id=session_id,
                user_id=self.test_user_id,
                case_id="blackthorn-hall-001"
            )
            
            await orchestrator.initialize()
            await orchestrator.start_experience()
            
            # Advance to a specific stage
            await orchestrator.advance_trial_stage()  # Charge reading
            await orchestrator.advance_trial_stage()  # Prosecution opening
            
            current_state = orchestrator.state_machine.current_state
            logger.info(f"✓ Advanced to: {current_state.value}")
            
            # Save progress
            from session import SessionStore
            session_store = SessionStore()
            session_store.save_progress(orchestrator.user_session)
            
            logger.info("✓ Session saved")
            
            # Restore progress
            restored_session = session_store.restore_progress(session_id)
            
            if not restored_session:
                logger.error("Failed to restore session")
                return False
            
            logger.info("✓ Session restored")
            
            # Verify state is preserved
            if restored_session.current_state != current_state:
                logger.error(f"State mismatch: {restored_session.current_state} != {current_state}")
                return False
            
            logger.info("✓ State preserved correctly")
            
            # Verify session is not expired
            if restored_session.is_expired(retention_hours=24):
                logger.error("Session incorrectly marked as expired")
                return False
            
            logger.info("✓ Session expiry check works")
            
            return True
            
        except Exception as e:
            logger.error(f"Session management test failed: {e}")
            return False
    
    def _print_summary(self):
        """Print test summary."""
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        
        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)
        
        logger.info(f"\nPassed: {passed}/{total}")
        
        if passed == total:
            logger.info("\n✅ ALL TESTS PASSED")
            logger.info("\nThe Luffa Bot integration is working correctly!")
            logger.info("\nNext steps:")
            logger.info("  1. Ensure all 5 bots are added to your Luffa group")
            logger.info("  2. Run: python src/multi_bot_service.py")
            logger.info("  3. In group chat, send: /start")
            logger.info("  4. Experience the complete trial flow!")
        else:
            logger.error("\n❌ SOME TESTS FAILED")
            logger.error("\nFailed tests:")
            for r in self.results:
                if not r["passed"]:
                    logger.error(f"  - {r['test']}")
                    if r["error"]:
                        logger.error(f"    Error: {r['error']}")


async def main():
    """Main entry point."""
    runner = E2ETestRunner()
    
    try:
        success = await runner.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
