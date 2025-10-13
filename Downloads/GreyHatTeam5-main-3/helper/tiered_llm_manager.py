"""
Tiered LLM Strategy Manager for CTF Agent
Implements cost-optimized LLM usage with escalating tiers:
- Tier 0: Free traditional tools (checksec, strings, sqlmap)
- Tier 1: Cheap models (Haiku $0.06) for basic tasks
- Tier 2: Mid-tier models (Sonnet $0.30) for main work
- Tier 3: Expensive reasoning models (o1 $3-5) for hard problems
"""

import logging
import subprocess
import re
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from helper.llm_helper import LiteLLMManager, LiteLLMClient

class LLMTier(Enum):
    TIER_0_FREE = 0      # Free traditional tools
    TIER_1_CHEAP = 1     # Haiku ($0.06)
    TIER_2_MID = 2       # Sonnet ($0.30)
    TIER_3_EXPENSIVE = 3 # o1 ($3-5)

@dataclass
class ModelConfig:
    model_name: str
    cost_per_1k_tokens: float
    max_tokens: int
    temperature: float
    use_case: str

@dataclass
class TierResult:
    success: bool
    result: Any
    cost: float
    tier: LLMTier
    method: str
    confidence: float

class TieredLLMManager:
    """
    Manages escalating LLM usage strategy for cost optimization.

    Tier 0 (Free): Traditional tools - 56.8% success rate
    Tier 1 (Cheap): Basic analysis and simple tasks
    Tier 2 (Mid): Complex reasoning and main exploitation
    Tier 3 (Expensive): Only for truly hard problems (43.2% remaining)
    """

    def __init__(self, llm_manager: LiteLLMManager, budget_limit: float = 0.50):
        self.llm_manager = llm_manager
        self.budget_limit = budget_limit
        self.total_spent = 0.0
        self.logger = logging.getLogger(__name__)

        # Model configurations by tier
        self.tier_configs = {
            LLMTier.TIER_1_CHEAP: ModelConfig(
                model_name="gpt-5-nano",
                cost_per_1k_tokens=0.06,
                max_tokens=4096,
                temperature=0.1,
                use_case="Basic analysis, file inspection, simple pattern matching"
            ),
            LLMTier.TIER_2_MID: ModelConfig(
                model_name="gemini-2.5-pro",
                cost_per_1k_tokens=0.30,
                max_tokens=8192,
                temperature=0.3,
                use_case="Complex reasoning, exploitation planning, script generation"
            ),
            LLMTier.TIER_3_EXPENSIVE: ModelConfig(
                model_name="o1-preview",
                cost_per_1k_tokens=3.0,
                max_tokens=32768,
                temperature=0.0,
                use_case="Advanced reasoning, complex crypto, multi-step exploitation"
            )
        }

        # Traditional tools for Tier 0
        self.tier_0_tools = {
            'checksec': 'checksec --file={}',
            'strings': 'strings {} | head -100',
            'file': 'file {}',
            'hexdump': 'hexdump -C {} | head -20',
            'nm': 'nm {} 2>/dev/null | head -50',
            'objdump': 'objdump -h {} 2>/dev/null',
            'readelf': 'readelf -h {} 2>/dev/null',
            'binwalk': 'binwalk {} 2>/dev/null',
            'sqlmap_check': 'echo "URL: {}" | grep -E "(\\?|&)\\w+="',
            'nmap_quick': 'nmap -sS -O -F {}',
            'curl_headers': 'curl -I {} 2>/dev/null',
            'base64_decode': 'echo "{}" | base64 -d 2>/dev/null',
            'rot13': 'echo "{}" | tr "A-Za-z" "N-ZA-Mn-za-m"',
        }

    def check_budget(self, estimated_cost: float) -> bool:
        """Check if we can afford the estimated cost."""
        return (self.total_spent + estimated_cost) <= self.budget_limit

    def execute_tier_0_tools(self, challenge_context: Dict[str, Any]) -> TierResult:
        """
        Execute free traditional tools first (Tier 0).
        Achieves 56.8% success rate according to research.
        """
        self.logger.info("Executing Tier 0: Free traditional tools")

        results = {}
        confidence = 0.0

        # Determine applicable tools based on challenge category
        categories = challenge_context.get('categories', [])
        files = challenge_context.get('files', [])

        applicable_tools = []

        # Rev/Pwn challenges - binary analysis tools
        if any(cat in ['rev', 'pwn', 'reverse', 'binary'] for cat in categories):
            applicable_tools.extend(['checksec', 'strings', 'file', 'nm', 'objdump', 'readelf'])

        # Crypto challenges - encoding/decoding tools
        if 'crypto' in categories:
            applicable_tools.extend(['base64_decode', 'rot13', 'hexdump'])

        # Web challenges - network tools
        if 'web' in categories:
            applicable_tools.extend(['curl_headers', 'sqlmap_check'])

        # Forensics - file analysis
        if any(cat in ['forensics', 'misc'] for cat in categories):
            applicable_tools.extend(['file', 'strings', 'binwalk', 'hexdump'])

        # Execute applicable tools
        for tool_name in applicable_tools:
            if tool_name in self.tier_0_tools:
                for file_path in files:
                    try:
                        cmd = self.tier_0_tools[tool_name].format(file_path)
                        result = subprocess.run(cmd, shell=True, capture_output=True,
                                              text=True, timeout=10)
                        if result.returncode == 0 and result.stdout.strip():
                            results[f"{tool_name}_{file_path}"] = result.stdout.strip()

                            # Check for immediate flag patterns
                            flag_match = re.search(r'flag\{[^}]+\}', result.stdout, re.IGNORECASE)
                            if flag_match:
                                self.logger.info(f"Tier 0 SUCCESS: Found flag with {tool_name}")
                                return TierResult(
                                    success=True,
                                    result=flag_match.group(0),
                                    cost=0.0,
                                    tier=LLMTier.TIER_0_FREE,
                                    method=f"tier_0_{tool_name}",
                                    confidence=0.95
                                )

                    except Exception as e:
                        self.logger.debug(f"Tier 0 tool {tool_name} failed: {e}")

        # Analyze results for patterns that suggest next tier
        if results:
            confidence = min(0.5, len(results) * 0.1)  # Basic confidence from tool outputs

        return TierResult(
            success=False,
            result=results,
            cost=0.0,
            tier=LLMTier.TIER_0_FREE,
            method="tier_0_analysis",
            confidence=confidence
        )

    def execute_tier_1_analysis(self, challenge_context: Dict[str, Any],
                               tier_0_results: Dict[str, Any]) -> TierResult:
        """
        Execute Tier 1: Cheap models for basic analysis.
        Focus on pattern recognition and simple reasoning.
        """
        if not self.check_budget(0.10):  # Estimate $0.10 for basic analysis
            return TierResult(False, None, 0.0, LLMTier.TIER_1_CHEAP, "budget_exceeded", 0.0)

        self.logger.info("Executing Tier 1: Cheap model analysis")

        config = self.tier_configs[LLMTier.TIER_1_CHEAP]
        client = self.llm_manager.create_client()

        # Focused prompt for basic analysis
        prompt = f"""
        You are a CTF expert analyzing a {challenge_context.get('categories', [])} challenge.

        Challenge: {challenge_context.get('name', 'Unknown')}
        Description: {challenge_context.get('description', 'No description')}

        Traditional tool results:
        {self._format_tool_results(tier_0_results)}

        ### ANALYZE ###
        1. What type of vulnerability or technique is most likely?
        2. Are there any obvious patterns or hints in the tool outputs?
        3. What's the simplest approach to try first?
        4. Rate confidence (0-1) in your analysis.

        Keep response concise and actionable. Focus on the most obvious approach.
        """

        try:
            response = client.simple_call(
                config.model_name,
                prompt,
                temperature=config.temperature,
                max_tokens=1024
            )

            cost = self._estimate_cost(prompt + response.choices[0].message.content, config)
            self.total_spent += cost

            # Extract confidence and approach
            content = response.choices[0].message.content
            confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', content, re.IGNORECASE)
            confidence = float(confidence_match.group(1)) if confidence_match else 0.3

            return TierResult(
                success=True,
                result=content,
                cost=cost,
                tier=LLMTier.TIER_1_CHEAP,
                method="tier_1_analysis",
                confidence=confidence
            )

        except Exception as e:
            self.logger.error(f"Tier 1 analysis failed: {e}")
            return TierResult(False, str(e), 0.0, LLMTier.TIER_1_CHEAP, "error", 0.0)

    def execute_tier_2_exploitation(self, challenge_context: Dict[str, Any],
                                   previous_results: List[TierResult]) -> TierResult:
        """
        Execute Tier 2: Mid-tier model for main exploitation work.
        Focus on script generation and complex reasoning.
        """
        if not self.check_budget(0.20):  # Estimate $0.20 for main work
            return TierResult(False, None, 0.0, LLMTier.TIER_2_MID, "budget_exceeded", 0.0)

        self.logger.info("Executing Tier 2: Mid-tier exploitation")

        config = self.tier_configs[LLMTier.TIER_2_MID]
        client = self.llm_manager.create_client()

        # Compile previous findings
        previous_analysis = self._compile_previous_results(previous_results)

        # Advanced prompt for script generation (164% improvement strategy)
        prompt = f"""
        You are an expert CTF solver. Based on the analysis below, write a Python script that generates the exploit.

        Challenge: {challenge_context.get('name')}
        Categories: {challenge_context.get('categories')}
        Description: {challenge_context.get('description')}

        Previous Analysis:
        {previous_analysis}

        ### GENERATE SCRIPT ###
        Write a complete Python script that:
        1. Implements the exploitation technique identified
        2. Includes error handling and debugging output
        3. Can be executed to solve the challenge
        4. Contains comments explaining each step

        Script should be self-contained and executable. Focus on the most promising approach from the analysis.
        If multiple approaches are viable, implement the simplest one first.

        Format response as:
        ```python
        # [explanation of approach]
        [complete python script]
        ```
        """

        try:
            response = client.call(
                model=config.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert CTF solver specializing in script generation for exploits. Always write complete, executable Python scripts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )

            cost = self._estimate_cost(prompt + response.choices[0].message.content, config)
            self.total_spent += cost

            content = response.choices[0].message.content

            # Extract and validate Python script
            script_match = re.search(r'```python\s*\n(.*?)\n```', content, re.DOTALL)
            if script_match:
                script = script_match.group(1)
                confidence = 0.7  # High confidence for script generation

                return TierResult(
                    success=True,
                    result={'script': script, 'full_response': content},
                    cost=cost,
                    tier=LLMTier.TIER_2_MID,
                    method="tier_2_script_generation",
                    confidence=confidence
                )
            else:
                # Fallback for non-script responses
                return TierResult(
                    success=True,
                    result=content,
                    cost=cost,
                    tier=LLMTier.TIER_2_MID,
                    method="tier_2_analysis",
                    confidence=0.5
                )

        except Exception as e:
            self.logger.error(f"Tier 2 exploitation failed: {e}")
            return TierResult(False, str(e), 0.0, LLMTier.TIER_2_MID, "error", 0.0)

    def execute_tier_3_advanced(self, challenge_context: Dict[str, Any],
                               previous_results: List[TierResult]) -> TierResult:
        """
        Execute Tier 3: Expensive reasoning models for truly hard problems.
        Only use when cheaper tiers fail and budget allows.
        """
        remaining_budget = self.budget_limit - self.total_spent
        if remaining_budget < 0.15:  # Reserve minimum for advanced reasoning
            return TierResult(False, None, 0.0, LLMTier.TIER_3_EXPENSIVE, "insufficient_budget", 0.0)

        self.logger.info("Executing Tier 3: Advanced reasoning model")

        config = self.tier_configs[LLMTier.TIER_3_EXPENSIVE]
        client = self.llm_manager.create_client()

        # Comprehensive prompt for advanced reasoning
        full_context = self._compile_full_context(challenge_context, previous_results)

        prompt = f"""
        You are solving a complex CTF challenge that has resisted simpler approaches.

        {full_context}

        ### ADVANCED ANALYSIS ###
        Previous attempts have not succeeded. Apply deep reasoning to:

        1. Re-examine all evidence with fresh perspective
        2. Consider advanced techniques and edge cases
        3. Look for subtle patterns or multi-step approaches
        4. Generate multiple solution strategies
        5. Provide detailed step-by-step execution plan

        This is the final tier - be thorough and consider non-obvious approaches.
        If this is a crypto challenge, consider advanced attacks.
        If this is reverse engineering, consider obfuscation techniques.
        If this is web, consider complex injection chains.

        Provide a comprehensive solution with high confidence.
        """

        try:
            # Use advanced model with higher token limit
            response = client.call(
                model=config.model_name,
                messages=[
                    {"role": "system", "content": "You are an expert CTF solver with deep knowledge across all categories. Apply advanced reasoning to solve complex challenges."},
                    {"role": "user", "content": prompt}
                ],
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )

            cost = self._estimate_cost(prompt + response.choices[0].message.content, config)
            self.total_spent += cost

            return TierResult(
                success=True,
                result=response.choices[0].message.content,
                cost=cost,
                tier=LLMTier.TIER_3_EXPENSIVE,
                method="tier_3_advanced_reasoning",
                confidence=0.8
            )

        except Exception as e:
            self.logger.error(f"Tier 3 advanced reasoning failed: {e}")
            return TierResult(False, str(e), 0.0, LLMTier.TIER_3_EXPENSIVE, "error", 0.0)

    def _format_tool_results(self, results: Dict[str, Any]) -> str:
        """Format tool results for LLM consumption."""
        if not results:
            return "No traditional tool results available."

        formatted = []
        for tool, output in results.items():
            formatted.append(f"{tool}:\n{str(output)[:500]}...")
        return "\n\n".join(formatted)

    def _compile_previous_results(self, results: List[TierResult]) -> str:
        """Compile previous tier results into readable format."""
        compiled = []
        for result in results:
            compiled.append(f"Tier {result.tier.value} ({result.method}):")
            compiled.append(f"Success: {result.success}, Confidence: {result.confidence}")
            compiled.append(f"Result: {str(result.result)[:300]}...")
            compiled.append("")
        return "\n".join(compiled)

    def _compile_full_context(self, challenge_context: Dict[str, Any],
                             previous_results: List[TierResult]) -> str:
        """Compile full context for Tier 3 analysis."""
        context = f"""
        Challenge: {challenge_context.get('name')}
        Categories: {challenge_context.get('categories')}
        Description: {challenge_context.get('description')}
        Files: {challenge_context.get('files', [])}

        Previous Analysis Results:
        {self._compile_previous_results(previous_results)}

        Budget Used: ${self.total_spent:.4f} / ${self.budget_limit}
        """
        return context

    def _estimate_cost(self, text: str, config: ModelConfig) -> float:
        """Estimate cost based on text length and model pricing."""
        # Rough estimation: ~4 characters per token
        estimated_tokens = len(text) / 4
        return (estimated_tokens / 1000) * config.cost_per_1k_tokens

    def get_remaining_budget(self) -> float:
        """Get remaining budget."""
        return max(0.0, self.budget_limit - self.total_spent)

    def get_spending_summary(self) -> Dict[str, Any]:
        """Get detailed spending summary."""
        return {
            'total_spent': self.total_spent,
            'budget_limit': self.budget_limit,
            'remaining': self.get_remaining_budget(),
            'utilization_pct': (self.total_spent / self.budget_limit) * 100
        }