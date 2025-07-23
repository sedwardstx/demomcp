"""
Log Management prompts for the MCP Log Analyzer server.
"""

from mcp.server import FastMCP


def register_log_management_prompts(mcp: FastMCP):
    """Register all log management prompts."""

    @mcp.prompt()
    async def log_management_guide() -> str:
        """
        Comprehensive guide for log management and analysis.

        This prompt provides detailed guidance on registering, querying,
        and analyzing various types of log sources.
        """
        return """
# 📊 MCP Log Analyzer - Log Management Guide

## 📝 **Supported Log Types**

### Windows Event Logs (evt)
- **System Event Logs**: Windows system events, hardware issues, driver problems
- **Application Event Logs**: Application crashes, errors, and informational events
- **Security Event Logs**: Authentication, authorization, and security events

### Structured Logs
- **JSON Logs**: Application logs in JSON format with structured data
- **XML Logs**: Structured XML log files with hierarchical data
- **CSV Logs**: Comma-separated log files with tabular data

### Unstructured Logs
- **Text Logs**: Plain text log files (syslog, application logs, etc.)
- **Custom Formats**: Any text-based log format with custom parsing rules

## 🔧 **Core Log Management Workflow**

### 1. Register Log Sources 💾
```
Tool: register_log_source
- name: Unique identifier for your log source
- source_type: Type of log (evt, json, xml, csv, text)
- path: File path or directory containing logs
- config: Additional parser configuration
```

### 2. List and Manage Sources 📋
```
Tools available:
- list_log_sources: View all registered sources
- get_log_source: Get details about a specific source
- delete_log_source: Remove a source when no longer needed
```

### 3. Query and Filter Logs 🔍
```
Tool: query_logs
- source_name: Which registered source to query
- filters: Apply specific criteria (level, event_id, etc.)
- start_time/end_time: Define time ranges
- limit/offset: Paginate through large result sets
```

### 4. Analyze Patterns and Anomalies 📊
```
Tool: analyze_logs
Analysis types:
- summary: General statistics and overview
- pattern: Detect recurring patterns and frequencies
- anomaly: Identify unusual or suspicious log entries
```

## 🎯 **Usage Examples**

### Windows Event Log Analysis
```
1. Register Windows System Events:
   - name: "windows_system"
   - source_type: "evt"
   - path: "System"

2. Query recent errors:
   - filters: {"level": "Error"}
   - start_time: Last 24 hours

3. Analyze error patterns:
   - analysis_type: "pattern"
```

### Application Log Analysis
```
1. Register JSON application logs:
   - name: "app_logs"
   - source_type: "json"
   - path: "/var/log/myapp/app.json"

2. Query specific errors:
   - filters: {"severity": "error", "component": "database"}

3. Detect anomalies:
   - analysis_type: "anomaly"
```

### System Log Monitoring
```
1. Register syslog:
   - name: "syslog"
   - source_type: "text"
   - path: "/var/log/syslog"

2. Query authentication events:
   - filters: {"message_contains": "authentication"}

3. Generate summary report:
   - analysis_type: "summary"
```

## 🔍 **Advanced Filtering Options**

### Time-based Filters
- **start_time/end_time**: Specific datetime ranges
- **last_hours**: Recent time periods (1h, 6h, 24h)
- **date_range**: Daily, weekly, or monthly ranges

### Content Filters
- **level/severity**: Error levels (Error, Warning, Info, Debug)
- **event_id**: Specific Windows Event IDs
- **source**: Log source or component name
- **message_contains**: Text search within log messages
- **regex_pattern**: Advanced pattern matching

### Logical Operators
- **AND conditions**: Multiple criteria must match
- **OR conditions**: Any criteria can match
- **NOT conditions**: Exclude specific criteria

## 📊 **Analysis Capabilities**

### Summary Analysis
- **Total log count** and time range coverage
- **Error/Warning/Info** distribution
- **Top sources** and components
- **Peak activity periods**

### Pattern Analysis
- **Frequent error messages** and their occurrence rates
- **Event sequences** and correlations
- **Recurring issues** and their patterns
- **Time-based trends** (hourly, daily patterns)

### Anomaly Detection
- **Unusual error spikes** or drops
- **New error types** not seen before
- **Unexpected source activity**
- **Timing anomalies** (events at unusual times)

## 🚀 **Best Practices**

### Log Source Management
- ✅ Use descriptive names for log sources
- ✅ Register logs by type and system for organization
- ✅ Set appropriate parsing configurations
- ✅ Remove unused sources to keep the system clean

### Querying Efficiently
- ✅ Use time ranges to limit data scope
- ✅ Apply specific filters to reduce noise
- ✅ Start with summary analysis before detailed queries
- ✅ Use pagination for large result sets

### Analysis Strategy
- ✅ Begin with summary analysis for overview
- ✅ Use pattern analysis to identify recurring issues
- ✅ Apply anomaly detection for security monitoring
- ✅ Combine multiple analysis types for comprehensive insights

## ⚠️ **Important Notes**

- **Permissions**: Ensure proper read access to log files
- **Performance**: Large log files may require time-based filtering
- **Storage**: Consider log retention policies for disk space
- **Security**: Be cautious with sensitive log data in filters
- **Platform**: Some log types are platform-specific (Windows Event Logs)

This comprehensive log management system supports everything from simple log viewing to advanced pattern detection and anomaly analysis across multiple platforms and log formats.
"""

    @mcp.prompt()
    async def log_troubleshooting_guide() -> str:
        """
        Guide for troubleshooting common log analysis issues.

        This prompt helps diagnose and resolve problems with log
        registration, parsing, and analysis.
        """
        return """
# 🔧 Log Management Troubleshooting Guide

## 🚫 **Common Registration Issues**

### Problem: "Log source already exists"
💡 **Solution**:
1. Use `list_log_sources` to check existing sources
2. Use `delete_log_source` to remove if needed
3. Choose a different unique name

### Problem: "Unsupported source type"
💡 **Solution**:
1. Use supported types: `evt`, `json`, `xml`, `csv`, `text`
2. Check spelling and case sensitivity
3. Consider using `text` type for custom formats

### Problem: "File not found or access denied"
💡 **Solution**:
1. Verify file path exists and is correct
2. Check file permissions and read access
3. For Windows Event Logs, ensure admin privileges
4. Test with `test_windows_event_log_access` or `test_linux_log_access`

## 🔍 **Query and Filtering Issues**

### Problem: "No logs returned"
💡 **Solution**:
1. Verify time range includes expected data
2. Remove or adjust filters that might be too restrictive
3. Check log source has data in the specified time period
4. Start with broader filters and narrow down

### Problem: "Query timeout or performance issues"
💡 **Solution**:
1. Reduce time range scope
2. Add more specific filters to limit data
3. Use pagination (limit/offset) for large datasets
4. Consider analyzing smaller time windows

### Problem: "Invalid filter format"
💡 **Solution**:
1. Check filter syntax matches expected format
2. Use correct field names for the log type
3. Verify datetime formats for time-based filters
4. Test filters incrementally

## 📊 **Analysis Problems**

### Problem: "Analysis failed or returned empty results"
💡 **Solution**:
1. Ensure logs contain data in the specified time range
2. Verify analysis type is supported (`summary`, `pattern`, `anomaly`)
3. Check that filters don't exclude all relevant data
4. Try with a smaller dataset first

### Problem: "Pattern analysis finds no patterns"
💡 **Solution**:
1. Increase time range to capture more data
2. Adjust pattern detection sensitivity
3. Ensure log format is consistent
4. Try different analysis parameters

### Problem: "Anomaly detection not working"
💡 **Solution**:
1. Ensure baseline data exists (normal behavior)
2. Increase time window for better baseline
3. Adjust anomaly detection thresholds
4. Verify log data has sufficient variety

## 🕰️ **Time Range Issues**

### Problem: "Time parsing errors"
💡 **Solution**:
1. Use ISO format: `YYYY-MM-DD HH:MM:SS`
2. Ensure timezone consistency
3. Check that start_time is before end_time
4. Use relative times when possible

### Problem: "No data in time range"
💡 **Solution**:
1. Verify log timestamps match expected format
2. Check system timezone settings
3. Expand time range to find available data
4. Use `summary` analysis to see data distribution

## 🛠️ **Platform-Specific Issues**

### Windows Event Log Issues
- **Problem**: pywin32 module not available
- **Solution**: Install pywin32 package
- **Problem**: Access denied to Security logs
- **Solution**: Run with administrator privileges

### Linux Log Issues
- **Problem**: systemd journal not accessible
- **Solution**: Check user permissions for journal access
- **Problem**: Log files in /var/log not readable
- **Solution**: Verify file permissions and user groups

## 📝 **Diagnostic Steps**

### Step 1: Test System Access
```
Windows: Use test_windows_event_log_access
Linux: Use test_linux_log_access
```

### Step 2: Verify Log Source
```
1. Use get_log_source to check registration
2. Verify file path and permissions
3. Test with simple query first
```

### Step 3: Start Simple
```
1. Query without filters
2. Use small time ranges
3. Gradually add complexity
```

### Step 4: Check Error Messages
```
1. Read error messages carefully
2. Check system logs for additional context
3. Verify prerequisites are met
```

## 🚀 **Performance Optimization**

### For Large Log Files
- Use time-based filtering to reduce data scope
- Implement pagination for large result sets
- Consider indexing for frequently accessed logs
- Use specific filters rather than broad searches

### For Multiple Sources
- Register sources with descriptive names
- Group related sources logically
- Remove unused sources regularly
- Cache analysis results when possible

### For Real-time Monitoring
- Use recent time ranges (last hour, last day)
- Focus on error and warning levels
- Set up automated analysis for critical patterns
- Monitor system resource usage during analysis

**Remember**: Start with basic functionality and gradually build complexity. Most issues can be resolved by verifying permissions, checking file paths, and using appropriate time ranges.
"""
