"""
Validation Layer for CTF Agent
Implements comprehensive validation to prevent 97.1% false positive rates.
Includes syntax checking, execution testing, and correctness verification.
"""

import ast
import subprocess
import tempfile
import os
import re
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import docker
import signal

@dataclass
class ValidationResult:
    valid: bool
    confidence: float
    errors: List[str]
    warnings: List[str]
    execution_output: str
    flag_candidate: Optional[str]
    execution_time: float
    security_issues: List[str]

class SecurityValidator:
    """Validates scripts for security issues before execution."""

    DANGEROUS_IMPORTS = {
        'os', 'subprocess', 'sys', 'shutil', 'socket', 'urllib', 'requests',
        'ftplib', 'smtplib', 'telnetlib', 'pickle', 'marshal', '__import__'
    }

    DANGEROUS_FUNCTIONS = {
        'exec', 'eval', 'compile', 'open', '__import__', 'getattr', 'setattr',
        'delattr', 'hasattr', 'globals', 'locals', 'vars', 'input', 'raw_input'
    }

    ALLOWED_MODULES = {
        'base64', 'hashlib', 'binascii', 'struct', 'math', 'random', 're',
        'json', 'string', 'itertools', 'collections', 'functools', 'operator',
        'cryptography', 'pycryptodome', 'gmpy2', 'sympy', 'numpy'
    }

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SecurityValidator")

    def validate_script_security(self, script: str) -> Tuple[bool, List[str]]:
        """
        Validate script for security issues.
        Returns (is_safe, security_issues)
        """
        issues = []

        try:
            # Parse AST to analyze code structure
            tree = ast.parse(script)

            # Check for dangerous patterns
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.DANGEROUS_IMPORTS and alias.name not in self.ALLOWED_MODULES:
                            issues.append(f"Dangerous import: {alias.name}")

                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.DANGEROUS_IMPORTS and node.module not in self.ALLOWED_MODULES:
                        issues.append(f"Dangerous import from: {node.module}")

                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.DANGEROUS_FUNCTIONS:
                            issues.append(f"Dangerous function call: {node.func.id}")
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in {'system', 'popen', 'spawn', 'exec'}:
                            issues.append(f"Dangerous method call: {node.func.attr}")

                elif isinstance(node, ast.Str):
                    # Check for suspicious string patterns
                    if any(pattern in node.s.lower() for pattern in ['/bin/', '/usr/', '/etc/', 'rm -', 'del ', 'format c:']):
                        issues.append(f"Suspicious string pattern: {node.s[:50]}...")

        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        except Exception as e:
            issues.append(f"AST analysis error: {e}")

        # Additional pattern-based checks
        dangerous_patterns = [
            r'__import__\s*\(',
            r'eval\s*\(',
            r'exec\s*\(',
            r'os\.system\s*\(',
            r'subprocess\.',
            r'socket\.',
            r'import\s+os\b',
            r'from\s+os\s+import',
            r'\.format\(\s*[\'"][^\'\"]*[\'\"]\s*\)',  # Format string attacks
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, script, re.IGNORECASE):
                issues.append(f"Dangerous pattern detected: {pattern}")

        is_safe = len(issues) == 0
        return is_safe, issues

