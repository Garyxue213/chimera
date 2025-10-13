"""
Ensemble CTF Agent Architecture
Implements 4-7 agents running in parallel as recommended by research:
- Fast/Simple Agent: Quick pattern matching and basic techniques
- Reasoning Agent: Deep analysis and complex problem solving
- Code-Focused Agent: Script generation and technical implementation
- Specialist Agents: Category-specific experts (crypto, web, rev, pwn)

Research shows: "no single agent solved everything" - diversity beats single approach
Simple AIDER agent had only 12.5% success but solved problems complex agents overcomplicated
"""

import asyncio
import concurrent.futures
import logging
import time
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from helper.ctf_challenge import CTFChallengeClient
from helper.tiered_llm_manager import TieredLLMManager, LLMTier, TierResult
from helper.llm_helper import LiteLLMManager

@dataclass
class AgentResult:
    agent_name: str
    success: bool
    flag: Optional[str]
    confidence: float
    execution_time: float
    cost: float
    method: str
    details: Dict[str, Any]

class KnowledgeBaseManager:
    """Manages structured knowledge files for domain expertise."""

    def __init__(self, knowledge_base_dir: str = "knowledge_base"):
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.knowledge_cache = {}

    def load_knowledge(self, category: str) -> Dict[str, Any]:
        """Load knowledge base for specific category."""
        if category in self.knowledge_cache:
            return self.knowledge_cache[category]

        knowledge_file = self.knowledge_base_dir / f"{category}_knowledge.xml"
        if not knowledge_file.exists():
            return {}

        try:
            tree = ET.parse(knowledge_file)
            root = tree.getroot()

            knowledge = {
                'vulnerability_types': {},
                'tools': {},
                'patterns': {},
                'payloads': {}
            }

            # Parse vulnerability types
            for vuln_type in root.findall('.//vulnerability_type'):
                name = vuln_type.get('name')
                knowledge['vulnerability_types'][name] = {
                    'patterns': [p.text for p in vuln_type.findall('.//pattern')],
                    'exploitation_guide': [s.text for s in vuln_type.findall('.//step')],
                    'payloads': {p.get('type'): p.text for p in vuln_type.findall('.//payload')},
                    'detection_patterns': [p.text for p in vuln_type.findall('.//detection_patterns/pattern')]
                }

            # Parse tools
            for tool in root.findall('.//tool'):
                name = tool.get('name')
                knowledge['tools'][name] = {
                    'description': tool.find('description').text if tool.find('description') is not None else '',
                    'use_cases': tool.find('use_cases').text if tool.find('use_cases') is not None else ''
                }

            # Parse common patterns
            for pattern in root.findall('.//common_ctf_patterns/pattern'):
                name = pattern.get('name')
                knowledge['patterns'][name] = {
                    'description': pattern.find('description').text if pattern.find('description') is not None else '',
                    'solution': pattern.find('solution').text if pattern.find('solution') is not None else ''
                }

            self.knowledge_cache[category] = knowledge
            return knowledge

        except Exception as e:
            logging.error(f"Failed to load knowledge base for {category}: {e}")
            return {}

