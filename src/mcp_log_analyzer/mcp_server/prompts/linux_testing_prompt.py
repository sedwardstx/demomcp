"""
Linux system testing and diagnostics prompts for the MCP Log Analyzer server.
"""

from mcp.server import FastMCP


def register_linux_testing_prompts(mcp: FastMCP):
    """Register all Linux testing prompts."""

    @mcp.prompt()
    async def linux_diagnostics_guide() -> str:
        """
        Comprehensive guide for Linux system diagnostics and testing.

        This prompt provides detailed guidance on using Linux system logs,
        systemd journal, and diagnostic tools for troubleshooting.
        """
        return """
# 🐧 Linux System Diagnostics Guide

## 📊 **Linux Log Analysis**

### Available Log Sources
- **systemd Journal**: Centralized logging system for modern Linux distributions
- **Syslog**: Traditional system logging (/var/log/syslog, /var/log/messages)
- **Auth Logs**: Authentication and authorization events (/var/log/auth.log)
- **Kernel Logs**: Kernel messages and hardware events (/var/log/kern.log)
- **Application Logs**: Service-specific logs in /var/log/

### Linux Testing Tools

#### 1. Test Log Access 🔍
```
Tool: test_linux_log_access
✅ Tests access to common log files in /var/log/
✅ Verifies systemd journal accessibility
✅ Checks availability of system commands (ss, netstat, systemctl)
✅ Reports file permissions and sizes
✅ Cross-platform compatibility check
```

#### 2. Query systemd Journal 📊
```
Tool: query_systemd_journal
Parameters:
- service_name: Specific service to query (e.g., "nginx", "sshd")
- priority: Log level (emerg, alert, crit, err, warning, notice, info, debug)
- time_duration: "30m", "2h", "1d", etc.
- max_lines: Result limit (default: 100)

Examples:
- Service errors: service_name="nginx", priority="err"
- Recent alerts: priority="alert", time_duration="1h"
- System boot logs: time_duration="1h", max_lines=200
```

#### 3. Analyze Linux Services 🛠️
```
Tool: analyze_linux_services
Parameters:
- service_pattern: Filter services by name pattern
- include_failed: Include failed services in analysis

Capabilities:
✅ Lists active and failed systemd services
✅ Retrieves recent logs for failed services
✅ Provides health status assessment
✅ Identifies problematic services
```

#### 4. System Overview 🖥️
```
Tool: get_linux_system_overview
✅ System information (hostname, uptime, kernel version)
✅ Memory and CPU status
✅ Disk usage for root filesystem
✅ Recent critical error logs
✅ Distribution and platform details
```

## 📝 **systemd Journal Priorities**

### Priority Levels (syslog standard)
- **emerg (0)**: System unusable, emergency conditions
- **alert (1)**: Action must be taken immediately
- **crit (2)**: Critical conditions
- **err (3)**: Error conditions
- **warning (4)**: Warning conditions
- **notice (5)**: Normal but significant conditions
- **info (6)**: Informational messages
- **debug (7)**: Debug-level messages

### Common Service Names
- **systemd**: System and service manager
- **kernel**: Linux kernel messages
- **sshd**: SSH daemon
- **nginx/apache2**: Web servers
- **mysql/postgresql**: Database services
- **networkd**: Network management
- **resolved**: DNS resolution
- **cron**: Scheduled tasks
- **docker**: Container runtime

## 🔧 **Diagnostic Workflows**

### 1. Initial System Health Check 🎨
```
Step 1: Test log access capabilities
→ tool: test_linux_log_access

Step 2: Get system overview
→ tool: get_linux_system_overview

Step 3: Check for failed services
→ tool: analyze_linux_services (include_failed=true)

Step 4: Review recent critical events
→ tool: query_systemd_journal (priority="crit", time_duration="24h")
```

### 2. Service Troubleshooting 🛠️
```
Step 1: Identify failed services
→ tool: analyze_linux_services

Step 2: Get service-specific logs
→ tool: query_systemd_journal (service_name="service-name")

Step 3: Check service dependencies
→ Look for related service failures

Step 4: Review error patterns
→ Query specific error priorities for the service
```

### 3. Boot and Startup Analysis 🚀
```
Step 1: Check boot-time logs
→ tool: query_systemd_journal (time_duration="1h", max_lines=500)

Step 2: Identify startup failures
→ priority="err", look for systemd and kernel messages

Step 3: Check service startup order
→ Look for dependency-related failures

Step 4: Hardware initialization
→ Check kernel logs for hardware issues
```

### 4. Authentication and Security 🔒
```
Step 1: Check authentication logs
→ tool: query_systemd_journal (service_name="sshd")

Step 2: Look for failed logins
→ priority="warning", search for "Failed password"

Step 3: Monitor sudo usage
→ service_name="sudo", time_duration="24h"

Step 4: Check for suspicious activity
→ Look for unusual login patterns or times
```

### 5. Performance Investigation 📊
```
Step 1: Check system resource warnings
→ priority="warning", time_duration="6h"

Step 2: Look for OOM (Out of Memory) events
→ Search for "killed process" or "Out of memory"

Step 3: Check disk space issues
→ Look for "No space left on device" messages

Step 4: Network connectivity problems
→ service_name="networkd" or "NetworkManager"
```

### 6. Application Debugging 🐛
```
Step 1: Query application-specific logs
→ service_name="your-app", priority="err"

Step 2: Check application dependencies
→ Look for database, network, or filesystem errors

Step 3: Review configuration issues
→ Search for "configuration" or "config" in messages

Step 4: Monitor resource usage
→ Look for memory, CPU, or file descriptor limits
```

## 🎨 **Health Status Interpretation**

### Healthy System ✅
- 0 failed services
- No critical or alert level messages in last 24h
- System uptime as expected
- All essential services active
- No recent authentication failures

### Fair System ⚠️
- 1-2 failed services (non-critical)
- Few error messages in logs
- Some warning messages
- Minor service restarts
- Occasional authentication issues

### Concerning System ❌
- 3+ failed services
- Critical or alert level messages
- Frequent service failures
- System crashes or unexpected reboots
- Security-related errors
- Resource exhaustion events

## 🛠️ **Common Log Patterns**

### Service Management
- **"Started [Service]"**: Service startup success
- **"Failed to start [Service]"**: Service startup failure
- **"Stopped [Service]"**: Service stopped (planned or unplanned)
- **"Reloading [Service]"**: Service configuration reload
- **"[Service] main process exited"**: Service process termination

### System Events
- **"Booting [Kernel Version]"**: System boot process
- **"systemd[1]: Startup finished"**: Boot completion
- **"kernel: Out of memory"**: OOM killer activation
- **"kernel: segfault"**: Application segmentation fault
- **"systemd-logind: Session [ID] logged out"**: User logout

### Security Events
- **"Failed password for [user]"**: Authentication failure
- **"Accepted publickey for [user]"**: SSH key authentication success
- **"sudo: [user] : TTY=[tty] ; PWD=[dir] ; USER=root"**: Sudo usage
- **"pam_unix(sudo:session): session opened for user root"**: Elevated privileges

### Network Events
- **"link is down"**: Network interface down
- **"link is up"**: Network interface up
- **"DHCP: lease renewal"**: IP address renewal
- **"DNS resolution failed"**: DNS lookup failure

## 🔍 **Advanced Query Examples**

### Find All Service Failures Today
```
priority: "err"
time_duration: "24h"
max_lines: 200
# Look for "Failed to start" or "Main process exited"
```

### Monitor SSH Activity
```
service_name: "sshd"
time_duration: "6h"
max_lines: 100
# Check for failed and successful logins
```

### Check Kernel Issues
```
service_name: "kernel"
priority: "err"
time_duration: "48h"
# Look for hardware or driver problems
```

### Boot Analysis
```
time_duration: "2h"
max_lines: 500
# Review entire boot process
```

## 📎 **File Locations Reference**

### Traditional Log Files
- `/var/log/syslog` - System messages (Debian/Ubuntu)
- `/var/log/messages` - System messages (RHEL/CentOS)
- `/var/log/auth.log` - Authentication logs
- `/var/log/kern.log` - Kernel messages
- `/var/log/dmesg` - Boot messages
- `/var/log/cron.log` - Scheduled task logs

### systemd Journal
- `/var/log/journal/` - Persistent journal storage
- `/run/log/journal/` - Volatile journal storage
- Use `journalctl` command for access

### Application Logs
- `/var/log/nginx/` - Nginx web server
- `/var/log/apache2/` - Apache web server
- `/var/log/mysql/` - MySQL database
- `/var/log/postgresql/` - PostgreSQL database

## ⚠️ **Important Notes**

### Permissions
- **Root access**: Required for most system logs
- **systemd-journal group**: For journal access without root
- **File permissions**: Check readable permissions on log files

### Performance Considerations
- **Large journals**: Use time-based filtering for better performance
- **Network queries**: May timeout on slow systems
- **Disk space**: Monitor journal size and rotation

### Distribution Differences
- **Debian/Ubuntu**: Uses /var/log/syslog and auth.log
- **RHEL/CentOS**: Uses /var/log/messages and secure
- **Arch Linux**: Primarily uses systemd journal
- **systemd vs SysV**: Modern vs traditional init systems

### Troubleshooting Tips
- Start with system overview for general health
- Use failed service analysis to identify specific issues
- Check recent time periods first, then expand
- Look for patterns in timestamps and error frequencies
- Cross-reference service failures with system events

This comprehensive Linux diagnostics system provides deep insights into system health, service status, security events, and performance issues for effective troubleshooting across different Linux distributions.
"""

    @mcp.prompt()
    async def linux_systemd_reference() -> str:
        """
        Quick reference guide for systemd services and common log patterns.

        This prompt provides a searchable reference for systemd service
        management and troubleshooting.
        """
        return """
# 📖 Linux systemd and Service Reference Guide

## 🛠️ **systemd Service States**

### Service Active States
- **active (running)**: Service is running normally
- **active (exited)**: One-shot service completed successfully
- **active (waiting)**: Service is waiting for an event
- **inactive (dead)**: Service is not running
- **failed**: Service failed to start or crashed

### Service Load States
- **loaded**: Unit file has been loaded into memory
- **not-found**: Unit file was not found
- **bad-setting**: Configuration error in unit file
- **error**: Error occurred while loading unit file
- **masked**: Unit file is masked (disabled)

### Service Sub States
- **running**: Main process is running
- **start-pre**: Pre-start commands are executing
- **start**: Main service is starting
- **start-post**: Post-start commands are executing
- **reload**: Service is reloading configuration
- **stop**: Service is stopping
- **stop-post**: Post-stop commands are executing
- **final-sigterm**: Final SIGTERM phase
- **final-sigkill**: Final SIGKILL phase
- **failed**: Service failed
- **auto-restart**: Service is scheduled for restart

## 📊 **Common systemd Services**

### Core System Services
- **systemd**: System and service manager (PID 1)
- **systemd-logind**: Login manager
- **systemd-networkd**: Network configuration
- **systemd-resolved**: DNS resolution
- **systemd-timesyncd**: Time synchronization
- **systemd-udevd**: Device management

### Network Services
- **NetworkManager**: Network connection management
- **sshd**: SSH daemon
- **firewalld**: Firewall management
- **networking**: Basic network configuration
- **dhclient**: DHCP client

### Web Services
- **nginx**: Nginx web server
- **apache2/httpd**: Apache web server
- **php-fpm**: PHP FastCGI Process Manager

### Database Services
- **mysql/mariadb**: MySQL/MariaDB database
- **postgresql**: PostgreSQL database
- **redis**: Redis in-memory database
- **mongodb**: MongoDB document database

### System Utilities
- **cron**: Scheduled tasks
- **rsyslog**: System logging
- **dbus**: Inter-process communication
- **avahi-daemon**: Service discovery

## 📝 **Common Log Messages and Meanings**

### Service Startup Messages
```
"Started [Service Name]"
→ Service started successfully

"Starting [Service Name]..."
→ Service startup initiated

"Failed to start [Service Name]"
→ Service startup failed - check dependencies and configuration

"[Service] main process exited, code=exited, status=1"
→ Service process terminated with error code 1

"Stopped [Service Name]"
→ Service stopped (planned or due to failure)
```

### Configuration and Dependencies
```
"Dependency failed for [Service]"
→ Required service or resource is not available

"Unit [Service] is bound to inactive unit"
→ Service depends on an inactive unit

"Reload requested from [source]"
→ Service configuration reload requested

"Configuration file [file] changed on disk"
→ Service detected configuration change
```

### Resource and Performance Issues
```
"Failed to allocate memory"
→ System running low on memory

"Too many open files"
→ Service hit file descriptor limit

"Connection refused"
→ Service not accepting connections (port/socket issue)

"Operation timed out"
→ Service operation exceeded timeout limit
```

### Security and Authentication
```
"Failed password for [user] from [IP]"
→ SSH login attempt failed

"Accepted publickey for [user] from [IP]"
→ SSH key-based authentication successful

"pam_unix(service:auth): authentication failure"
→ PAM authentication failed

"sudo: [user] : TTY=[tty] ; PWD=[dir] ; USER=root ; COMMAND=[cmd]"
→ User executed command with sudo
```

## 🔍 **Troubleshooting Common Issues**

### Service Won't Start
→ **Check for**: "Failed to start", "Dependency failed"
→ **Look at**: Service dependencies, configuration files
→ **Commands**: `systemctl status service`, `systemctl list-dependencies service`

### Service Keeps Crashing
→ **Check for**: "main process exited", "failed", frequent restarts
→ **Look at**: Exit codes, resource limits, configuration errors
→ **Commands**: `systemctl status service`, check service logs

### High CPU/Memory Usage
→ **Check for**: Performance warnings, resource allocation messages
→ **Look at**: Process monitoring, resource limits
→ **Commands**: `systemctl show service --property=MemoryCurrent`

### Network Connectivity Issues
→ **Check for**: "Connection refused", "Network unreachable"
→ **Look at**: Network service status, firewall rules
→ **Commands**: Check NetworkManager, firewalld, or systemd-networkd

### Permission Problems
→ **Check for**: "Permission denied", "Access denied"
→ **Look at**: File permissions, SELinux/AppArmor, user/group settings
→ **Commands**: Check file ownership and permissions

## 🕰️ **Log Timestamp Patterns**

### Boot Sequence Analysis
```
Look for timestamps clustering around boot time:
- systemd[1]: messages for core system startup
- kernel: messages for hardware initialization
- Various services starting in dependency order
```

### Service Restart Patterns
```
Service cycling (frequent restarts):
- "Stopped [Service]" followed by "Started [Service]"
- Look for underlying cause in error messages
- Check restart limits and backoff policies
```

### Failure Correlation
```
Multiple services failing simultaneously:
- May indicate system-wide issue (memory, disk, network)
- Check for common dependencies or resources
- Look for hardware or kernel messages
```

## 📊 **Log Analysis Strategies**

### Time-based Analysis
1. **Recent Issues**: Last 1-6 hours for current problems
2. **Daily Patterns**: Last 24-48 hours for recurring issues
3. **Long-term Trends**: Last week for pattern identification
4. **Boot Analysis**: Since last boot for startup issues

### Priority-based Analysis
1. **Critical/Alert**: System-wide failures, security breaches
2. **Error**: Service failures, application crashes
3. **Warning**: Performance issues, configuration problems
4. **Info**: Normal operations, status updates

### Service-specific Analysis
1. **Individual Services**: Focus on specific failing service
2. **Service Groups**: Related services (web stack, database cluster)
3. **System Services**: Core systemd services for system health
4. **User Services**: Application-specific services

## 📎 **Quick Reference Commands**

### Essential systemctl Commands
```
systemctl status [service]     # Service status and recent logs
systemctl list-units --failed  # List all failed units
systemctl list-dependencies    # Show service dependencies
systemctl show [service]       # Detailed service properties
systemctl is-active [service]  # Check if service is running
systemctl is-enabled [service] # Check if service is enabled
```

### Journal Queries
```
journalctl -u [service]        # Logs for specific service
journalctl -p err              # Only error priority logs
journalctl --since "1 hour ago" # Recent logs
journalctl -f                  # Follow logs in real-time
journalctl --list-boots        # Available boot sessions
journalctl -b 0                # Current boot logs
```

## ⚠️ **Best Practices**

### Log Analysis
- Start with failed services before investigating specific issues
- Use time-based filtering to focus on relevant time periods
- Look for patterns in error messages and timestamps
- Cross-reference service failures with system events

### Performance
- Use specific service filters to reduce log volume
- Query recent time periods first, then expand if needed
- Be aware that large journal queries may take time
- Consider log rotation and retention policies

### Security
- Monitor authentication logs regularly
- Check for unusual service start/stop patterns
- Review privilege escalation logs (sudo usage)
- Be aware of log retention for forensic analysis

**Remember**: systemd provides comprehensive logging and service management. Most issues can be diagnosed by examining service states, dependencies, and recent log entries. Always start with the systemd service status before diving into detailed log analysis.
"""