class SyntaxValidator:
    """Validates Python syntax and common errors."""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SyntaxValidator")

    def validate_syntax(self, script: str) -> Tuple[bool, List[str], List[str]]:
        """
        Validate Python syntax and check for common issues.
        Returns (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Basic syntax check
        try:
            ast.parse(script)
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return False, errors, warnings
        except Exception as e:
            errors.append(f"Parse error: {e}")
            return False, errors, warnings

        # Additional static analysis
        try:
            tree = ast.parse(script)

            # Check for common issues
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check for functions without return statements
                    has_return = any(isinstance(child, ast.Return) for child in ast.walk(node))
                    if not has_return and node.name not in ['main', '__init__']:
                        warnings.append(f"Function '{node.name}' has no return statement")

                elif isinstance(node, ast.Name):
                    # Check for potentially undefined variables (basic check)
                    if isinstance(node.ctx, ast.Load) and node.id in ['undefined', 'None', 'null']:
                        warnings.append(f"Potentially undefined variable: {node.id}")

                elif isinstance(node, ast.Div):
                    warnings.append("Division operation found - check for division by zero")

                elif isinstance(node, ast.Subscript):
                    warnings.append("Array/dict access found - check for index/key errors")

        except Exception as e:
            warnings.append(f"Static analysis warning: {e}")

        return True, errors, warnings

class ExecutionValidator:
    """Validates scripts by executing them in a controlled environment."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.ExecutionValidator")

    def execute_script_safe(self, script: str, working_dir: str, challenge_context: Dict[str, Any]) -> ValidationResult:
        """
        Execute script in a safe, controlled environment.
        """
        start_time = time.time()

        try:
            # Create temporary script file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(script)
                script_path = f.name

            # Execute with timeout and resource limits
            result = subprocess.run(
                ['python', script_path],
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=self._get_safe_environment()
            )

            execution_time = time.time() - start_time

            # Clean up
            os.unlink(script_path)

            # Analyze output
            output = result.stdout + result.stderr
            flag_candidate = self._extract_flag_candidate(output, challenge_context.get('flag_regex', r'flag\{[^}]+\}'))

            # Determine success
            success = result.returncode == 0 and flag_candidate is not None
            confidence = self._calculate_confidence(result, flag_candidate, execution_time)

            return ValidationResult(
                valid=success,
                confidence=confidence,
                errors=[] if result.returncode == 0 else [f"Script exit code: {result.returncode}"],
                warnings=[],
                execution_output=output,
                flag_candidate=flag_candidate,
                execution_time=execution_time,
                security_issues=[]
            )

        except subprocess.TimeoutExpired:
            return ValidationResult(
                valid=False,
                confidence=0.0,
                errors=[f"Script execution timeout ({self.timeout}s)"],
                warnings=[],
                execution_output="",
                flag_candidate=None,
                execution_time=self.timeout,
                security_issues=[]
            )
        except Exception as e:
            return ValidationResult(
                valid=False,
                confidence=0.0,
                errors=[f"Execution error: {e}"],
                warnings=[],
                execution_output="",
                flag_candidate=None,
                execution_time=time.time() - start_time,
                security_issues=[]
            )

    def _get_safe_environment(self) -> Dict[str, str]:
        """Create a restricted environment for script execution."""
        safe_env = {
            'PATH': '/usr/bin:/bin',
            'PYTHONPATH': '',
            'HOME': '/tmp',
            'USER': 'ctf',
            'SHELL': '/bin/sh'
        }
        return safe_env

    def _extract_flag_candidate(self, output: str, flag_regex: str) -> Optional[str]:
        """Extract potential flag from script output."""
        try:
            matches = re.findall(flag_regex, output, re.IGNORECASE)
            if matches:
                return matches[0]  # Return first match
        except Exception as e:
            self.logger.debug(f"Flag extraction error: {e}")
        return None

    def _calculate_confidence(self, result: subprocess.CompletedProcess, flag_candidate: Optional[str], execution_time: float) -> float:
        """Calculate confidence score for execution result."""
        confidence = 0.0

        # Base confidence from successful execution
        if result.returncode == 0:
            confidence += 0.3

        # Confidence from finding flag
        if flag_candidate:
            confidence += 0.5

        # Confidence from reasonable execution time
        if execution_time < 10:
            confidence += 0.1

        # Confidence from clean output (no errors)
        if 'error' not in result.stderr.lower() and 'exception' not in result.stderr.lower():
            confidence += 0.1

        return min(confidence, 1.0)