class FastSimpleAgent:
    """
    Fast/Simple Agent: Quick pattern matching and basic techniques.
    Focuses on obvious solutions that complex agents might overcomplicate.
    """

    def __init__(self, llm_manager: TieredLLMManager, knowledge_manager: KnowledgeBaseManager):
        self.llm_manager = llm_manager
        self.knowledge_manager = knowledge_manager
        self.logger = logging.getLogger(f"{__name__}.FastSimpleAgent")

    async def solve(self, challenge: CTFChallengeClient) -> AgentResult:
        start_time = time.time()

        try:
            # Always start with Tier 0 (free tools)
            tier_0_result = self.llm_manager.execute_tier_0_tools({
                'categories': challenge.challenge.categories,
                'files': self._get_files(challenge.working_folder),
                'name': challenge.challenge.name,
                'description': challenge.challenge.description
            })

            if tier_0_result.success and tier_0_result.result:
                # Check if we found a flag directly
                if isinstance(tier_0_result.result, str) and 'flag{' in tier_0_result.result.lower():
                    return AgentResult(
                        agent_name="FastSimple",
                        success=True,
                        flag=tier_0_result.result,
                        confidence=tier_0_result.confidence,
                        execution_time=time.time() - start_time,
                        cost=0.0,
                        method="tier_0_direct",
                        details={"tier_0_output": tier_0_result.result}
                    )

            # Quick pattern matching for common CTF patterns
            flag = self._quick_pattern_analysis(challenge, tier_0_result.result)
            if flag:
                return AgentResult(
                    agent_name="FastSimple",
                    success=True,
                    flag=flag,
                    confidence=0.8,
                    execution_time=time.time() - start_time,
                    cost=0.0,
                    method="pattern_matching",
                    details={"tier_0_output": tier_0_result.result}
                )

            # Use Tier 1 (cheap) for basic analysis only
            if self.llm_manager.check_budget(0.05):
                tier_1_result = self.llm_manager.execute_tier_1_analysis(
                    {
                        'categories': challenge.challenge.categories,
                        'name': challenge.challenge.name,
                        'description': challenge.challenge.description
                    },
                    tier_0_result.result if isinstance(tier_0_result.result, dict) else {}
                )

                if tier_1_result.success:
                    # Simple flag extraction from LLM response
                    flag = self._extract_flag_from_response(tier_1_result.result, challenge.challenge.flag_regex)
                    if flag:
                        return AgentResult(
                            agent_name="FastSimple",
                            success=True,
                            flag=flag,
                            confidence=tier_1_result.confidence,
                            execution_time=time.time() - start_time,
                            cost=tier_1_result.cost,
                            method="tier_1_simple",
                            details={"llm_response": tier_1_result.result}
                        )

            return AgentResult(
                agent_name="FastSimple",
                success=False,
                flag=None,
                confidence=0.0,
                execution_time=time.time() - start_time,
                cost=self.llm_manager.total_spent,
                method="no_solution",
                details={}
            )

        except Exception as e:
            self.logger.error(f"FastSimple agent failed: {e}")
            return AgentResult(
                agent_name="FastSimple",
                success=False,
                flag=None,
                confidence=0.0,
                execution_time=time.time() - start_time,
                cost=0.0,
                method="error",
                details={"error": str(e)}
            )

    def _get_files(self, working_folder: str) -> List[str]:
        """Get list of files in working folder."""
        try:
            return [str(f) for f in Path(working_folder).rglob('*') if f.is_file()]
        except:
            return []

    def _quick_pattern_analysis(self, challenge: CTFChallengeClient, tool_results: Dict[str, Any]) -> Optional[str]:
        """Quick pattern matching for common CTF solutions."""
        import re

        # Check for flags in tool output
        if isinstance(tool_results, dict):
            for tool, output in tool_results.items():
                if isinstance(output, str):
                    flag_match = re.search(challenge.challenge.flag_regex, output)
                    if flag_match:
                        return flag_match.group(0)

        # Common simple patterns
        categories = challenge.challenge.categories

        # Base64 pattern
        if 'crypto' in categories:
            for file_path in self._get_files(challenge.working_folder):
                try:
                    content = Path(file_path).read_text(errors='ignore')
                    # Check for base64 patterns
                    import base64
                    if re.match(r'^[A-Za-z0-9+/]*={0,2}$', content.strip()):
                        try:
                            decoded = base64.b64decode(content.strip()).decode('utf-8', errors='ignore')
                            flag_match = re.search(challenge.challenge.flag_regex, decoded)
                            if flag_match:
                                return flag_match.group(0)
                        except:
                            pass
                except:
                    pass

        return None

    def _extract_flag_from_response(self, response: str, flag_regex: str) -> Optional[str]:
        """Extract flag from LLM response using regex."""
        import re
        if isinstance(response, str):
            match = re.search(flag_regex, response)
            if match:
                return match.group(0)
        return None

