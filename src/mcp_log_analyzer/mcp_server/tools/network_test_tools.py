"""
Network monitoring and testing MCP tools.
"""

import platform
import socket
import subprocess
from typing import Any, Dict, List

from mcp.server import FastMCP
from pydantic import BaseModel, Field


class NetworkPortTestRequest(BaseModel):
    """Request model for network port testing."""

    ports: List[int] = Field(..., description="List of ports to test")
    host: str = Field("localhost", description="Host to test (default: localhost)")
    timeout: int = Field(5, description="Connection timeout in seconds")


class NetworkConnectivityRequest(BaseModel):
    """Request model for network connectivity testing."""

    hosts: List[str] = Field(
        default_factory=lambda: ["8.8.8.8", "google.com", "github.com"],
        description="List of hosts to test connectivity to",
    )
    ping_count: int = Field(3, description="Number of ping packets to send")


class NetworkAnalysisRequest(BaseModel):
    """Request model for network analysis."""

    include_listening: bool = Field(
        True, description="Include listening ports analysis"
    )
    include_established: bool = Field(
        True, description="Include established connections"
    )
    analyze_traffic: bool = Field(False, description="Analyze network traffic patterns")


def register_network_test_tools(mcp: FastMCP):
    """Register all network testing tools with the MCP server."""

    @mcp.tool()
    async def test_network_tools_availability() -> Dict[str, Any]:
        """
        Test availability of network diagnostic tools.

        This tool checks if essential network tools are available
        on the system for network troubleshooting.
        """
        tools_to_test = {
            "ping": "Network connectivity testing",
            "netstat": "Network connections and statistics",
            "ss": "Modern replacement for netstat (Linux)",
            "nslookup": "DNS lookup utility",
            "curl": "HTTP client for testing web connectivity",
            "wget": "HTTP client alternative",
            "telnet": "TCP connection testing",
            "nc": "Netcat - networking utility",
        }

        available_tools = {}

        for tool, description in tools_to_test.items():
            try:
                # Test if tool exists and can run
                result = subprocess.run(
                    [tool, "--help"] if tool != "telnet" else [tool],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                # Most tools return 0 for --help, but some may not
                available_tools[tool] = {
                    "available": True,
                    "description": description,
                    "test_successful": True,
                }

            except FileNotFoundError:
                available_tools[tool] = {
                    "available": False,
                    "description": description,
                    "error": "Command not found",
                }
            except subprocess.TimeoutExpired:
                available_tools[tool] = {
                    "available": True,
                    "description": description,
                    "test_successful": False,
                    "note": "Tool exists but test timed out",
                }
            except Exception as e:
                available_tools[tool] = {
                    "available": False,
                    "description": description,
                    "error": str(e),
                }

        # Count available tools
        available_count = sum(
            1 for tool in available_tools.values() if tool["available"]
        )
        total_count = len(tools_to_test)

        return {
            "platform": platform.system(),
            "tools_summary": {
                "total_tools": total_count,
                "available_tools": available_count,
                "availability_percentage": round(
                    (available_count / total_count) * 100, 1
                ),
            },
            "tools": available_tools,
        }

    @mcp.tool()
    async def test_port_connectivity(
        request: NetworkPortTestRequest,
    ) -> Dict[str, Any]:
        """
        Test connectivity to specific ports.

        This tool tests whether specific ports are open and accepting
        connections on the specified host.
        """
        try:
            test_results = {}

            for port in request.ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(request.timeout)

                    start_time = __import__("time").time()
                    result = sock.connect_ex((request.host, port))
                    end_time = __import__("time").time()

                    sock.close()

                    if result == 0:
                        test_results[port] = {
                            "status": "open",
                            "accessible": True,
                            "response_time_ms": round(
                                (end_time - start_time) * 1000, 2
                            ),
                        }
                    else:
                        test_results[port] = {
                            "status": "closed",
                            "accessible": False,
                            "error_code": result,
                        }

                except socket.timeout:
                    test_results[port] = {
                        "status": "timeout",
                        "accessible": False,
                        "error": f"Connection timed out after {request.timeout} seconds",
                    }
                except Exception as e:
                    test_results[port] = {
                        "status": "error",
                        "accessible": False,
                        "error": str(e),
                    }

            # Summary statistics
            open_ports = [p for p, r in test_results.items() if r["accessible"]]
            closed_ports = [p for p, r in test_results.items() if not r["accessible"]]

            return {
                "target_host": request.host,
                "timeout_seconds": request.timeout,
                "summary": {
                    "total_ports_tested": len(request.ports),
                    "open_ports": len(open_ports),
                    "closed_ports": len(closed_ports),
                    "open_port_list": open_ports,
                },
                "detailed_results": test_results,
            }

        except Exception as e:
            return {"error": f"Error testing port connectivity: {str(e)}"}

    @mcp.tool()
    async def test_network_connectivity(
        request: NetworkConnectivityRequest,
    ) -> Dict[str, Any]:
        """
        Test network connectivity to various hosts.

        This tool tests network connectivity using ping and provides
        latency and packet loss information.
        """
        try:
            connectivity_results = {}

            for host in request.hosts:
                try:
                    # Determine ping command based on platform
                    if platform.system() == "Windows":
                        ping_cmd = ["ping", "-n", str(request.ping_count), host]
                    else:
                        ping_cmd = ["ping", "-c", str(request.ping_count), host]

                    result = subprocess.run(
                        ping_cmd,
                        capture_output=True,
                        text=True,
                        timeout=request.ping_count * 5 + 10,  # Dynamic timeout
                    )

                    if result.returncode == 0:
                        # Parse ping output for statistics
                        output = result.stdout

                        # Extract basic connectivity info
                        connectivity_results[host] = {
                            "reachable": True,
                            "ping_output": output,
                            "command_used": " ".join(ping_cmd),
                        }

                        # Try to extract timing information (platform-specific parsing)
                        if platform.system() == "Windows":
                            # Windows ping output parsing
                            if "Average" in output:
                                lines = output.split("\n")
                                for line in lines:
                                    if "Average" in line:
                                        avg_time = line.split("=")[-1].strip()
                                        connectivity_results[host][
                                            "average_latency"
                                        ] = avg_time
                        else:
                            # Linux/Unix ping output parsing
                            if "min/avg/max" in output:
                                lines = output.split("\n")
                                for line in lines:
                                    if "min/avg/max" in line:
                                        times = line.split("=")[-1].strip()
                                        connectivity_results[host][
                                            "latency_stats"
                                        ] = times

                    else:
                        connectivity_results[host] = {
                            "reachable": False,
                            "error": result.stderr or "Ping failed",
                            "command_used": " ".join(ping_cmd),
                        }

                except subprocess.TimeoutExpired:
                    connectivity_results[host] = {
                        "reachable": False,
                        "error": "Ping command timed out",
                    }
                except Exception as e:
                    connectivity_results[host] = {
                        "reachable": False,
                        "error": str(e),
                    }

            # Summary statistics
            reachable_hosts = [
                h for h, r in connectivity_results.items() if r["reachable"]
            ]
            unreachable_hosts = [
                h for h, r in connectivity_results.items() if not r["reachable"]
            ]

            return {
                "test_parameters": {
                    "ping_count": request.ping_count,
                    "total_hosts": len(request.hosts),
                },
                "summary": {
                    "reachable_hosts": len(reachable_hosts),
                    "unreachable_hosts": len(unreachable_hosts),
                    "success_rate": round(
                        (len(reachable_hosts) / len(request.hosts)) * 100, 1
                    ),
                    "reachable_list": reachable_hosts,
                    "unreachable_list": unreachable_hosts,
                },
                "detailed_results": connectivity_results,
            }

        except Exception as e:
            return {"error": f"Error testing network connectivity: {str(e)}"}

    @mcp.tool()
    async def analyze_network_connections(
        request: NetworkAnalysisRequest,
    ) -> Dict[str, Any]:
        """
        Analyze current network connections and listening ports.

        This tool provides comprehensive analysis of network connections,
        listening ports, and traffic patterns for troubleshooting.
        """
        try:
            analysis_results = {}

            if request.include_listening:
                # Analyze listening ports
                try:
                    if platform.system() == "Windows":
                        cmd = ["netstat", "-an"]
                    else:
                        # Try ss first, fall back to netstat
                        try:
                            cmd_result = subprocess.run(
                                ["ss", "-tlnp"],
                                capture_output=True,
                                text=True,
                                timeout=10,
                            )
                            if cmd_result.returncode == 0:
                                cmd = ["ss", "-tlnp"]
                            else:
                                cmd = ["netstat", "-tlnp"]
                        except FileNotFoundError:
                            cmd = ["netstat", "-tlnp"]

                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=10
                    )

                    if result.returncode == 0:
                        lines = result.stdout.split("\n")
                        listening_ports = []

                        for line in lines:
                            if "LISTEN" in line or (
                                platform.system() != "Windows" and "tcp" in line.lower()
                            ):
                                parts = line.split()
                                if len(parts) >= 4:
                                    local_address = (
                                        parts[3]
                                        if platform.system() == "Windows"
                                        else parts[0]
                                    )
                                    if ":" in local_address:
                                        port = local_address.split(":")[-1]
                                        listening_ports.append(
                                            {
                                                "port": port,
                                                "address": local_address,
                                                "protocol": "TCP",
                                            }
                                        )

                        analysis_results["listening_ports"] = {
                            "total_count": len(listening_ports),
                            "ports": listening_ports[:20],  # Limit to first 20
                            "command_used": " ".join(cmd),
                        }
                    else:
                        analysis_results["listening_ports"] = {"error": result.stderr}

                except Exception as e:
                    analysis_results["listening_ports"] = {"error": str(e)}

            if request.include_established:
                # Analyze established connections
                try:
                    if platform.system() == "Windows":
                        cmd = ["netstat", "-an"]
                    else:
                        try:
                            cmd_result = subprocess.run(
                                ["ss", "-tnp", "state", "established"],
                                capture_output=True,
                                text=True,
                                timeout=10,
                            )
                            if cmd_result.returncode == 0:
                                cmd = ["ss", "-tnp", "state", "established"]
                            else:
                                cmd = ["netstat", "-tnp"]
                        except FileNotFoundError:
                            cmd = ["netstat", "-tnp"]

                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=10
                    )

                    if result.returncode == 0:
                        lines = result.stdout.split("\n")
                        established_connections = []

                        for line in lines:
                            if "ESTABLISHED" in line or "ESTAB" in line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    local_addr = (
                                        parts[3]
                                        if platform.system() == "Windows"
                                        else parts[0]
                                    )
                                    foreign_addr = (
                                        parts[4]
                                        if platform.system() == "Windows"
                                        else parts[1]
                                    )
                                    established_connections.append(
                                        {
                                            "local_address": local_addr,
                                            "foreign_address": foreign_addr,
                                            "state": "ESTABLISHED",
                                        }
                                    )

                        analysis_results["established_connections"] = {
                            "total_count": len(established_connections),
                            "connections": established_connections[
                                :20
                            ],  # Limit to first 20
                            "command_used": " ".join(cmd),
                        }
                    else:
                        analysis_results["established_connections"] = {
                            "error": result.stderr
                        }

                except Exception as e:
                    analysis_results["established_connections"] = {"error": str(e)}

            # Network interface information
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(
                        ["ipconfig", "/all"], capture_output=True, text=True, timeout=10
                    )
                else:
                    result = subprocess.run(
                        ["ip", "addr", "show"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                if result.returncode == 0:
                    analysis_results["network_interfaces"] = {
                        "configuration": result.stdout[:2000],  # Limit output size
                        "command_used": (
                            "ipconfig /all"
                            if platform.system() == "Windows"
                            else "ip addr show"
                        ),
                    }
                else:
                    analysis_results["network_interfaces"] = {"error": result.stderr}

            except Exception as e:
                analysis_results["network_interfaces"] = {"error": str(e)}

            return {
                "analysis_scope": {
                    "include_listening": request.include_listening,
                    "include_established": request.include_established,
                    "analyze_traffic": request.analyze_traffic,
                },
                "platform": platform.system(),
                "results": analysis_results,
            }

        except Exception as e:
            return {"error": f"Error analyzing network connections: {str(e)}"}

    @mcp.tool()
    async def diagnose_network_issues() -> Dict[str, Any]:
        """
        Perform comprehensive network diagnostics.

        This tool runs multiple network tests to identify potential
        network connectivity or configuration issues.
        """
        try:
            diagnostic_results = {}

            # Test 1: Basic connectivity to well-known servers
            connectivity_hosts = ["8.8.8.8", "1.1.1.1", "google.com"]
            connectivity_results = {}

            for host in connectivity_hosts:
                try:
                    if platform.system() == "Windows":
                        ping_cmd = ["ping", "-n", "1", host]
                    else:
                        ping_cmd = ["ping", "-c", "1", host]

                    result = subprocess.run(
                        ping_cmd, capture_output=True, text=True, timeout=10
                    )
                    connectivity_results[host] = {
                        "reachable": result.returncode == 0,
                        "details": (
                            "Success" if result.returncode == 0 else result.stderr[:200]
                        ),
                    }
                except Exception as e:
                    connectivity_results[host] = {"reachable": False, "error": str(e)}

            diagnostic_results["connectivity_test"] = connectivity_results

            # Test 2: DNS Resolution
            dns_test_hosts = ["google.com", "github.com", "stackoverflow.com"]
            dns_results = {}

            for host in dns_test_hosts:
                try:
                    import socket

                    ip = socket.gethostbyname(host)
                    dns_results[host] = {"resolved": True, "ip_address": ip}
                except Exception as e:
                    dns_results[host] = {"resolved": False, "error": str(e)}

            diagnostic_results["dns_resolution_test"] = dns_results

            # Test 3: Common port connectivity
            important_ports = [80, 443, 53, 22]
            port_results = {}

            for port in important_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    result = sock.connect_ex(("google.com", port))
                    sock.close()

                    port_results[port] = {
                        "accessible": result == 0,
                        "service": {80: "HTTP", 443: "HTTPS", 53: "DNS", 22: "SSH"}.get(
                            port, "Unknown"
                        ),
                    }
                except Exception as e:
                    port_results[port] = {"accessible": False, "error": str(e)}

            diagnostic_results["port_connectivity_test"] = port_results

            # Test 4: Network interface status
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(
                        ["ipconfig"], capture_output=True, text=True, timeout=5
                    )
                else:
                    result = subprocess.run(
                        ["ip", "link", "show"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )

                diagnostic_results["interface_status"] = {
                    "command_successful": result.returncode == 0,
                    "output_preview": (
                        result.stdout[:500]
                        if result.returncode == 0
                        else result.stderr[:500]
                    ),
                }
            except Exception as e:
                diagnostic_results["interface_status"] = {"error": str(e)}

            # Overall assessment
            connectivity_success = sum(
                1 for r in connectivity_results.values() if r["reachable"]
            )
            dns_success = sum(1 for r in dns_results.values() if r["resolved"])
            port_success = sum(1 for r in port_results.values() if r["accessible"])

            total_tests = (
                len(connectivity_hosts) + len(dns_test_hosts) + len(important_ports)
            )
            successful_tests = connectivity_success + dns_success + port_success
            success_rate = (successful_tests / total_tests) * 100

            if success_rate >= 80:
                overall_status = "healthy"
            elif success_rate >= 60:
                overall_status = "fair"
            else:
                overall_status = "issues_detected"

            return {
                "overall_status": overall_status,
                "success_rate": round(success_rate, 1),
                "test_summary": {
                    "connectivity_tests": f"{connectivity_success}/{len(connectivity_hosts)} passed",
                    "dns_tests": f"{dns_success}/{len(dns_test_hosts)} passed",
                    "port_tests": f"{port_success}/{len(important_ports)} passed",
                },
                "detailed_results": diagnostic_results,
                "recommendations": _generate_network_recommendations(
                    diagnostic_results
                ),
            }

        except Exception as e:
            return {"error": f"Error performing network diagnostics: {str(e)}"}


def _generate_network_recommendations(results: Dict) -> List[str]:
    """Generate network troubleshooting recommendations based on test results."""
    recommendations = []

    # Check connectivity issues
    connectivity = results.get("connectivity_test", {})
    failed_connectivity = [
        host
        for host, result in connectivity.items()
        if not result.get("reachable", False)
    ]

    if failed_connectivity:
        recommendations.append(
            f"Check internet connectivity - failed to reach: {', '.join(failed_connectivity)}"
        )

    # Check DNS issues
    dns = results.get("dns_resolution_test", {})
    failed_dns = [
        host for host, result in dns.items() if not result.get("resolved", False)
    ]

    if failed_dns:
        recommendations.append(
            f"Check DNS configuration - failed to resolve: {', '.join(failed_dns)}"
        )

    # Check port issues
    ports = results.get("port_connectivity_test", {})
    failed_ports = [
        str(port)
        for port, result in ports.items()
        if not result.get("accessible", False)
    ]

    if failed_ports:
        recommendations.append(
            f"Check firewall settings - blocked ports: {', '.join(failed_ports)}"
        )

    if not recommendations:
        recommendations.append("Network appears to be functioning normally")

    return recommendations