class DockerExecutionValidator:
    """Execute scripts in isolated Docker containers for maximum security."""

    def __init__(self, timeout: int = 45):
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.DockerExecutionValidator")
        self.client = docker.from_env()

    def execute_script_docker(self, script: str, working_dir: str, challenge_context: Dict[str, Any]) -> ValidationResult:
        """
        Execute script in a Docker container for complete isolation.
        """
        start_time = time.time()
        container = None

        try:
            # Create temporary directory for script and data
            with tempfile.TemporaryDirectory() as temp_dir:
                script_path = os.path.join(temp_dir, 'solution.py')
                with open(script_path, 'w') as f:
                    f.write(script)

                # Copy challenge files to temp directory
                import shutil
                data_dir = os.path.join(temp_dir, 'data')
                shutil.copytree(working_dir, data_dir)

                # Run in Docker container
                container = self.client.containers.run(
                    'python:3.9-slim',
                    command=['python', '/workspace/solution.py'],
                    volumes={temp_dir: {'bind': '/workspace', 'mode': 'ro'}},
                    working_dir='/workspace/data',
                    network_mode='none',  # No network access
                    mem_limit='128m',     # Memory limit
                    cpu_period=100000,    # CPU limit
                    cpu_quota=50000,      # 50% CPU
                    detach=True,
                    remove=True
                )

                # Wait for completion with timeout
                try:
                    exit_code = container.wait(timeout=self.timeout)['StatusCode']
                    logs = container.logs().decode('utf-8')
                except Exception as e:
                    if container:
                        container.kill()
                    raise e

                execution_time = time.time() - start_time

                # Analyze output
                flag_candidate = self._extract_flag_candidate(logs, challenge_context.get('flag_regex', r'flag\{[^}]+\}'))

                success = exit_code == 0 and flag_candidate is not None
                confidence = self._calculate_confidence(exit_code, flag_candidate, execution_time, logs)

                return ValidationResult(
                    valid=success,
                    confidence=confidence,
                    errors=[] if exit_code == 0 else [f"Container exit code: {exit_code}"],
                    warnings=[],
                    execution_output=logs,
                    flag_candidate=flag_candidate,
                    execution_time=execution_time,
                    security_issues=[]
                )

        except Exception as e:
            if container:
                try:
                    container.kill()
                except:
                    pass

            return ValidationResult(
                valid=False,
                confidence=0.0,
                errors=[f"Docker execution error: {e}"],
                warnings=[],
                execution_output="",
                flag_candidate=None,
                execution_time=time.time() - start_time,
                security_issues=[]
            )

    def _extract_flag_candidate(self, output: str, flag_regex: str) -> Optional[str]:
        """Extract potential flag from script output."""
        try:
            matches = re.findall(flag_regex, output, re.IGNORECASE)
            if matches:
                return matches[0]
        except Exception:
            pass
        return None

    def _calculate_confidence(self, exit_code: int, flag_candidate: Optional[str], execution_time: float, logs: str) -> float:
        """Calculate confidence score for Docker execution result."""
        confidence = 0.0

        if exit_code == 0:
            confidence += 0.3

        if flag_candidate:
            confidence += 0.5

        if execution_time < 20:
            confidence += 0.1

        if 'error' not in logs.lower() and 'exception' not in logs.lower():
            confidence += 0.1

        return min(confidence, 1.0)

class ComprehensiveValidator:
    """
    Main validation layer that combines all validation techniques.
    Prevents false positives and ensures script correctness.
    """

    def __init__(self, use_docker: bool = True, timeout: int = 30):
        self.use_docker = use_docker
        self.timeout = timeout
        self.logger = logging.getLogger(f"{__name__}.ComprehensiveValidator")

        self.security_validator = SecurityValidator()
        self.syntax_validator = SyntaxValidator()
        self.execution_validator = ExecutionValidator(timeout)

        if use_docker:
            try:
                self.docker_validator = DockerExecutionValidator(timeout)
            except Exception as e:
                self.logger.warning(f"Docker validator unavailable: {e}")
                self.docker_validator = None
        else:
            self.docker_validator = None

    def validate_solution(self, script: str, working_dir: str, challenge_context: Dict[str, Any]) -> ValidationResult:
        """
        Comprehensive validation of generated solution script.

        Steps:
        1. Security validation - check for dangerous patterns
        2. Syntax validation - verify Python syntax
        3. Execution validation - run script and verify output
        4. Flag validation - submit flag to challenge
        """

        self.logger.info("Starting comprehensive solution validation")

        # Step 1: Security validation
        is_safe, security_issues = self.security_validator.validate_script_security(script)
        if not is_safe:
            self.logger.warning(f"Security validation failed: {security_issues}")
            return ValidationResult(
                valid=False,
                confidence=0.0,
                errors=[],
                warnings=[],
                execution_output="",
                flag_candidate=None,
                execution_time=0.0,
                security_issues=security_issues
            )

        # Step 2: Syntax validation
        is_valid_syntax, syntax_errors, syntax_warnings = self.syntax_validator.validate_syntax(script)
        if not is_valid_syntax:
            self.logger.warning(f"Syntax validation failed: {syntax_errors}")
            return ValidationResult(
                valid=False,
                confidence=0.0,
                errors=syntax_errors,
                warnings=syntax_warnings,
                execution_output="",
                flag_candidate=None,
                execution_time=0.0,
                security_issues=[]
            )

        # Step 3: Execution validation
        if self.docker_validator and self.use_docker:
            self.logger.info("Using Docker execution validation")
            exec_result = self.docker_validator.execute_script_docker(script, working_dir, challenge_context)
        else:
            self.logger.info("Using subprocess execution validation")
            exec_result = self.execution_validator.execute_script_safe(script, working_dir, challenge_context)

        # Combine all validation results
        combined_result = ValidationResult(
            valid=exec_result.valid,
            confidence=exec_result.confidence,
            errors=syntax_errors + exec_result.errors,
            warnings=syntax_warnings + exec_result.warnings,
            execution_output=exec_result.execution_output,
            flag_candidate=exec_result.flag_candidate,
            execution_time=exec_result.execution_time,
            security_issues=security_issues
        )

        # Log validation summary
        self.logger.info(f"Validation complete: valid={combined_result.valid}, "
                        f"confidence={combined_result.confidence:.2f}, "
                        f"flag_found={'Yes' if combined_result.flag_candidate else 'No'}")

        return combined_result

    def validate_and_submit_flag(self, script: str, working_dir: str, challenge_context: Dict[str, Any], challenge_client) -> Tuple[bool, Optional[str]]:
        """
        Validate script and automatically submit flag if found and valid.
        Returns (success, flag)
        """
        validation_result = self.validate_solution(script, working_dir, challenge_context)

        if not validation_result.valid or not validation_result.flag_candidate:
            return False, None

        # Step 4: Flag validation - submit to challenge
        flag = validation_result.flag_candidate

        try:
            if challenge_client.submit_flag(flag):
                self.logger.info(f"Flag validation successful: {flag}")
                return True, flag
            else:
                self.logger.warning(f"Flag validation failed: {flag}")
                return False, flag
        except Exception as e:
            self.logger.error(f"Flag submission error: {e}")
            return False, flag