class ReasoningAgent:
    """
    Reasoning Agent: Deep analysis and complex problem solving.
    Uses advanced LLM capabilities for multi-step reasoning.
    """

    def __init__(self, llm_manager: TieredLLMManager, knowledge_manager: KnowledgeBaseManager):
        self.llm_manager = llm_manager
        self.knowledge_manager = knowledge_manager
        self.logger = logging.getLogger(f"{__name__}.ReasoningAgent")

    async def solve(self, challenge: CTFChallengeClient) -> AgentResult:
        start_time = time.time()

        try:
            # Load relevant knowledge
            knowledge = {}
            for category in challenge.challenge.categories:
                knowledge.update(self.knowledge_manager.load_knowledge(category))

            # Build context iteratively (multi-turn context building)
            context = self._build_challenge_context(challenge, knowledge)

            # Use Tier 2 for main reasoning work
            if self.llm_manager.check_budget(0.20):
                tier_2_result = self.llm_manager.execute_tier_2_exploitation(
                    context,
                    []  # Previous results - empty for reasoning agent
                )

                if tier_2_result.success:
                    # Try to execute any generated script
                    if isinstance(tier_2_result.result, dict) and 'script' in tier_2_result.result:
                        flag = await self._execute_generated_script(tier_2_result.result['script'], challenge)
                        if flag:
                            return AgentResult(
                                agent_name="Reasoning",
                                success=True,
                                flag=flag,
                                confidence=tier_2_result.confidence,
                                execution_time=time.time() - start_time,
                                cost=tier_2_result.cost,
                                method="script_execution",
                                details={"script": tier_2_result.result['script']}
                            )

                    # If Tier 2 doesn't solve it, escalate to Tier 3 for advanced reasoning
                    if self.llm_manager.check_budget(0.15):
                        tier_3_result = self.llm_manager.execute_tier_3_advanced(
                            context,
                            [tier_2_result]
                        )

                        if tier_3_result.success:
                            flag = self._extract_flag_from_response(tier_3_result.result, challenge.challenge.flag_regex)
                            if flag:
                                return AgentResult(
                                    agent_name="Reasoning",
                                    success=True,
                                    flag=flag,
                                    confidence=tier_3_result.confidence,
                                    execution_time=time.time() - start_time,
                                    cost=tier_2_result.cost + tier_3_result.cost,
                                    method="advanced_reasoning",
                                    details={"tier_3_analysis": tier_3_result.result}
                                )

            return AgentResult(
                agent_name="Reasoning",
                success=False,
                flag=None,
                confidence=0.0,
                execution_time=time.time() - start_time,
                cost=self.llm_manager.total_spent,
                method="reasoning_failed",
                details={}
            )

        except Exception as e:
            self.logger.error(f"Reasoning agent failed: {e}")
            return AgentResult(
                agent_name="Reasoning",
                success=False,
                flag=None,
                confidence=0.0,
                execution_time=time.time() - start_time,
                cost=0.0,
                method="error",
                details={"error": str(e)}
            )

    def _build_challenge_context(self, challenge: CTFChallengeClient, knowledge: Dict[str, Any]) -> Dict[str, Any]:
        """Build comprehensive context for reasoning."""
        return {
            'name': challenge.challenge.name,
            'description': challenge.challenge.description,
            'categories': challenge.challenge.categories,
            'files': self._get_files(challenge.working_folder),
            'flag_regex': challenge.challenge.flag_regex,
            'knowledge': knowledge,
            'network_info': challenge.network_info
        }

    def _get_files(self, working_folder: str) -> List[str]:
        """Get list of files in working folder."""
        try:
            return [str(f) for f in Path(working_folder).rglob('*') if f.is_file()]
        except:
            return []

    async def _execute_generated_script(self, script: str, challenge: CTFChallengeClient) -> Optional[str]:
        """Safely execute generated Python script."""
        import tempfile
        import subprocess
        import re

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script)
                script_path = f.name

            # Execute script in working directory
            result = subprocess.run(
                ['python', script_path],
                cwd=challenge.working_folder,
                capture_output=True,
                text=True,
                timeout=30
            )

            # Look for flag in output
            output = result.stdout + result.stderr
            flag_match = re.search(challenge.challenge.flag_regex, output)
            if flag_match:
                return flag_match.group(0)

        except Exception as e:
            self.logger.debug(f"Script execution failed: {e}")

        return None

    def _extract_flag_from_response(self, response: str, flag_regex: str) -> Optional[str]:
        """Extract flag from LLM response using regex."""
        import re
        if isinstance(response, str):
            match = re.search(flag_regex, response)
            if match:
                return match.group(0)
        return None

