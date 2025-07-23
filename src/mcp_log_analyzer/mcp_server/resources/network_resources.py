"""
Network monitoring MCP resources (netstat functionality).
"""

import platform
import subprocess

from mcp.server import FastMCP


def register_network_resources(mcp: FastMCP):
    """Register all network-related resources with the MCP server."""

    @mcp.resource("system://netstat")
    async def get_netstat() -> str:
        """
        Get network connections and statistics with default options.

        Use parameterized versions for specific troubleshooting:
        - system://netstat/listening - Show only listening ports
        - system://netstat/established - Show only established connections
        - system://netstat/all - Show all connections with process info
        - system://netstat/stats - Show network statistics
        - system://netstat/routing - Show routing table
        - system://netstat/port/80 - Show connections on specific port
        """
        # Default to listening ports for quick overview
        return await get_netstat_listening()

    @mcp.resource("system://netstat/listening")
    async def get_netstat_listening() -> str:
        """
        Show all listening ports and services.

        Useful for checking which services are running and what ports are open.
        """
        result = []
        result.append("=== Listening Ports ===\n")

        try:
            if platform.system() == "Windows":
                # Windows netstat command
                cmd_output = subprocess.run(
                    ["netstat", "-an", "-p", "TCP"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if cmd_output.returncode == 0:
                    lines = cmd_output.stdout.split("\n")
                    result.append("Protocol  Local Address          State")
                    result.append("-" * 50)
                    for line in lines:
                        if "LISTENING" in line:
                            result.append(line.strip())

                # Also show UDP listening
                cmd_output = subprocess.run(
                    ["netstat", "-an", "-p", "UDP"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if cmd_output.returncode == 0:
                    result.append("\nUDP Listening:")
                    result.append("Protocol  Local Address")
                    result.append("-" * 30)
                    lines = cmd_output.stdout.split("\n")
                    for line in lines:
                        if "UDP" in line and "*:*" in line:
                            result.append(line.strip())

            else:
                # Linux - try ss first (modern), then netstat (legacy)
                try:
                    cmd_output = subprocess.run(
                        ["ss", "-tlnp"], capture_output=True, text=True, timeout=10
                    )
                    if cmd_output.returncode == 0:
                        result.append("TCP Listening Ports (ss):")
                        result.append(cmd_output.stdout)

                    # UDP listening
                    cmd_output = subprocess.run(
                        ["ss", "-ulnp"], capture_output=True, text=True, timeout=10
                    )
                    if cmd_output.returncode == 0:
                        result.append("\nUDP Listening Ports (ss):")
                        result.append(cmd_output.stdout)

                except FileNotFoundError:
                    # Fall back to netstat if ss not available
                    cmd_output = subprocess.run(
                        ["netstat", "-tlnp"], capture_output=True, text=True, timeout=10
                    )
                    if cmd_output.returncode == 0:
                        result.append("TCP Listening Ports (netstat):")
                        result.append(cmd_output.stdout)

                    cmd_output = subprocess.run(
                        ["netstat", "-ulnp"], capture_output=True, text=True, timeout=10
                    )
                    if cmd_output.returncode == 0:
                        result.append("\nUDP Listening Ports (netstat):")
                        result.append(cmd_output.stdout)

        except Exception as e:
            result.append(f"Error getting listening ports: {str(e)}")

        return "\n".join(result)

    @mcp.resource("system://netstat/established")
    async def get_netstat_established() -> str:
        """
        Show all established network connections.

        Useful for seeing active connections and identifying communication patterns.
        """
        result = []
        result.append("=== Established Connections ===\n")

        try:
            if platform.system() == "Windows":
                cmd_output = subprocess.run(
                    ["netstat", "-an", "-p", "TCP"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if cmd_output.returncode == 0:
                    lines = cmd_output.stdout.split("\n")
                    result.append(
                        "Protocol  Local Address          Foreign Address        State"
                    )
                    result.append("-" * 70)
                    for line in lines:
                        if "ESTABLISHED" in line:
                            result.append(line.strip())
            else:
                # Linux
                try:
                    cmd_output = subprocess.run(
                        ["ss", "-tnp", "state", "established"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if cmd_output.returncode == 0:
                        result.append("Established TCP Connections (ss):")
                        result.append(cmd_output.stdout)
                except FileNotFoundError:
                    cmd_output = subprocess.run(
                        ["netstat", "-tnp"], capture_output=True, text=True, timeout=10
                    )
                    if cmd_output.returncode == 0:
                        lines = cmd_output.stdout.split("\n")
                        result.append("Established TCP Connections (netstat):")
                        result.append(
                            "Proto  Local Address          Foreign Address        State       PID/Program"
                        )
                        result.append("-" * 90)
                        for line in lines:
                            if "ESTABLISHED" in line:
                                result.append(line.strip())

        except Exception as e:
            result.append(f"Error getting established connections: {str(e)}")

        return "\n".join(result)

    @mcp.resource("system://netstat/all")
    async def get_netstat_all() -> str:
        """
        Show all network connections with process information.

        Comprehensive view including listening, established, and other states.
        """
        result = []
        result.append("=== All Network Connections ===\n")

        try:
            if platform.system() == "Windows":
                cmd_output = subprocess.run(
                    ["netstat", "-ano"], capture_output=True, text=True, timeout=15
                )
                if cmd_output.returncode == 0:
                    result.append("All TCP/UDP Connections:")
                    result.append(cmd_output.stdout)
            else:
                try:
                    # Use ss for comprehensive output
                    cmd_output = subprocess.run(
                        ["ss", "-tulanp"], capture_output=True, text=True, timeout=15
                    )
                    if cmd_output.returncode == 0:
                        result.append("All Network Connections (ss):")
                        result.append(cmd_output.stdout)
                except FileNotFoundError:
                    cmd_output = subprocess.run(
                        ["netstat", "-tulanp"],
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    if cmd_output.returncode == 0:
                        result.append("All Network Connections (netstat):")
                        result.append(cmd_output.stdout)

        except Exception as e:
            result.append(f"Error getting all connections: {str(e)}")

        return "\n".join(result)

    @mcp.resource("system://netstat/stats")
    async def get_netstat_stats() -> str:
        """
        Show network interface statistics and protocol statistics.

        Useful for identifying network performance issues and packet loss.
        """
        result = []
        result.append("=== Network Statistics ===\n")

        try:
            if platform.system() == "Windows":
                # Network statistics
                cmd_output = subprocess.run(
                    ["netstat", "-s"], capture_output=True, text=True, timeout=10
                )
                if cmd_output.returncode == 0:
                    result.append("Protocol Statistics:")
                    result.append(cmd_output.stdout)

                # Interface statistics
                cmd_output = subprocess.run(
                    ["netstat", "-e"], capture_output=True, text=True, timeout=10
                )
                if cmd_output.returncode == 0:
                    result.append("\nInterface Statistics:")
                    result.append(cmd_output.stdout)
            else:
                # Linux interface statistics
                try:
                    cmd_output = subprocess.run(
                        ["ss", "-i"], capture_output=True, text=True, timeout=10
                    )
                    if cmd_output.returncode == 0:
                        result.append("Interface Statistics (ss):")
                        result.append(cmd_output.stdout)
                except FileNotFoundError:
                    cmd_output = subprocess.run(
                        ["netstat", "-i"], capture_output=True, text=True, timeout=10
                    )
                    if cmd_output.returncode == 0:
                        result.append("Interface Statistics (netstat):")
                        result.append(cmd_output.stdout)

                # Protocol statistics if available
                try:
                    cmd_output = subprocess.run(
                        ["netstat", "-s"], capture_output=True, text=True, timeout=10
                    )
                    if cmd_output.returncode == 0:
                        result.append("\nProtocol Statistics:")
                        result.append(cmd_output.stdout)
                except:
                    pass

        except Exception as e:
            result.append(f"Error getting network statistics: {str(e)}")

        return "\n".join(result)

    @mcp.resource("system://netstat/routing")
    async def get_netstat_routing() -> str:
        """
        Show routing table information.

        Useful for diagnosing routing issues and network connectivity problems.
        """
        result = []
        result.append("=== Routing Table ===\n")

        try:
            if platform.system() == "Windows":
                cmd_output = subprocess.run(
                    ["netstat", "-r"], capture_output=True, text=True, timeout=10
                )
                if cmd_output.returncode == 0:
                    result.append("IPv4 Routing Table:")
                    result.append(cmd_output.stdout)
            else:
                # Linux routing table
                try:
                    cmd_output = subprocess.run(
                        ["ip", "route", "show"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if cmd_output.returncode == 0:
                        result.append("Routing Table (ip route):")
                        result.append(cmd_output.stdout)
                except FileNotFoundError:
                    cmd_output = subprocess.run(
                        ["netstat", "-r"], capture_output=True, text=True, timeout=10
                    )
                    if cmd_output.returncode == 0:
                        result.append("Routing Table (netstat):")
                        result.append(cmd_output.stdout)

        except Exception as e:
            result.append(f"Error getting routing table: {str(e)}")

        return "\n".join(result)

    @mcp.resource("system://netstat/port/{port}")
    async def get_netstat_port(port: str) -> str:
        """
        Show connections on a specific port.

        Args:
            port: Port number to check (e.g., "80", "443", "22")

        Useful for checking if a service is running on a specific port.
        """
        try:
            port_num = int(port)
        except ValueError:
            return f"Invalid port number: {port}"

        result = []
        result.append(f"=== Connections on Port {port} ===\n")

        try:
            if platform.system() == "Windows":
                cmd_output = subprocess.run(
                    ["netstat", "-ano"], capture_output=True, text=True, timeout=10
                )
                if cmd_output.returncode == 0:
                    lines = cmd_output.stdout.split("\n")
                    result.append(
                        "Protocol  Local Address          Foreign Address        State       PID"
                    )
                    result.append("-" * 80)
                    for line in lines:
                        if f":{port}" in line:
                            result.append(line.strip())
            else:
                # Linux
                try:
                    cmd_output = subprocess.run(
                        ["ss", "-tulanp", f"sport = :{port}"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if cmd_output.returncode == 0:
                        result.append(f"Connections on port {port} (ss):")
                        result.append(cmd_output.stdout)

                    # Also check for connections TO this port
                    cmd_output = subprocess.run(
                        ["ss", "-tulanp", f"dport = :{port}"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if cmd_output.returncode == 0:
                        result.append(f"\nConnections TO port {port} (ss):")
                        result.append(cmd_output.stdout)

                except FileNotFoundError:
                    cmd_output = subprocess.run(
                        ["netstat", "-tulanp"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    if cmd_output.returncode == 0:
                        lines = cmd_output.stdout.split("\n")
                        result.append(f"Connections involving port {port} (netstat):")
                        result.append(
                            "Proto  Local Address          Foreign Address        State       PID/Program"
                        )
                        result.append("-" * 90)
                        for line in lines:
                            if f":{port}" in line:
                                result.append(line.strip())

        except Exception as e:
            result.append(f"Error checking port {port}: {str(e)}")

        return "\n".join(result)
