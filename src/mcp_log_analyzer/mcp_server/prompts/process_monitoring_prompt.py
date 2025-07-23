"""
Process monitoring and system resource prompts for the MCP Log Analyzer server.
"""

from mcp.server import FastMCP


def register_process_monitoring_prompts(mcp: FastMCP):
    """Register all process monitoring prompts."""

    @mcp.prompt()
    async def process_monitoring_guide() -> str:
        """
        Comprehensive guide for process monitoring and system resource analysis.

        This prompt provides detailed guidance on monitoring system performance,
        analyzing resource usage, and troubleshooting process-related issues.
        """
        return """
# 🖥️ Process Monitoring and System Resource Guide

## 📊 **System Resource Monitoring**

### Available Monitoring Tools

#### 1. System Resources Access Test 🔍
```
Tool: test_system_resources_access
✅ Tests CPU monitoring capabilities
✅ Verifies memory access and statistics
✅ Checks disk usage monitoring
✅ Tests network I/O counters
✅ Validates process enumeration
✅ Reports psutil library version and capabilities
```

#### 2. System Performance Analysis 📊
```
Tool: analyze_system_performance
Parameters:
- include_network: Include network statistics (default: true)
- include_disk: Include disk I/O statistics (default: true)
- sample_interval: Sampling interval in seconds (default: 1.0)

Capabilities:
✅ CPU usage, frequency, and load average
✅ Memory (virtual and swap) usage statistics
✅ Disk usage and I/O counters
✅ Network I/O and active connections
✅ Performance status assessment (good/fair/concerning)
```

#### 3. Resource-Intensive Process Analysis 🔍
```
Tool: find_resource_intensive_processes
Parameters:
- process_name: Filter by specific process name
- min_cpu_percent: Minimum CPU usage threshold (default: 0.0)
- min_memory_percent: Minimum memory usage threshold (default: 0.0)
- max_results: Maximum number of processes to return (default: 20)
- sort_by: Sort by 'cpu', 'memory', or 'pid' (default: 'cpu')

Capabilities:
✅ Identifies high CPU and memory consumers
✅ Provides detailed process information
✅ Calculates summary statistics
✅ Supports filtering and sorting options
```

#### 4. Process Health Monitoring 🎨
```
Tool: monitor_process_health
Parameters:
- process_name: Specific process name to monitor

Capabilities:
✅ Monitors specific process health and status
✅ Tracks resource usage over time
✅ Reports process age and connection count
✅ Identifies potential health issues
✅ Handles multiple instances of the same process
```

#### 5. System Health Summary 📊
```
Tool: get_system_health_summary
✅ Overall system health assessment
✅ Resource usage summary (CPU, memory, disk)
✅ Top process consumers by CPU and memory
✅ Health score calculation (0-100)
✅ Issues identification and recommendations
```

## 📊 **Resource Metrics Explained**

### CPU Metrics
- **Usage Percent**: Current CPU utilization (0-100%)
- **Core Count**: Physical and logical CPU cores
- **Frequency**: Current, minimum, and maximum CPU frequency
- **Load Average**: System load over 1, 5, and 15 minutes (Linux/Unix)

### Memory Metrics
- **Total Memory**: Total physical RAM available
- **Available Memory**: Memory available for new processes
- **Used Memory**: Currently allocated memory
- **Memory Percent**: Percentage of memory in use
- **Swap Usage**: Virtual memory usage and percentage

### Disk Metrics
- **Disk Usage**: Total, used, and free space
- **Disk Percent**: Percentage of disk space used
- **Read/Write Bytes**: Total bytes read/written
- **Read/Write Count**: Number of read/write operations

### Network Metrics
- **Bytes Sent/Received**: Total network traffic
- **Packets Sent/Received**: Total packet counts
- **Active Connections**: Current network connections

### Process Metrics
- **PID**: Process identifier
- **CPU Percent**: Process CPU usage
- **Memory Percent**: Process memory usage
- **Memory MB**: Process memory in megabytes
- **Process Status**: Running, sleeping, zombie, etc.
- **Create Time**: When process was started
- **Command Line**: Process command and arguments

## 🔧 **Monitoring Workflows**

### 1. Initial System Health Assessment 🎨
```
Step 1: Test system resource access
→ tool: test_system_resources_access

Step 2: Get overall system health summary
→ tool: get_system_health_summary

Step 3: Analyze current performance
→ tool: analyze_system_performance

Step 4: Identify resource-intensive processes
→ tool: find_resource_intensive_processes (sort_by="cpu")
```

### 2. Performance Troubleshooting 🛠️
```
Step 1: Identify performance bottlenecks
→ tool: analyze_system_performance
→ Look for high CPU, memory, or disk usage

Step 2: Find resource-intensive processes
→ tool: find_resource_intensive_processes
→ Set appropriate thresholds (min_cpu_percent, min_memory_percent)

Step 3: Monitor specific problematic processes
→ tool: monitor_process_health
→ Focus on high-usage processes identified in step 2

Step 4: Analyze trends and patterns
→ Look for consistent high usage vs spikes
→ Check for memory leaks or runaway processes
```

### 3. Capacity Planning 📊
```
Step 1: Baseline system performance
→ tool: get_system_health_summary
→ Document normal operating levels

Step 2: Monitor resource trends
→ tool: analyze_system_performance
→ Track usage patterns over time

Step 3: Identify growth patterns
→ Look for increasing memory/CPU usage trends
→ Monitor disk space growth

Step 4: Plan resource upgrades
→ Use trend data to predict future needs
```

### 4. Process Health Monitoring 👩‍⚕️
```
Step 1: Identify critical processes
→ List essential services and applications

Step 2: Monitor process health
→ tool: monitor_process_health
→ Check each critical process individually

Step 3: Set up alerting thresholds
→ Define acceptable CPU/memory limits
→ Monitor for process crashes or restarts

Step 4: Track process lifecycle
→ Monitor process age and stability
→ Check for memory leaks over time
```

### 5. Security Monitoring 🔒
```
Step 1: Monitor for suspicious processes
→ tool: find_resource_intensive_processes
→ Look for unknown or unexpected high-usage processes

Step 2: Check process command lines
→ Review command-line arguments for suspicious activity
→ Look for processes running from unusual locations

Step 3: Monitor network connections
→ Check active connections for unusual patterns
→ Look for unexpected outbound connections

Step 4: Track process creation
→ Monitor for new processes or frequent process creation
```

## 🎨 **Health Status Interpretation**

### Excellent Health (Score: 80-100) ✅
- CPU usage < 60%
- Memory usage < 75%
- Disk usage < 80%
- No resource-intensive processes
- Stable process ecosystem

### Good Health (Score: 60-79) ⚠️
- CPU usage 60-80%
- Memory usage 75-90%
- Disk usage 80-90%
- Some resource-intensive processes
- Generally stable performance

### Fair Health (Score: 40-59) 🟡
- CPU usage 80-90%
- Memory usage 90-95%
- Disk usage 90-95%
- Multiple resource-intensive processes
- Performance degradation visible

### Poor Health (Score: 0-39) ❌
- CPU usage > 90%
- Memory usage > 95%
- Disk usage > 95%
- System overloaded
- Critical performance issues

## 🛠️ **Common Performance Issues**

### High CPU Usage
**Symptoms**: CPU > 80% consistently
**Causes**:
- CPU-intensive applications
- Infinite loops or runaway processes
- Insufficient CPU cores for workload
- Background system tasks

**Investigation Steps**:
1. Find top CPU consumers
2. Check process command lines
3. Monitor CPU usage over time
4. Look for periodic spikes vs constant usage

### High Memory Usage
**Symptoms**: Memory > 90% consistently
**Causes**:
- Memory leaks in applications
- Insufficient RAM for workload
- Memory-intensive applications
- Cache and buffer usage

**Investigation Steps**:
1. Find top memory consumers
2. Check memory growth over time
3. Monitor swap usage
4. Look for memory leak patterns

### High Disk Usage
**Symptoms**: Disk > 90% full
**Causes**:
- Log file accumulation
- Data growth without cleanup
- Large temporary files
- Backup files not cleaned up

**Investigation Steps**:
1. Identify large files and directories
2. Check disk I/O patterns
3. Review log rotation policies
4. Monitor disk growth trends

### Process Issues
**Symptoms**: Process crashes, high resource usage
**Causes**:
- Application bugs
- Resource exhaustion
- Configuration issues
- External dependencies

**Investigation Steps**:
1. Monitor process health over time
2. Check process logs for errors
3. Review resource limits
4. Analyze process dependencies

## 📊 **Monitoring Best Practices**

### Baseline Establishment
- ✅ Document normal resource usage patterns
- ✅ Identify typical CPU, memory, and disk utilization
- ✅ Record normal process behavior
- ✅ Establish performance benchmarks

### Regular Monitoring
- ✅ Check system health summary daily
- ✅ Monitor resource-intensive processes
- ✅ Track performance trends over time
- ✅ Set up alerting for critical thresholds

### Proactive Maintenance
- ✅ Address high resource usage before it becomes critical
- ✅ Plan capacity upgrades based on trends
- ✅ Regular cleanup of unnecessary processes
- ✅ Monitor for memory leaks and resource exhaustion

### Documentation
- ✅ Keep records of normal vs abnormal behavior
- ✅ Document known resource-intensive processes
- ✅ Track changes in system performance
- ✅ Maintain process health history

## 📎 **Quick Reference Thresholds**

### CPU Usage Guidelines
- **0-30%**: Normal/light usage
- **30-60%**: Moderate usage
- **60-80%**: High usage (monitor closely)
- **80-95%**: Very high usage (investigate)
- **95-100%**: Critical usage (immediate action)

### Memory Usage Guidelines
- **0-60%**: Normal usage
- **60-75%**: Moderate usage
- **75-85%**: High usage (monitor closely)
- **85-95%**: Very high usage (investigate)
- **95-100%**: Critical usage (immediate action)

### Process Count Guidelines
- **<100**: Light system load
- **100-300**: Normal system load
- **300-500**: Moderate system load
- **500-1000**: High system load
- **>1000**: Very high system load

## ⚠️ **Important Considerations**

### Performance Impact
- Monitoring tools consume system resources
- Frequent monitoring may impact performance
- Balance monitoring frequency with system load
- Consider monitoring overhead in capacity planning

### Platform Differences
- Some metrics may not be available on all platforms
- Windows and Linux have different process models
- Process enumeration permissions vary by system
- Network monitoring capabilities differ by OS

### Security Implications
- Process monitoring may reveal sensitive information
- Ensure appropriate access controls
- Be cautious with process command-line data
- Consider privacy implications of monitoring data

This comprehensive process monitoring system provides detailed insights into system performance, resource utilization, and process health for effective system administration and troubleshooting.
"""

    @mcp.prompt()
    async def process_troubleshooting_guide() -> str:
        """
        Specialized guide for troubleshooting process and performance issues.

        This prompt focuses on diagnosing and resolving specific performance
        problems and process-related issues.
        """
        return """
# 🔧 Process Troubleshooting and Performance Issues Guide

## 🚫 **Common Process Problems**

### High CPU Usage Troubleshooting

#### Problem: Single Process Consuming High CPU
💡 **Investigation Steps**:
1. **Identify the process**:
   ```
   Tool: find_resource_intensive_processes
   Parameters: min_cpu_percent=50, sort_by="cpu"
   ```

2. **Monitor process behavior**:
   ```
   Tool: monitor_process_health
   Parameters: process_name="problematic-process"
   ```

3. **Check process details**:
   - Review command line arguments
   - Check process age (recent start = potential issue)
   - Look for multiple instances

**Common Causes & Solutions**:
- **Infinite loops**: Restart application, check code
- **CPU-intensive tasks**: Normal behavior, consider scheduling
- **Stuck processes**: Kill and restart process
- **Resource contention**: Check for locking issues

#### Problem: System-wide High CPU Usage
💡 **Investigation Steps**:
1. **Get system overview**:
   ```
   Tool: get_system_health_summary
   ```

2. **Find all high CPU processes**:
   ```
   Tool: find_resource_intensive_processes
   Parameters: min_cpu_percent=10, max_results=50
   ```

3. **Analyze CPU distribution**:
   - Check if multiple processes are competing
   - Look for system processes vs user processes
   - Check for background tasks

**Solutions**:
- **Too many processes**: Reduce concurrent tasks
- **Insufficient CPU cores**: Hardware upgrade needed
- **Background tasks**: Schedule during off-peak hours
- **System processes**: Check for malware or system issues

### Memory Usage Issues

#### Problem: Memory Leak Detection
💡 **Investigation Steps**:
1. **Monitor memory trends**:
   ```
   Tool: analyze_system_performance
   Parameters: sample_interval=1.0
   ```

2. **Track specific process memory**:
   ```
   Tool: monitor_process_health
   Parameters: process_name="suspected-process"
   ```

3. **Look for growing memory usage**:
   - Check process age vs memory usage
   - Look for steadily increasing memory
   - Compare memory usage to expected levels

**Memory Leak Indicators**:
- Process memory increases over time without decreasing
- Memory usage disproportionate to process age
- System memory gradually decreasing
- Swap usage increasing over time

**Solutions**:
- **Application restart**: Temporary fix for memory leaks
- **Code review**: Fix memory management in application
- **Memory limits**: Set process memory limits
- **Monitoring**: Implement automated restart on high memory

#### Problem: Out of Memory Conditions
💡 **Investigation Steps**:
1. **Check system memory status**:
   ```
   Tool: analyze_system_performance
   Parameters: include_network=false, include_disk=false
   ```

2. **Find memory-intensive processes**:
   ```
   Tool: find_resource_intensive_processes
   Parameters: min_memory_percent=5, sort_by="memory"
   ```

3. **Check swap usage**:
   - High swap usage indicates memory pressure
   - Frequent swapping causes performance issues

**Solutions**:
- **Kill unnecessary processes**: Free up memory
- **Increase swap space**: Temporary relief
- **Add more RAM**: Hardware upgrade
- **Optimize applications**: Reduce memory footprint

### Process Stability Issues

#### Problem: Processes Keep Crashing
💡 **Investigation Steps**:
1. **Monitor process health**:
   ```
   Tool: monitor_process_health
   Parameters: process_name="crashing-process"
   ```

2. **Check for patterns**:
   - Note crash frequency and timing
   - Check if crashes correlate with high resource usage
   - Look for external triggers (network, disk I/O)

3. **Resource analysis**:
   ```
   Tool: find_resource_intensive_processes
   Parameters: process_name="crashing-process"
   ```

**Common Crash Causes**:
- **Out of memory**: Process exceeds memory limits
- **Segmentation fault**: Application bug or corruption
- **Resource exhaustion**: File descriptors, network connections
- **External dependencies**: Database, network service failures

**Solutions**:
- **Increase resource limits**: ulimit, systemd limits
- **Fix application bugs**: Code review and debugging
- **Improve error handling**: Graceful degradation
- **Monitor dependencies**: Check external service health

#### Problem: Zombie Processes
💡 **Investigation Steps**:
1. **Find zombie processes**:
   ```
   Tool: find_resource_intensive_processes
   # Look for processes with status "zombie"
   ```

2. **Identify parent processes**:
   - Zombie processes are cleaned up by parent
   - Parent process may not be handling SIGCHLD

**Solutions**:
- **Restart parent process**: Forces cleanup of zombies
- **Fix parent process**: Proper signal handling
- **System reboot**: Last resort for persistent zombies

## 📊 **Performance Optimization Strategies**

### CPU Optimization

#### Process Scheduling
- **Nice values**: Lower priority for non-critical processes
- **CPU affinity**: Bind processes to specific cores
- **Process distribution**: Spread load across cores

#### Application Optimization
- **Threading**: Use appropriate number of threads
- **Asynchronous I/O**: Reduce CPU waiting for I/O
- **Caching**: Reduce computational overhead

### Memory Optimization

#### Memory Management
- **Process memory limits**: Prevent runaway memory usage
- **Swap configuration**: Optimize swap usage patterns
- **Memory cleanup**: Regular garbage collection

#### Application Strategies
- **Memory pooling**: Reuse memory allocations
- **Lazy loading**: Load data only when needed
- **Data compression**: Reduce memory footprint

### Disk I/O Optimization

#### I/O Patterns
- **Sequential vs random**: Optimize access patterns
- **Batch operations**: Reduce I/O overhead
- **Caching**: Use memory for frequently accessed data

#### Storage Management
- **SSD vs HDD**: Choose appropriate storage type
- **RAID configuration**: Balance performance and redundancy
- **File system tuning**: Optimize for workload

## 🔍 **Diagnostic Tools and Techniques**

### Real-time Monitoring
```
Continuous monitoring setup:
1. Use get_system_health_summary every 5 minutes
2. Monitor top processes with find_resource_intensive_processes
3. Track specific processes with monitor_process_health
4. Alert on thresholds exceeded
```

### Historical Analysis
```
Trend analysis:
1. Collect performance data over time
2. Look for patterns and anomalies
3. Correlate with system events
4. Plan capacity based on trends
```

### Load Testing
```
Performance validation:
1. Baseline system performance
2. Apply controlled load
3. Monitor resource usage during load
4. Identify bottlenecks and limits
```

## 🛠️ **Emergency Response Procedures**

### High CPU Emergency
1. **Immediate**: Find top CPU consumers
2. **Assess**: Determine if processes can be safely killed
3. **Action**: Kill non-critical high-CPU processes
4. **Monitor**: Verify CPU usage returns to normal
5. **Investigate**: Root cause analysis after stabilization

### Memory Emergency
1. **Immediate**: Check available memory and swap
2. **Assess**: Find largest memory consumers
3. **Action**: Kill unnecessary processes to free memory
4. **Monitor**: Verify memory pressure is relieved
5. **Plan**: Schedule memory upgrade if needed

### Disk Space Emergency
1. **Immediate**: Check disk usage percentage
2. **Assess**: Find largest files and directories
3. **Action**: Clean up logs, temporary files, old backups
4. **Monitor**: Verify sufficient free space
5. **Implement**: Automated cleanup policies

### System Unresponsive
1. **Immediate**: Check system health summary
2. **Assess**: Identify resource exhaustion cause
3. **Action**: Kill problematic processes
4. **Fallback**: System restart if necessary
5. **Prevent**: Implement monitoring and limits

## 📎 **Process Monitoring Checklist**

### Daily Monitoring
- [ ] Check system health summary
- [ ] Review top CPU and memory consumers
- [ ] Verify critical processes are running
- [ ] Check for any zombie processes
- [ ] Monitor disk space usage

### Weekly Analysis
- [ ] Analyze performance trends
- [ ] Review process crash logs
- [ ] Check for memory leak indicators
- [ ] Validate monitoring thresholds
- [ ] Update capacity planning estimates

### Monthly Review
- [ ] Comprehensive performance analysis
- [ ] Review and update process documentation
- [ ] Assess need for hardware upgrades
- [ ] Test emergency response procedures
- [ ] Update monitoring and alerting rules

## ⚠️ **Warning Signs to Watch For**

### Critical Indicators
- CPU usage > 90% for extended periods
- Memory usage > 95% consistently
- Disk usage > 95%
- Frequent process crashes
- Growing number of zombie processes
- Increasing swap usage over time

### Early Warning Signs
- Gradual increase in resource usage
- New processes appearing regularly
- Performance degradation reports
- Increasing response times
- Memory usage trending upward

**Remember**: Proactive monitoring and early intervention prevent most performance crises. Regular monitoring, trend analysis, and capacity planning are key to maintaining system health and performance.
"""
