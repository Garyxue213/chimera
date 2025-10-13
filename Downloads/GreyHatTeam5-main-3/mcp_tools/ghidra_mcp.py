"""
Ghidra MCP Integration for Reverse Engineering
Based on: https://github.com/jtang613/GhidrAssistMCP

Provides automated binary analysis capabilities for CTF reverse engineering challenges
via MCP server connection.
"""

import requests
import json
import logging
import time
import subprocess
import re
from typing import Dict, List, Optional, Any
from pathlib import Path

class GhidraMCP:
    """
    Model Context Protocol client for GhidrAssistMCP server.
    Provides automated analysis of binary files for CTF challenges.
    """

    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.message_endpoint = f"{self.base_url}/message"
        self.logger = logging.getLogger(f"{__name__}.GhidraMCP")
        self._server_available = self._check_server_availability()

    def _check_server_availability(self) -> bool:
        """Check if GhidrAssistMCP server is available."""
        try:
            response = requests.get(f"{self.base_url}/sse", timeout=2, stream=True)
            if response.status_code in [200, 404]:  # 404 is ok, means server is running
                self.logger.info(f"GhidrAssistMCP server available at {self.base_url}")
                return True
        except Exception as e:
            self.logger.warning(f"GhidrAssistMCP server not available at {self.base_url}: {e}")
        return False

    def _call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call a tool on the GhidrAssistMCP server.

        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments (optional)

        Returns:
            Tool result as dictionary
        """
        if not self._server_available:
            self.logger.warning(f"Server not available, cannot call tool: {tool_name}")
            return {"error": "MCP server not available", "fallback": True}

        try:
            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments or {}
                }
            }

            response = requests.post(
                self.message_endpoint,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                self.logger.debug(f"Tool {tool_name} result: {result}")
                return result
            else:
                self.logger.error(f"Tool call failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}", "response": response.text}

        except Exception as e:
            self.logger.error(f"Exception calling tool {tool_name}: {e}")
            return {"error": str(e)}

    def analyze_binary(self, binary_path: str, analysis_type: str = "full") -> Dict[str, Any]:
        """
        Analyze binary using GhidrAssistMCP server.
        Note: Binary must be loaded in Ghidra first.

        Args:
            binary_path: Path to binary file (for reference/fallback)
            analysis_type: Type of analysis ("quick", "full", "strings", "functions")

        Returns:
            Dictionary containing analysis results
        """
        if not self._server_available:
            return self._fallback_analysis(binary_path)

        results = {}

        # Get program info
        program_info = self._call_tool("get_program_info")
        if "error" not in program_info:
            results["program_info"] = program_info

        # Get functions
        if analysis_type in ["full", "functions"]:
            functions = self._call_tool("list_functions")
            if "error" not in functions:
                results["functions"] = functions

        # Get strings
        if analysis_type in ["full", "strings"]:
            strings = self._call_tool("list_strings")
            if "error" not in strings:
                results["strings"] = strings

        # If we got no results, fallback
        if not results or all("error" in v for v in results.values()):
            return self._fallback_analysis(binary_path)

        return results

    def _fallback_analysis(self, binary_path: str) -> Dict[str, Any]:
        """Fallback analysis using basic command-line tools."""
        results = {
            "fallback": True,
            "analysis_type": "basic_tools"
        }

        try:
            # File command
            file_result = subprocess.run(['file', binary_path], capture_output=True, text=True)
            results['file_info'] = file_result.stdout.strip()

            # Strings command
            strings_result = subprocess.run(['strings', binary_path], capture_output=True, text=True)
            strings_output = strings_result.stdout.strip()
            results['strings'] = strings_output.split('\n')[:100]  # Limit output

            # Look for flag patterns in strings
            flag_candidates = []
            for string in results['strings']:
                if re.search(r'flag\{[^}]+\}', string, re.IGNORECASE):
                    flag_candidates.append(string)
                elif re.search(r'ctf\{[^}]+\}', string, re.IGNORECASE):
                    flag_candidates.append(string)

            results['flag_candidates'] = flag_candidates

            # nm command (if available)
            try:
                nm_result = subprocess.run(['nm', binary_path], capture_output=True, text=True)
                if nm_result.returncode == 0:
                    results['symbols'] = nm_result.stdout.strip().split('\n')[:50]
            except:
                pass

            # objdump headers
            try:
                objdump_result = subprocess.run(['objdump', '-h', binary_path], capture_output=True, text=True)
                if objdump_result.returncode == 0:
                    results['sections'] = objdump_result.stdout.strip()
            except:
                pass

        except Exception as e:
            results['error'] = str(e)

        return results

    def extract_flag_candidates(self, binary_path: str) -> List[str]:
        """Extract potential flag strings from binary."""
        flag_candidates = []

        if self._server_available:
            # Try to get strings from MCP server
            strings_result = self._call_tool("list_strings")

            if "error" not in strings_result and "content" in strings_result:
                # Parse strings from content
                content = strings_result.get("content", [])
                if isinstance(content, list):
                    for item in content:
                        text = item.get("text", "") if isinstance(item, dict) else str(item)
                        if re.search(r'flag\{[^}]+\}', text, re.IGNORECASE):
                            flag_candidates.append(text)
                        elif re.search(r'ctf\{[^}]+\}', text, re.IGNORECASE):
                            flag_candidates.append(text)

        # Fallback to command-line tools
        if not flag_candidates:
            fallback_result = self._fallback_analysis(binary_path)
            flag_candidates = fallback_result.get("flag_candidates", [])

        return list(set(flag_candidates))  # Remove duplicates

    def get_function_info(self, function_name: str = "main") -> Dict[str, Any]:
        """Get detailed information about a specific function."""
        if not self._server_available:
            return {}

        result = self._call_tool("get_function_info", {"function_name": function_name})
        return result if "error" not in result else {}

    def list_functions(self) -> List[str]:
        """List all functions in the current program."""
        if not self._server_available:
            return []

        result = self._call_tool("list_functions")

        if "error" in result:
            return []

        # Parse function list from content
        functions = []
        if "content" in result:
            content = result.get("content", [])
            if isinstance(content, list):
                for item in content:
                    text = item.get("text", "") if isinstance(item, dict) else str(item)
                    # Parse function names from text like "- function_name @ address"
                    for line in text.split('\n'):
                        if line.strip().startswith('-'):
                            parts = line.strip()[1:].split('@')
                            if parts:
                                functions.append(parts[0].strip())

        return functions

    def decompile_function(self, function_name: str = "main") -> str:
        """Get decompiled code for a specific function."""
        if not self._server_available:
            return "Decompilation not available (MCP server not connected)"

        result = self._call_tool("decompile_function", {"function_name": function_name})

        if "error" in result:
            return f"Decompilation failed: {result.get('error')}"

        # Extract decompiled code from content
        if "content" in result:
            content = result.get("content", [])
            if isinstance(content, list) and content:
                first_item = content[0]
                return first_item.get("text", "") if isinstance(first_item, dict) else str(first_item)

        return "No decompilation output"

    def disassemble_function(self, binary_path: str, function_name: str = "main") -> str:
        """Get disassembly of a specific function using objdump fallback."""
        try:
            # Use objdump as fallback disassembler
            result = subprocess.run(
                ['objdump', '-d', binary_path],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                disassembly = result.stdout

                # Extract function if specified
                if function_name != "main":
                    # Look for function label
                    lines = disassembly.split('\n')
                    func_lines = []
                    in_function = False

                    for line in lines:
                        if f"<{function_name}>" in line:
                            in_function = True
                        elif in_function and re.match(r'^[0-9a-f]+\s+<.+>:', line):
                            # Start of next function
                            break

                        if in_function:
                            func_lines.append(line)

                    return '\n'.join(func_lines) if func_lines else disassembly[:2000]

                return disassembly[:2000]  # Limit output

        except Exception as e:
            return f"Disassembly failed: {e}"

        return "Disassembly not available"

    def get_current_address(self) -> str:
        """Get current cursor address in Ghidra."""
        if not self._server_available:
            return ""

        result = self._call_tool("get_current_address")

        if "error" in result:
            return ""

        if "content" in result:
            content = result.get("content", [])
            if isinstance(content, list) and content:
                first_item = content[0]
                return first_item.get("text", "") if isinstance(first_item, dict) else str(first_item)

        return ""

    def list_strings(self) -> List[str]:
        """List all strings in the current program."""
        if not self._server_available:
            return []

        result = self._call_tool("list_strings")

        if "error" in result:
            return []

        strings = []
        if "content" in result:
            content = result.get("content", [])
            if isinstance(content, list):
                for item in content:
                    text = item.get("text", "") if isinstance(item, dict) else str(item)
                    for line in text.split('\n'):
                        if line.strip():
                            strings.append(line.strip())

        return strings

    def get_xrefs_to(self, address: str) -> List[str]:
        """Get cross-references to an address."""
        if not self._server_available:
            return []

        result = self._call_tool("xrefs_to", {"address": address})

        if "error" in result:
            return []

        xrefs = []
        if "content" in result:
            content = result.get("content", [])
            if isinstance(content, list):
                for item in content:
                    text = item.get("text", "") if isinstance(item, dict) else str(item)
                    for line in text.split('\n'):
                        if line.strip():
                            xrefs.append(line.strip())

        return xrefs

    def is_available(self) -> bool:
        """Check if the MCP server is available."""
        return self._server_available