class ScriptGenerationValidator:
    """
    Specialized validator for script generation with iterative improvement.
    Implements the 164% success improvement from script generation strategy.
    """

    def __init__(self, validator: ComprehensiveValidator, max_iterations: int = 3):
        self.validator = validator
        self.max_iterations = max_iterations
        self.logger = logging.getLogger(f"{__name__}.ScriptGenerationValidator")

    def validate_and_improve_script(self, initial_script: str, working_dir: str,
                                  challenge_context: Dict[str, Any], llm_client) -> Tuple[bool, Optional[str], str]:
        """
        Validate script and iteratively improve it based on execution feedback.
        Returns (success, flag, final_script)
        """

        current_script = initial_script

        for iteration in range(self.max_iterations):
            self.logger.info(f"Script validation iteration {iteration + 1}/{self.max_iterations}")

            # Validate current script
            result = self.validator.validate_solution(current_script, working_dir, challenge_context)

            if result.valid and result.flag_candidate:
                self.logger.info(f"Script validation successful on iteration {iteration + 1}")
                return True, result.flag_candidate, current_script

            # If not successful and we have iterations left, try to improve
            if iteration < self.max_iterations - 1:
                self.logger.info(f"Improving script based on feedback (iteration {iteration + 1})")

                improvement_feedback = self._generate_improvement_feedback(result)
                improved_script = self._improve_script_with_llm(
                    current_script,
                    improvement_feedback,
                    challenge_context,
                    llm_client
                )

                if improved_script:
                    current_script = improved_script
                else:
                    self.logger.warning("Failed to improve script, continuing with current version")

        self.logger.warning("Script validation failed after all iterations")
        return False, None, current_script

    def _generate_improvement_feedback(self, validation_result: ValidationResult) -> str:
        """Generate feedback for script improvement based on validation result."""
        feedback_parts = []

        if validation_result.errors:
            feedback_parts.append(f"Errors encountered: {'; '.join(validation_result.errors)}")

        if validation_result.warnings:
            feedback_parts.append(f"Warnings: {'; '.join(validation_result.warnings)}")

        if validation_result.security_issues:
            feedback_parts.append(f"Security issues: {'; '.join(validation_result.security_issues)}")

        if validation_result.execution_output:
            feedback_parts.append(f"Execution output: {validation_result.execution_output[:500]}...")

        if not validation_result.flag_candidate:
            feedback_parts.append("No flag found in output. Ensure the script prints the flag clearly.")

        return "\n".join(feedback_parts)

    def _improve_script_with_llm(self, script: str, feedback: str, challenge_context: Dict[str, Any], llm_client) -> Optional[str]:
        """Use LLM to improve script based on feedback."""

        improvement_prompt = f"""
The following Python script for a CTF challenge needs improvement:

Challenge: {challenge_context.get('name', 'Unknown')}
Categories: {challenge_context.get('categories', [])}

Current script:
```python
{script}
```

Issues found during validation:
{feedback}

Please provide an improved version of the script that:
1. Fixes all identified issues
2. Ensures the flag is clearly printed to stdout
3. Includes proper error handling
4. Is more robust and reliable

Respond with only the improved Python script in code blocks:
```python
# Improved script here
```
"""

        try:
            response = llm_client.simple_call("gemini-2.5-pro", improvement_prompt, temperature=0.1)

            # Extract improved script
            script_match = re.search(r'```python\s*\n(.*?)\n```', response.choices[0].message.content, re.DOTALL)
            if script_match:
                return script_match.group(1)

        except Exception as e:
            self.logger.error(f"Script improvement failed: {e}")

        return None