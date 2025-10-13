"""
Optimized CTF Agent for Round 1 Competition
Implements all advanced strategies:
- Tiered LLM usage (Tier 0-3) for cost optimization
- Ensemble agent architecture (4-7 agents in parallel)
- Validation layer (97.1% false positive prevention)
- Script generation (164% improvement strategy)
- Domain knowledge integration
- MCP tool integrations
"""

import asyncio
import logging
from typing import Optional

from helper.ctf_challenge import CTFChallengeClient
from helper.llm_helper import LiteLLMManager
from helper.agent_boilerplate import AgentInterface
from agent.ensemble_agent import EnsembleAgent
from helper.validation_layer import ComprehensiveValidator, ScriptGenerationValidator
from helper.tiered_llm_manager import TieredLLMManager
from mcp_tools.ghidra_mcp import GhidraMCP
from mcp_tools.kali_mcp import KaliMCP

class OptimizedCTFAgent(AgentInterface):
    """
    Production-ready CTF agent implementing all advanced strategies.

    Features:
    - Cost-optimized LLM usage with $0.50 budget limit
    - Ensemble of specialized agents running in parallel
    - Comprehensive validation to prevent false positives
    - Tool integration for automated analysis
    - Domain-specific knowledge bases
    """

    def __init__(self, lite_llm_manager: LiteLLMManager, budget_limit: float = 0.50,
                 logger: Optional[logging.Logger] = None):
        self.lite_llm_manager = lite_llm_manager
        self.budget_limit = budget_limit
        self.logger = logger or logging.getLogger(__name__)

        # Initialize ensemble agent with distributed budget
        self.ensemble_agent = EnsembleAgent(lite_llm_manager, budget_limit * 0.8, logger)  # 80% for ensemble

        # Initialize validation layer
        self.validator = ComprehensiveValidator(use_docker=True, timeout=30)
        self.script_validator = ScriptGenerationValidator(self.validator, max_iterations=2)

        # Initialize tool integrations
        self.ghidra_mcp = GhidraMCP()
        self.kali_mcp = KaliMCP()

        # Initialize tiered LLM manager for fallback
        self.fallback_llm = TieredLLMManager(lite_llm_manager, budget_limit * 0.2)  # 20% for fallback

    async def solve_challenge(self, challenge: CTFChallengeClient) -> Optional[str]:
        """
        Main challenge solving method using ensemble approach.
        """
        self.logger.info(f"OptimizedCTFAgent solving: {challenge.challenge.name}")
        self.logger.info(f"Categories: {challenge.challenge.categories}")
        self.logger.info(f"Budget limit: ${self.budget_limit}")

        try:
            # Step 1: Pre-analysis using tools (Tier 0 equivalent)
            tool_results = await self._pre_analyze_with_tools(challenge)

            # Step 2: Run ensemble agents in parallel
            self.logger.info("Starting ensemble agent analysis...")
            ensemble_result = await self.ensemble_agent.solve_challenge(challenge)

            if ensemble_result:
                self.logger.info(f"Ensemble agents found solution: {ensemble_result}")
                return ensemble_result

            # Step 3: Fallback analysis if ensemble fails
            self.logger.info("Ensemble failed, trying fallback analysis...")
            fallback_result = await self._fallback_analysis(challenge, tool_results)

            if fallback_result:
                self.logger.info(f"Fallback analysis found solution: {fallback_result}")
                return fallback_result

            # Step 4: Last resort - manual pattern analysis
            self.logger.info("Trying manual pattern analysis as last resort...")
            manual_result = self._manual_pattern_analysis(challenge, tool_results)

            if manual_result:
                self.logger.info(f"Manual analysis found solution: {manual_result}")
                return manual_result

            self.logger.warning("All methods failed to find a solution")
            return None

        except Exception as e:
            self.logger.error(f"Agent execution failed: {e}", exc_info=True)
            return None

    async def _pre_analyze_with_tools(self, challenge: CTFChallengeClient) -> dict:
        """Pre-analyze challenge using automated tools."""
        self.logger.info("Running pre-analysis with automated tools...")

        results = {
            'files_analyzed': [],
            'flags_found': [],
            'tool_outputs': {}
        }

        try:
            # Get all files in working directory
            from pathlib import Path
            working_path = Path(challenge.working_folder)

            for file_path in working_path.rglob('*'):
                if file_path.is_file():
                    file_str = str(file_path)
                    results['files_analyzed'].append(file_str)

                    # Determine file type and apply appropriate tools
                    if any(ext in file_str.lower() for ext in ['.exe', '.elf', '.bin']):
                        # Binary analysis
                        ghidra_result = self.ghidra_mcp.analyze_binary(file_str, "quick")
                        results['tool_outputs'][file_str] = ghidra_result

                        # Extract flags from Ghidra analysis
                        flags = self.ghidra_mcp.extract_flag_candidates(file_str)
                        results['flags_found'].extend(flags)

                    else:
                        # General file analysis
                        kali_result = self.kali_mcp.auto_analyze_file(file_str)
                        results['tool_outputs'][file_str] = kali_result

                        # Extract flags from Kali analysis
                        flags = self.kali_mcp.extract_flags_from_results(kali_result)
                        results['flags_found'].extend(flags)

            # Try immediate flag validation
            for flag in results['flags_found']:
                if challenge.submit_flag(flag):
                    self.logger.info(f"Pre-analysis found correct flag: {flag}")
                    results['correct_flag'] = flag
                    return results

        except Exception as e:
            self.logger.warning(f"Pre-analysis failed: {e}")

        self.logger.info(f"Pre-analysis complete. Found {len(results['flags_found'])} flag candidates.")
        return results

    async def _fallback_analysis(self, challenge: CTFChallengeClient, tool_results: dict) -> Optional[str]:
        """Fallback analysis using tiered LLM approach."""
        self.logger.info("Starting fallback analysis with tiered LLM...")

        try:
            # Build context from tool results
            context = {
                'name': challenge.challenge.name,
                'description': challenge.challenge.description,
                'categories': challenge.challenge.categories,
                'flag_regex': challenge.challenge.flag_regex,
                'tool_results': tool_results,
                'files': tool_results.get('files_analyzed', [])
            }

            # Start with Tier 0 (free tools) - already done in pre-analysis

            # Try Tier 1 (cheap) analysis
            if self.fallback_llm.check_budget(0.05):
                tier_1_result = self.fallback_llm.execute_tier_1_analysis(context, tool_results)

                if tier_1_result.success:
                    flag = self._extract_flag_from_response(tier_1_result.result, challenge.challenge.flag_regex)
                    if flag and challenge.submit_flag(flag):
                        return flag

            # Try Tier 2 (mid-tier) for script generation
            if self.fallback_llm.check_budget(0.15):
                tier_2_result = self.fallback_llm.execute_tier_2_exploitation(context, [])

                if tier_2_result.success and isinstance(tier_2_result.result, dict):
                    script = tier_2_result.result.get('script')
                    if script:
                        # Validate and execute script
                        success, flag, final_script = self.script_validator.validate_and_improve_script(
                            script, challenge.working_folder, context, self.lite_llm_manager.create_client()
                        )

                        if success and flag and challenge.submit_flag(flag):
                            return flag

            # Try Tier 3 (expensive) as last resort
            remaining_budget = self.fallback_llm.get_remaining_budget()
            if remaining_budget > 0.10:
                tier_3_result = self.fallback_llm.execute_tier_3_advanced(context, [])

                if tier_3_result.success:
                    flag = self._extract_flag_from_response(tier_3_result.result, challenge.challenge.flag_regex)
                    if flag and challenge.submit_flag(flag):
                        return flag

        except Exception as e:
            self.logger.error(f"Fallback analysis failed: {e}")

        return None

    def _manual_pattern_analysis(self, challenge: CTFChallengeClient, tool_results: dict) -> Optional[str]:
        """Manual pattern analysis as last resort."""
        self.logger.info("Performing manual pattern analysis...")

        try:
            # Check tool results for obvious patterns
            all_flags = tool_results.get('flags_found', [])

            # Try each flag candidate
            for flag in all_flags:
                if challenge.submit_flag(flag):
                    return flag

            # Manual file content analysis
            from pathlib import Path
            import re
            import base64

            working_path = Path(challenge.working_folder)

            for file_path in working_path.rglob('*'):
                if file_path.is_file() and file_path.stat().st_size < 1024 * 1024:  # Max 1MB
                    try:
                        # Try reading as text
                        content = file_path.read_text(errors='ignore')

                        # Direct flag search
                        flag_matches = re.findall(challenge.challenge.flag_regex, content, re.IGNORECASE)
                        for flag in flag_matches:
                            if challenge.submit_flag(flag):
                                return flag

                        # Base64 decoding attempts
                        base64_patterns = re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', content)
                        for b64_str in base64_patterns:
                            try:
                                decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                                flag_matches = re.findall(challenge.challenge.flag_regex, decoded, re.IGNORECASE)
                                for flag in flag_matches:
                                    if challenge.submit_flag(flag):
                                        return flag
                            except:
                                continue

                        # ROT13 attempts
                        import codecs
                        rot13_content = codecs.encode(content, 'rot13')
                        flag_matches = re.findall(challenge.challenge.flag_regex, rot13_content, re.IGNORECASE)
                        for flag in flag_matches:
                            if challenge.submit_flag(flag):
                                return flag

                    except Exception as e:
                        continue

        except Exception as e:
            self.logger.error(f"Manual pattern analysis failed: {e}")

        return None

    def _extract_flag_from_response(self, response: str, flag_regex: str) -> Optional[str]:
        """Extract flag from LLM response using regex."""
        import re
        if isinstance(response, str):
            match = re.search(flag_regex, response)
            if match:
                return match.group(0)
        return None

    def log(self, message: str):
        """Compatibility method for logging."""
        if hasattr(self, 'logger') and self.logger:
            self.logger.info(message)
        else:
            print(message)

# Synchronous wrapper for compatibility
class SyncOptimizedAgent(AgentInterface):
    """Synchronous wrapper for the optimized agent."""

    def __init__(self, lite_llm_manager: LiteLLMManager, logger: Optional[logging.Logger] = None,
                 budget_limit: float = 0.50):
        self.async_agent = OptimizedCTFAgent(lite_llm_manager, budget_limit, logger)

    def solve_challenge(self, challenge: CTFChallengeClient) -> Optional[str]:
        """Synchronous solve method."""
        return asyncio.run(self.async_agent.solve_challenge(challenge))

# Export the agent class for compatibility
Agent = SyncOptimizedAgent