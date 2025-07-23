"""
Windows testing and diagnostics prompts for the MCP Log Analyzer server.
"""

from mcp.server import FastMCP


def register_windows_testing_prompts(mcp: FastMCP):
    """Register all Windows testing prompts."""

    @mcp.prompt()
    async def windows_diagnostics_guide() -> str:
        """
        Comprehensive guide for Windows system diagnostics and testing.

        This prompt provides detailed guidance on using Windows Event Logs
        and system diagnostic tools for troubleshooting.
        """
        return """
# 🪟 Windows System Diagnostics Guide

## 📊 **Windows Event Log Analysis**

### Available Event Logs
- **System Log**: Hardware, drivers, system services, and kernel events
- **Application Log**: Application crashes, errors, and informational events
- **Security Log**: Authentication, authorization, and security audit events

### Event Log Testing Tools

#### 1. Test Event Log Access 🔍
```
Tool: test_windows_event_log_access
✅ Tests access to System, Application, and Security logs
✅ Verifies pywin32 package availability
✅ Checks permissions for each log type
✅ Provides diagnostic information
```

#### 2. Get Event Log Information 📊
```
Tool: get_windows_event_log_info
Parameters:
- log_name: "System", "Application", or "Security"
- max_entries: Number of recent entries to retrieve (default: 10)

Returns:
- Log metadata (creation time, last written, size)
- Recent log entries with formatted messages
- Event IDs, timestamps, and source information
```

#### 3. Query Events by Criteria 🎯
```
Tool: query_windows_events_by_criteria
Filters available:
- event_id: Specific Windows Event ID
- level: "Error", "Warning", "Information"
- time_duration: "30m", "2h", "1d", etc.
- max_entries: Result limit

Examples:
- All errors in last hour: level="Error", time_duration="1h"
- Specific Event ID: event_id=7001, time_duration="24h"
```

#### 4. System Health Overview 🎨
```
Tool: get_windows_system_health
✅ Analyzes last 24 hours of System and Application logs
✅ Counts errors and warnings
✅ Identifies critical events
✅ Provides overall health status: healthy/fair/concerning
```

## 📝 **Common Windows Event IDs**

### System Event Log
- **Event ID 7001**: Service start failures
- **Event ID 7023**: Service terminated with errors
- **Event ID 7026**: Boot-start driver failures
- **Event ID 1074**: System shutdown/restart events
- **Event ID 6005/6006**: Event Log service start/stop
- **Event ID 7000**: Service failed to start
- **Event ID 7011**: Service timeout

### Application Event Log
- **Event ID 1000**: Application crashes
- **Event ID 1001**: Windows Error Reporting
- **Event ID 1002**: Application hang events
- **Event ID 2001**: Perflib events
- **Event ID 4625**: Failed logon attempts (Security log)

### Security Event Log
- **Event ID 4624**: Successful logon
- **Event ID 4625**: Failed logon attempt
- **Event ID 4634**: Account logoff
- **Event ID 4648**: Logon using explicit credentials
- **Event ID 4720**: User account created
- **Event ID 4726**: User account deleted

## 🔧 **Diagnostic Workflows**

### 1. Initial System Health Check 🎨
```
Step 1: Test Event Log access
→ tool: test_windows_event_log_access

Step 2: Get system health overview
→ tool: get_windows_system_health

Step 3: Review critical events if health is concerning
→ Focus on Error level events in last 24 hours
```

### 2. Service Troubleshooting 🛠️
```
Step 1: Query service-related errors
→ event_id: 7001, 7023, 7000, 7011
→ time_duration: "6h" or "24h"

Step 2: Analyze service failure patterns
→ Look for recurring service names
→ Check timestamps for failure clustering

Step 3: Get detailed service information
→ Query specific Event IDs for failed services
```

### 3. Application Crash Analysis 💥
```
Step 1: Find application crashes
→ log_name: "Application"
→ event_id: 1000, 1001, 1002

Step 2: Identify problematic applications
→ Look for recurring application names
→ Check crash frequencies and timing

Step 3: Get crash details
→ Query specific timeframes around crashes
→ Review error messages and stack traces
```

### 4. Security Event Monitoring 🔒
```
Step 1: Check authentication events
→ log_name: "Security"
→ event_id: 4624, 4625
→ time_duration: "2h"

Step 2: Monitor failed logons
→ event_id: 4625
→ Look for brute force patterns

Step 3: Account management events
→ event_id: 4720, 4726 (user creation/deletion)
```

### 5. Boot and Startup Issues 🚀
```
Step 1: Check boot-related events
→ event_id: 7026 (driver failures)
→ event_id: 6005 (Event Log start)

Step 2: Service startup problems
→ event_id: 7000, 7001 (service failures)
→ time_duration: since last boot

Step 3: System restart events
→ event_id: 1074 (planned restarts)
→ Look for unexpected reboots
```

## 🎨 **Health Status Interpretation**

### Healthy System ✅
- 0 errors in last 24 hours
- <5 warnings in last 24 hours
- No critical service failures
- Regular successful logons

### Fair System ⚠️
- <3 errors in last 24 hours
- <20 warnings in last 24 hours
- Minor service issues
- Some application crashes

### Concerning System ❌
- 3+ errors in last 24 hours
- 20+ warnings in last 24 hours
- Critical service failures
- Security-related errors
- Frequent application crashes

## 🛠️ **Troubleshooting Tips**

### Permission Issues
- **Security Log Access**: Requires administrator privileges
- **pywin32 Missing**: Install with `pip install pywin32`
- **Access Denied**: Run as administrator or check user permissions

### Performance Optimization
- Use time-based filtering to reduce query scope
- Query specific Event IDs rather than all events
- Start with recent time periods (1h, 6h) before expanding

### Common Error Patterns
- **Recurring Service Failures**: Check service dependencies
- **Application Crashes**: Look for updated drivers or software
- **Authentication Failures**: Check for account lockouts or password issues
- **Driver Issues**: Boot-time driver failures may indicate hardware problems

## 🔍 **Advanced Query Examples**

### Find All Service Errors Today
```
log_name: "System"
event_id: [7000, 7001, 7023, 7011]
time_duration: "24h"
level: "Error"
```

### Application Crashes This Week
```
log_name: "Application"
event_id: [1000, 1001]
time_duration: "7d"
max_entries: 100
```

### Security Events Last Hour
```
log_name: "Security"
event_id: [4624, 4625]
time_duration: "1h"
max_entries: 50
```

## ⚠️ **Important Notes**

- **Administrator Rights**: Required for Security log access
- **Performance Impact**: Large time ranges may take longer to process
- **Event Log Size**: Logs rotate based on size/age settings
- **Time Zones**: Ensure system time zone is correct for accurate filtering
- **Dependencies**: Requires pywin32 package for Windows Event Log access

This comprehensive Windows diagnostics system provides deep insights into system health, service status, application stability, and security events for effective troubleshooting and monitoring.
"""

    @mcp.prompt()
    async def windows_event_reference() -> str:
        """
        Quick reference guide for common Windows Event IDs and their meanings.

        This prompt provides a searchable reference for Windows Event IDs
        commonly encountered during system troubleshooting.
        """
        return """
# 📖 Windows Event ID Reference Guide

## 🚑 **Critical System Events**

### Service Control Manager (Source: Service Control Manager)
- **7000**: Service failed to start due to logon failure
- **7001**: Service depends on another service that failed to start
- **7003**: Service depends on a group that failed to start
- **7009**: Service startup timeout (30 seconds default)
- **7011**: Service failed to start within timeout period
- **7022**: Service hung on starting
- **7023**: Service terminated with errors
- **7024**: Service terminated with service-specific error
- **7026**: Boot-start or system-start driver failed to load
- **7031**: Service terminated unexpectedly
- **7032**: Service Control Manager tried to take corrective action
- **7034**: Service terminated unexpectedly (no recovery action)

### System Events (Source: EventLog)
- **6005**: Event Log service started (system boot)
- **6006**: Event Log service stopped (system shutdown)
- **6008**: Previous system shutdown was unexpected
- **6009**: System version information
- **6013**: System uptime in seconds

### User32 Events (Source: USER32)
- **1074**: System has been shut down by a user or process
- **1076**: System shutdown reason codes

## 💻 **Application Events**

### Windows Error Reporting
- **1000**: Application crash (fault bucket information)
- **1001**: Windows Error Reporting (fault bucket summary)
- **1002**: Application hang event

### Application Specific
- **1001**: Application Error (generic application failure)
- **1002**: Application Hang (application became unresponsive)
- **1004**: Application Recovery (application was recovering)

### .NET Runtime Events
- **1026**: .NET Runtime unhandled exception
- **1023**: .NET Runtime just-in-time debugger error

## 🔒 **Security Events**

### Logon/Logoff Events
- **4624**: Account successfully logged on
- **4625**: Account failed to log on
- **4634**: Account logged off
- **4647**: User initiated logoff
- **4648**: Logon using explicit credentials
- **4672**: Special privileges assigned to new logon

### Account Management
- **4720**: User account created
- **4722**: User account enabled
- **4723**: User attempted to change password
- **4724**: User password reset
- **4725**: User account disabled
- **4726**: User account deleted
- **4738**: User account changed
- **4740**: User account locked out
- **4767**: User account unlocked

### Group Management
- **4728**: Member added to security-enabled global group
- **4729**: Member removed from security-enabled global group
- **4732**: Member added to security-enabled local group
- **4733**: Member removed from security-enabled local group

### Policy Changes
- **4719**: System audit policy changed
- **4739**: Domain policy changed
- **4902**: Per-user audit policy table created

### Object Access
- **4656**: Handle to object requested
- **4658**: Handle to object closed
- **4663**: Object access attempted

## 🔌 **Hardware Events**

### Disk Events (Source: Disk)
- **7**: Device has a bad block
- **11**: Driver detected controller error
- **15**: Device not ready for access
- **51**: Page fault error

### Kernel Events (Source: Microsoft-Windows-Kernel-General)
- **1**: System time changed
- **5**: System started
- **6**: System shutdown
- **12**: Operating system start
- **13**: Operating system shutdown

## 🌐 **Network Events**

### DHCP Client (Source: Microsoft-Windows-Dhcp-Client)
- **1002**: DHCP address assignment
- **1003**: DHCP renewal
- **1006**: DHCP address conflict

### DNS Client (Source: Microsoft-Windows-DNS-Client)
- **1014**: DNS name resolution timeout
- **5011**: DNS client service error

### Network Profile (Source: Microsoft-Windows-NetworkProfile)
- **10000**: Network connected
- **10001**: Network disconnected

## 🔍 **Event Level Classifications**

### Error (Level 2) ❌
- System failures
- Service crashes
- Application errors
- Hardware problems
- Critical security events

### Warning (Level 3) ⚠️
- Performance issues
- Non-critical failures
- Configuration problems
- Resource constraints
- Security concerns

### Information (Level 4) ℹ️
- Normal operations
- Service starts/stops
- Successful logons
- Configuration changes
- Status updates

### Verbose (Level 5) 📝
- Detailed operation logs
- Debug information
- Trace events
- Performance data

## 🔍 **Common Troubleshooting Scenarios**

### System Won't Boot
→ Look for: 7026, 7000, 7001, 7023 in System log
→ Check for: Hardware errors (Disk events 7, 11, 15)

### Service Issues
→ Look for: 7000-7034 range in System log
→ Focus on: Specific service names in event descriptions

### Application Crashes
→ Look for: 1000, 1001, 1002 in Application log
→ Check for: .NET events 1026, 1023 for managed applications

### Security Concerns
→ Look for: 4625 (failed logons), 4740 (lockouts)
→ Monitor: 4720, 4726 (account creation/deletion)

### Performance Issues
→ Look for: Warning level events in System log
→ Check for: Resource-related errors and timeouts

## 📊 **Event Frequency Analysis**

### Normal Frequency
- **4624/4634**: Multiple per day (user logons/logoffs)
- **6005/6006**: Once per boot cycle
- **1074**: Occasional (planned restarts)

### Concerning Frequency
- **4625**: Multiple failed logons (potential brute force)
- **1000**: Frequent application crashes
- **7000-7034**: Recurring service failures

### Investigation Triggers
- Same Event ID occurring >10 times per hour
- Critical events (7000, 7026) during boot
- Security events outside normal patterns
- New Event IDs not seen before

**Pro Tip**: Use time-based filtering to correlate events and identify patterns. Events occurring within minutes of each other may be related to the same underlying issue.
"""