class CodeFocusedAgent:
    """
    Code-Focused Agent: Script generation and technical implementation.
    Specializes in generating executable solutions and exploits.
    """

    def __init__(self, llm_manager: TieredLLMManager, knowledge_manager: KnowledgeBaseManager):
        self.llm_manager = llm_manager
        self.knowledge_manager = knowledge_manager
        self.logger = logging.getLogger(f"{__name__}.CodeFocusedAgent")

    async def solve(self, challenge: CTFChallengeClient) -> AgentResult:
        start_time = time.time()

        try:
            # Always prioritize script generation (164% improvement strategy)
            context = self._build_technical_context(challenge)

            # Use Tier 2 for script generation
            if self.llm_manager.check_budget(0.25):
                tier_2_result = self.llm_manager.execute_tier_2_exploitation(context, [])

                if tier_2_result.success and isinstance(tier_2_result.result, dict):
                    script = tier_2_result.result.get('script')
                    if script:
                        # Execute and validate script
                        flag = await self._execute_and_validate_script(script, challenge)
                        if flag:
                            return AgentResult(
                                agent_name="CodeFocused",
                                success=True,
                                flag=flag,
                                confidence=0.9,  # High confidence for script-based solutions
                                execution_time=time.time() - start_time,
                                cost=tier_2_result.cost,
                                method="validated_script",
                                details={"script": script, "execution_success": True}
                            )
                        else:
                            # Script didn't work, try iterative refinement
                            refined_flag = await self._refine_script(script, challenge, tier_2_result.cost)
                            if refined_flag:
                                return AgentResult(
                                    agent_name="CodeFocused",
                                    success=True,
                                    flag=refined_flag,
                                    confidence=0.8,
                                    execution_time=time.time() - start_time,
                                    cost=self.llm_manager.total_spent,
                                    method="refined_script",
                                    details={"original_script": script, "refinement_applied": True}
                                )

            return AgentResult(
                agent_name="CodeFocused",
                success=False,
                flag=None,
                confidence=0.0,
                execution_time=time.time() - start_time,
                cost=self.llm_manager.total_spent,
                method="script_generation_failed",
                details={}
            )

        except Exception as e:
            self.logger.error(f"CodeFocused agent failed: {e}")
            return AgentResult(
                agent_name="CodeFocused",
                success=False,
                flag=None,
                confidence=0.0,
                execution_time=time.time() - start_time,
                cost=0.0,
                method="error",
                details={"error": str(e)}
            )

    def _build_technical_context(self, challenge: CTFChallengeClient) -> Dict[str, Any]:
        """Build context focused on technical implementation."""
        return {
            'name': challenge.challenge.name,
            'description': challenge.challenge.description,
            'categories': challenge.challenge.categories,
            'files': self._analyze_files_technically(challenge.working_folder),
            'flag_regex': challenge.challenge.flag_regex,
            'network_info': challenge.network_info
        }

    def _analyze_files_technically(self, working_folder: str) -> Dict[str, Any]:
        """Analyze files with focus on technical details."""
        file_analysis = {}

        for file_path in Path(working_folder).rglob('*'):
            if file_path.is_file():
                try:
                    # Get file type and basic info
                    import subprocess
                    file_cmd = subprocess.run(['file', str(file_path)], capture_output=True, text=True)

                    analysis = {
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'type': file_cmd.stdout.strip() if file_cmd.returncode == 0 else 'unknown'
                    }

                    # Read first few bytes for pattern analysis
                    if file_path.stat().st_size < 10000:  # Only for small files
                        try:
                            with open(file_path, 'rb') as f:
                                analysis['header'] = f.read(64).hex()

                            # Try to read as text
                            try:
                                analysis['content_preview'] = file_path.read_text(encoding='utf-8', errors='ignore')[:500]
                            except:
                                pass
                        except:
                            pass

                    file_analysis[file_path.name] = analysis

                except Exception as e:
                    self.logger.debug(f"File analysis failed for {file_path}: {e}")

        return file_analysis

    async def _execute_and_validate_script(self, script: str, challenge: CTFChallengeClient) -> Optional[str]:
        """Execute script with comprehensive validation."""
        import tempfile
        import subprocess
        import re
        import ast

        try:
            # Basic syntax validation
            ast.parse(script)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script)
                script_path = f.name

            # Execute with timeout and capture all output
            result = subprocess.run(
                ['python', script_path],
                cwd=challenge.working_folder,
                capture_output=True,
                text=True,
                timeout=45
            )

            # Comprehensive flag extraction
            all_output = result.stdout + result.stderr

            # Look for flag patterns
            flag_match = re.search(challenge.challenge.flag_regex, all_output)
            if flag_match:
                candidate_flag = flag_match.group(0)

                # Validate flag by submitting it
                if challenge.submit_flag(candidate_flag):
                    return candidate_flag

            # Look for other potential flag patterns
            potential_flags = re.findall(r'flag\{[^}]+\}', all_output, re.IGNORECASE)
            for flag in potential_flags:
                if challenge.submit_flag(flag):
                    return flag

        except Exception as e:
            self.logger.debug(f"Script execution/validation failed: {e}")

        return None

    async def _refine_script(self, original_script: str, challenge: CTFChallengeClient, previous_cost: float) -> Optional[str]:
        """Refine script based on execution feedback."""
        if not self.llm_manager.check_budget(0.10):
            return None

        # Get execution error feedback
        import tempfile
        import subprocess

        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(original_script)
                script_path = f.name

            result = subprocess.run(
                ['python', script_path],
                cwd=challenge.working_folder,
                capture_output=True,
                text=True,
                timeout=30
            )

            error_feedback = f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}\nReturn code: {result.returncode}"

        except Exception as e:
            error_feedback = str(e)

        # Use LLM to refine script based on feedback
        refinement_prompt = f"""
        The following Python script failed to solve the CTF challenge correctly:

        ```python
        {original_script}
        ```

        Execution output:
        {error_feedback}

        Challenge details:
        - Name: {challenge.challenge.name}
        - Categories: {challenge.challenge.categories}
        - Flag format: {challenge.challenge.flag_regex}

        Fix the script to correctly solve the challenge. Focus on:
        1. Fixing any runtime errors
        2. Improving the exploitation logic
        3. Ensuring proper output formatting
        4. Adding debug output to understand execution

        Provide the corrected script in the same format:
        ```python
        # Fixed script
        [corrected script here]
        ```
        """

        try:
            client = self.llm_manager.llm_manager.create_client()
            response = client.simple_call("gemini-2.5-pro", refinement_prompt, temperature=0.2)

            # Extract refined script
            import re
            script_match = re.search(r'```python\s*\n(.*?)\n```', response.choices[0].message.content, re.DOTALL)
            if script_match:
                refined_script = script_match.group(1)

                # Execute refined script
                flag = await self._execute_and_validate_script(refined_script, challenge)
                return flag

        except Exception as e:
            self.logger.debug(f"Script refinement failed: {e}")

        return None

