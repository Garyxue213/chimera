"""
Kali Linux MCP Integration for CTF Tools
Based on: https://github.com/Wh0am123/MCP-Kali-Server

Provides access to security tools commonly found in Kali Linux distribution.
"""

import subprocess
import tempfile
import json
import os
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

class KaliMCP:
    """
    Model Context Protocol integration for Kali Linux security tools.
    Provides automated access to common CTF/penetration testing tools.
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.KaliMCP")
        self.available_tools = self._detect_available_tools()

    def _detect_available_tools(self) -> Dict[str, bool]:
        """Detect which Kali tools are available on the system."""
        tools_to_check = [
            'nmap', 'sqlmap', 'gobuster', 'dirb', 'nikto', 'hydra',
            'john', 'hashcat', 'binwalk', 'foremost', 'steghide',
            'exiftool', 'strings', 'file', 'checksec', 'objdump',
            'gdb', 'ltrace', 'strace', 'radare2', 'curl', 'wget'
        ]

        available = {}
        for tool in tools_to_check:
            try:
                result = subprocess.run(['which', tool], capture_output=True, text=True)
                available[tool] = result.returncode == 0
            except:
                available[tool] = False

        return available

    def run_tool(self, tool_name: str, arguments: List[str], timeout: int = 60) -> Dict[str, Any]:
        """
        Run a security tool with specified arguments.

        Args:
            tool_name: Name of the tool to run
            arguments: List of arguments to pass to the tool
            timeout: Timeout in seconds

        Returns:
            Dictionary containing tool output and metadata
        """
        if tool_name not in self.available_tools or not self.available_tools[tool_name]:
            return {
                "error": f"Tool '{tool_name}' not available",
                "available_tools": [k for k, v in self.available_tools.items() if v]
            }

        try:
            cmd = [tool_name] + arguments
            self.logger.info(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "tool": tool_name,
                "command": ' '.join(cmd),
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                "tool": tool_name,
                "error": f"Command timeout after {timeout} seconds",
                "exit_code": -1
            }
        except Exception as e:
            return {
                "tool": tool_name,
                "error": str(e),
                "exit_code": -1
            }

    # Network Tools
    def nmap_scan(self, target: str, scan_type: str = "basic") -> Dict[str, Any]:
        """Run nmap scan on target."""
        scan_configs = {
            "basic": ["-sS", "-O", "-F"],
            "quick": ["-T4", "-F"],
            "stealth": ["-sS", "-T2"],
            "version": ["-sV", "-O"],
            "vuln": ["--script=vuln"]
        }

        args = scan_configs.get(scan_type, scan_configs["basic"]) + [target]
        return self.run_tool("nmap", args, timeout=300)

    def gobuster_dir(self, url: str, wordlist: str = "/usr/share/wordlists/dirb/common.txt") -> Dict[str, Any]:
        """Run directory brute-force with gobuster."""
        args = ["dir", "-u", url, "-w", wordlist, "-t", "50"]
        return self.run_tool("gobuster", args, timeout=300)

    def nikto_scan(self, target: str) -> Dict[str, Any]:
        """Run Nikto web vulnerability scanner."""
        args = ["-h", target, "-Format", "txt"]
        return self.run_tool("nikto", args, timeout=300)

    # Web Application Tools
    def sqlmap_test(self, url: str, parameter: str = None) -> Dict[str, Any]:
        """Test for SQL injection using sqlmap."""
        args = ["-u", url, "--batch", "--level=2", "--risk=2"]

        if parameter:
            args.extend(["-p", parameter])

        return self.run_tool("sqlmap", args, timeout=600)

    def curl_request(self, url: str, method: str = "GET", headers: Dict[str, str] = None,
                    data: str = None) -> Dict[str, Any]:
        """Make HTTP request using curl."""
        args = ["-i", "-X", method]

        if headers:
            for key, value in headers.items():
                args.extend(["-H", f"{key}: {value}"])

        if data and method in ["POST", "PUT", "PATCH"]:
            args.extend(["-d", data])

        args.append(url)
        return self.run_tool("curl", args, timeout=60)

    # Cryptography Tools
    def john_crack(self, hash_file: str, wordlist: str = "/usr/share/wordlists/rockyou.txt") -> Dict[str, Any]:
        """Crack hashes using John the Ripper."""
        args = ["--wordlist=" + wordlist, hash_file]
        return self.run_tool("john", args, timeout=300)

    def hashcat_crack(self, hash_value: str, hash_type: str = "0", wordlist: str = "/usr/share/wordlists/rockyou.txt") -> Dict[str, Any]:
        """Crack hashes using hashcat."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.hash') as f:
            f.write(hash_value)
            hash_file = f.name

        try:
            args = ["-m", hash_type, hash_file, wordlist]
            result = self.run_tool("hashcat", args, timeout=300)

            # Clean up temp file
            os.unlink(hash_file)
            return result

        except Exception as e:
            os.unlink(hash_file)
            return {"error": str(e)}

    # Forensics Tools
    def binwalk_extract(self, file_path: str) -> Dict[str, Any]:
        """Extract embedded files using binwalk."""
        args = ["-e", file_path]
        return self.run_tool("binwalk", args, timeout=120)

    def foremost_recover(self, file_path: str, output_dir: str = None) -> Dict[str, Any]:
        """Recover files using foremost."""
        if not output_dir:
            output_dir = tempfile.mkdtemp(prefix="foremost_")

        args = ["-i", file_path, "-o", output_dir]
        return self.run_tool("foremost", args, timeout=300)

    def steghide_extract(self, file_path: str, passphrase: str = "") -> Dict[str, Any]:
        """Extract hidden data using steghide."""
        args = ["extract", "-sf", file_path]

        if passphrase:
            args.extend(["-p", passphrase])
        else:
            args.extend(["-p", ""])

        return self.run_tool("steghide", args, timeout=60)

    def exiftool_analyze(self, file_path: str) -> Dict[str, Any]:
        """Analyze file metadata using exiftool."""
        args = ["-j", file_path]  # JSON output
        result = self.run_tool("exiftool", args, timeout=30)

        # Parse JSON output if successful
        if result.get("success") and result.get("stdout"):
            try:
                metadata = json.loads(result["stdout"])
                result["metadata"] = metadata
            except json.JSONDecodeError:
                pass

        return result

    # Reverse Engineering Tools
    def strings_extract(self, file_path: str, min_length: int = 4) -> Dict[str, Any]:
        """Extract strings from binary file."""
        args = ["-n", str(min_length), file_path]
        result = self.run_tool("strings", args, timeout=60)

        # Parse strings and look for flags
        if result.get("success") and result.get("stdout"):
            strings = result["stdout"].strip().split('\n')
            flag_candidates = []

            for string in strings:
                if re.search(r'flag\{[^}]+\}', string, re.IGNORECASE):
                    flag_candidates.append(string)
                elif re.search(r'ctf\{[^}]+\}', string, re.IGNORECASE):
                    flag_candidates.append(string)

            result["strings"] = strings
            result["flag_candidates"] = flag_candidates

        return result

    def file_analyze(self, file_path: str) -> Dict[str, Any]:
        """Analyze file type and properties."""
        args = [file_path]
        return self.run_tool("file", args, timeout=30)

    def checksec_analyze(self, binary_path: str) -> Dict[str, Any]:
        """Analyze binary security features."""
        args = ["--file", binary_path]
        return self.run_tool("checksec", args, timeout=30)

    def objdump_disassemble(self, binary_path: str, function: str = None) -> Dict[str, Any]:
        """Disassemble binary using objdump."""
        args = ["-d"]

        if function:
            # Try to disassemble specific function
            args.extend(["--disassemble=" + function])

        args.append(binary_path)
        return self.run_tool("objdump", args, timeout=60)

    def gdb_analyze(self, binary_path: str, commands: List[str] = None) -> Dict[str, Any]:
        """Run GDB with specified commands."""
        if not commands:
            commands = ["info functions", "info variables", "disas main", "quit"]

        # Create GDB command file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.gdb') as f:
            for cmd in commands:
                f.write(cmd + '\n')
            cmd_file = f.name

        try:
            args = ["-batch", "-x", cmd_file, binary_path]
            result = self.run_tool("gdb", args, timeout=120)

            # Clean up command file
            os.unlink(cmd_file)
            return result

        except Exception as e:
            os.unlink(cmd_file)
            return {"error": str(e)}

    # System Analysis Tools
    def ltrace_trace(self, binary_path: str, arguments: List[str] = None) -> Dict[str, Any]:
        """Trace library calls using ltrace."""
        args = [binary_path]
        if arguments:
            args.extend(arguments)

        return self.run_tool("ltrace", args, timeout=60)

    def strace_trace(self, binary_path: str, arguments: List[str] = None) -> Dict[str, Any]:
        """Trace system calls using strace."""
        args = [binary_path]
        if arguments:
            args.extend(arguments)

        return self.run_tool("strace", args, timeout=60)

    # Automated CTF Analysis
    def auto_analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Automatically analyze a file based on its type."""
        results = {
            "file_path": file_path,
            "analysis_results": {}
        }

        # Basic file analysis
        file_info = self.file_analyze(file_path)
        results["analysis_results"]["file_info"] = file_info

        if not file_info.get("success"):
            return results

        file_type = file_info.get("stdout", "").lower()

        # Binary analysis
        if any(keyword in file_type for keyword in ["elf", "executable", "binary"]):
            results["analysis_results"]["strings"] = self.strings_extract(file_path)
            results["analysis_results"]["checksec"] = self.checksec_analyze(file_path)
            results["analysis_results"]["objdump"] = self.objdump_disassemble(file_path)

        # Image analysis
        elif any(keyword in file_type for keyword in ["jpeg", "png", "gif", "bmp"]):
            results["analysis_results"]["exiftool"] = self.exiftool_analyze(file_path)
            results["analysis_results"]["steghide"] = self.steghide_extract(file_path)
            results["analysis_results"]["binwalk"] = self.binwalk_extract(file_path)

        # Archive analysis
        elif any(keyword in file_type for keyword in ["zip", "tar", "gzip", "archive"]):
            results["analysis_results"]["binwalk"] = self.binwalk_extract(file_path)
            results["analysis_results"]["foremost"] = self.foremost_recover(file_path)

        # Text file analysis
        elif "text" in file_type:
            results["analysis_results"]["strings"] = self.strings_extract(file_path, min_length=1)

        # Generic analysis for unknown types
        else:
            results["analysis_results"]["strings"] = self.strings_extract(file_path)
            results["analysis_results"]["binwalk"] = self.binwalk_extract(file_path)
            results["analysis_results"]["exiftool"] = self.exiftool_analyze(file_path)

        return results

    def auto_analyze_url(self, url: str) -> Dict[str, Any]:
        """Automatically analyze a web URL."""
        results = {
            "url": url,
            "analysis_results": {}
        }

        # Basic HTTP analysis
        results["analysis_results"]["curl_get"] = self.curl_request(url, "GET")

        # Directory enumeration
        results["analysis_results"]["gobuster"] = self.gobuster_dir(url)

        # Vulnerability scanning
        results["analysis_results"]["nikto"] = self.nikto_scan(url)

        # SQL injection testing (basic)
        if "?" in url:
            results["analysis_results"]["sqlmap"] = self.sqlmap_test(url)

        return results

    def extract_flags_from_results(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Extract potential flags from analysis results."""
        flags = []

        def search_in_text(text: str):
            if isinstance(text, str):
                flag_matches = re.findall(r'flag\{[^}]+\}', text, re.IGNORECASE)
                ctf_matches = re.findall(r'ctf\{[^}]+\}', text, re.IGNORECASE)
                flags.extend(flag_matches + ctf_matches)

        def search_recursive(obj):
            if isinstance(obj, dict):
                for value in obj.values():
                    search_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    search_recursive(item)
            elif isinstance(obj, str):
                search_in_text(obj)

        search_recursive(analysis_results)
        return list(set(flags))  # Remove duplicates

    def get_tool_help(self, tool_name: str) -> Dict[str, Any]:
        """Get help/usage information for a tool."""
        if tool_name not in self.available_tools or not self.available_tools[tool_name]:
            return {"error": f"Tool '{tool_name}' not available"}

        # Try different help flags
        help_flags = ["--help", "-h", "-help"]

        for flag in help_flags:
            result = self.run_tool(tool_name, [flag], timeout=10)
            if result.get("success") or result.get("stderr"):
                return result

        return {"error": f"No help available for {tool_name}"}

    def list_available_tools(self) -> Dict[str, Any]:
        """List all available tools and their status."""
        return {
            "available_tools": {k: v for k, v in self.available_tools.items() if v},
            "unavailable_tools": {k: v for k, v in self.available_tools.items() if not v},
            "total_available": sum(self.available_tools.values()),
            "total_tools": len(self.available_tools)
        }