class SpecialistAgent:
    """
    Specialist Agent: Category-specific expert knowledge.
    Tailored for specific CTF categories with deep domain expertise.
    """

    def __init__(self, category: str, llm_manager: TieredLLMManager, knowledge_manager: KnowledgeBaseManager):
        self.category = category
        self.llm_manager = llm_manager
        self.knowledge_manager = knowledge_manager
        self.logger = logging.getLogger(f"{__name__}.SpecialistAgent.{category}")

    async def solve(self, challenge: CTFChallengeClient) -> AgentResult:
        start_time = time.time()

        # Only work on challenges in our specialty
        if self.category not in challenge.challenge.categories:
            return AgentResult(
                agent_name=f"Specialist-{self.category}",
                success=False,
                flag=None,
                confidence=0.0,
                execution_time=time.time() - start_time,
                cost=0.0,
                method="category_mismatch",
                details={"expected_category": self.category, "actual_categories": challenge.challenge.categories}
            )

        try:
            # Load specialized knowledge
            knowledge = self.knowledge_manager.load_knowledge(self.category)

            # Apply category-specific logic
            if self.category == "crypto":
                return await self._solve_crypto(challenge, knowledge, start_time)
            elif self.category == "web":
                return await self._solve_web(challenge, knowledge, start_time)
            elif self.category == "rev":
                return await self._solve_rev(challenge, knowledge, start_time)
            elif self.category == "pwn":
                return await self._solve_pwn(challenge, knowledge, start_time)
            else:
                return await self._solve_generic(challenge, knowledge, start_time)

        except Exception as e:
            self.logger.error(f"Specialist-{self.category} agent failed: {e}")
            return AgentResult(
                agent_name=f"Specialist-{self.category}",
                success=False,
                flag=None,
                confidence=0.0,
                execution_time=time.time() - start_time,
                cost=0.0,
                method="error",
                details={"error": str(e)}
            )

    async def _solve_crypto(self, challenge: CTFChallengeClient, knowledge: Dict[str, Any], start_time: float) -> AgentResult:
        """Crypto-specific solving logic."""
        # Implement crypto-specific techniques based on knowledge base
        # This would include automated cipher detection, key analysis, etc.
        return await self._solve_generic(challenge, knowledge, start_time)

    async def _solve_web(self, challenge: CTFChallengeClient, knowledge: Dict[str, Any], start_time: float) -> AgentResult:
        """Web-specific solving logic."""
        # Implement web-specific techniques: SQL injection, XSS, etc.
        return await self._solve_generic(challenge, knowledge, start_time)

    async def _solve_rev(self, challenge: CTFChallengeClient, knowledge: Dict[str, Any], start_time: float) -> AgentResult:
        """Reverse engineering specific solving logic."""
        return await self._solve_generic(challenge, knowledge, start_time)

    async def _solve_pwn(self, challenge: CTFChallengeClient, knowledge: Dict[str, Any], start_time: float) -> AgentResult:
        """Binary exploitation specific solving logic."""
        return await self._solve_generic(challenge, knowledge, start_time)

    async def _solve_generic(self, challenge: CTFChallengeClient, knowledge: Dict[str, Any], start_time: float) -> AgentResult:
        """Generic specialist solving using knowledge base."""
        # Use specialized knowledge with tier 1/2 LLM
        if not self.llm_manager.check_budget(0.15):
            return AgentResult(
                agent_name=f"Specialist-{self.category}",
                success=False,
                flag=None,
                confidence=0.0,
                execution_time=time.time() - start_time,
                cost=0.0,
                method="budget_exceeded",
                details={}
            )

        context = {
            'name': challenge.challenge.name,
            'description': challenge.challenge.description,
            'categories': challenge.challenge.categories,
            'specialized_knowledge': knowledge,
            'flag_regex': challenge.challenge.flag_regex
        }

        tier_2_result = self.llm_manager.execute_tier_2_exploitation(context, [])

        if tier_2_result.success:
            flag = self._extract_flag_from_response(tier_2_result.result, challenge.challenge.flag_regex)
            if flag:
                return AgentResult(
                    agent_name=f"Specialist-{self.category}",
                    success=True,
                    flag=flag,
                    confidence=tier_2_result.confidence,
                    execution_time=time.time() - start_time,
                    cost=tier_2_result.cost,
                    method="specialist_knowledge",
                    details={"knowledge_applied": True}
                )

        return AgentResult(
            agent_name=f"Specialist-{self.category}",
            success=False,
            flag=None,
            confidence=0.0,
            execution_time=time.time() - start_time,
            cost=tier_2_result.cost if tier_2_result else 0.0,
            method="specialist_failed",
            details={}
        )

    def _extract_flag_from_response(self, response: str, flag_regex: str) -> Optional[str]:
        """Extract flag from LLM response using regex."""
        import re
        if isinstance(response, str):
            match = re.search(flag_regex, response)
            if match:
                return match.group(0)
        return None

class EnsembleAgent:
    """
    Main Ensemble Agent that coordinates multiple specialized agents.
    Runs 4-7 agents in parallel and takes the first successful solution.
    """

    def __init__(self, lite_llm_manager: LiteLLMManager, budget_limit: float = 0.50, logger: Optional[logging.Logger] = None):
        self.lite_llm_manager = lite_llm_manager
        self.budget_limit = budget_limit
        self.logger = logger or logging.getLogger(__name__)

        # Initialize knowledge base manager
        self.knowledge_manager = KnowledgeBaseManager()

        # Initialize tiered LLM managers for each agent (separate budgets)
        agent_budget = budget_limit / 6  # Distribute budget across agents

        self.agents = {
            'fast_simple': FastSimpleAgent(
                TieredLLMManager(lite_llm_manager, agent_budget),
                self.knowledge_manager
            ),
            'reasoning': ReasoningAgent(
                TieredLLMManager(lite_llm_manager, agent_budget),
                self.knowledge_manager
            ),
            'code_focused': CodeFocusedAgent(
                TieredLLMManager(lite_llm_manager, agent_budget),
                self.knowledge_manager
            ),
            'specialist_crypto': SpecialistAgent(
                'crypto',
                TieredLLMManager(lite_llm_manager, agent_budget),
                self.knowledge_manager
            ),
            'specialist_web': SpecialistAgent(
                'web',
                TieredLLMManager(lite_llm_manager, agent_budget),
                self.knowledge_manager
            ),
            'specialist_rev': SpecialistAgent(
                'rev',
                TieredLLMManager(lite_llm_manager, agent_budget),
                self.knowledge_manager
            ),
            'specialist_pwn': SpecialistAgent(
                'pwn',
                TieredLLMManager(lite_llm_manager, agent_budget),
                self.knowledge_manager
            )
        }

    async def solve_challenge(self, challenge: CTFChallengeClient) -> Optional[str]:
        """
        Run ensemble of agents in parallel and return first successful solution.
        """
        self.logger.info(f"Ensemble solving challenge: {challenge.challenge.name}")
        self.logger.info(f"Categories: {challenge.challenge.categories}")

        # Run all agents in parallel
        tasks = []
        for agent_name, agent in self.agents.items():
            task = asyncio.create_task(agent.solve(challenge))
            tasks.append(task)

        successful_result = None
        all_results = []

        try:
            # Wait for all agents to complete or first success
            for completed_task in asyncio.as_completed(tasks):
                result = await completed_task
                all_results.append(result)

                self.logger.info(f"Agent {result.agent_name} completed: success={result.success}, "
                               f"confidence={result.confidence:.2f}, cost=${result.cost:.4f}, "
                               f"time={result.execution_time:.2f}s")

                if result.success and not successful_result:
                    # Validate the flag before accepting
                    if result.flag and challenge.submit_flag(result.flag):
                        successful_result = result
                        self.logger.info(f"SUCCESS! Agent {result.agent_name} found correct flag: {result.flag}")

                        # Cancel remaining tasks to save budget
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        break
                    else:
                        self.logger.warning(f"Agent {result.agent_name} found invalid flag: {result.flag}")

            # Wait for any remaining tasks to complete
            if not successful_result:
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            self.logger.error(f"Ensemble execution error: {e}")

        # Log summary
        total_cost = sum(r.cost for r in all_results)
        avg_confidence = sum(r.confidence for r in all_results) / len(all_results) if all_results else 0

        self.logger.info(f"Ensemble summary: total_cost=${total_cost:.4f}, "
                        f"avg_confidence={avg_confidence:.2f}, "
                        f"agents_completed={len(all_results)}")

        if successful_result:
            self.logger.info(f"Winning agent: {successful_result.agent_name} "
                           f"(method: {successful_result.method})")
            return successful_result.flag
        else:
            self.logger.info("No agent found a valid solution")
            return None

# Export the main agent class
Agent = EnsembleAgent