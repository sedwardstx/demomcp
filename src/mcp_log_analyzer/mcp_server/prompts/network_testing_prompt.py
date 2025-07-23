"""
Network testing and diagnostics prompts for the MCP Log Analyzer server.
"""

from mcp.server import FastMCP


def register_network_testing_prompts(mcp: FastMCP):
    """Register all network testing prompts."""

    @mcp.prompt()
    async def network_diagnostics_guide() -> str:
        """
        Comprehensive guide for network diagnostics and troubleshooting.

        This prompt provides detailed guidance on using network diagnostic
        tools and analyzing network connectivity issues.
        """
        return """
# 🌐 Network Diagnostics and Troubleshooting Guide

## 📊 **Network Diagnostic Tools**

### Available Network Tools

#### 1. Network Tools Availability Test 🔍
```
Tool: test_network_tools_availability
✅ Tests availability of essential network diagnostic tools
✅ Checks ping, netstat, ss, nslookup, curl, wget, telnet, nc
✅ Provides platform compatibility information
✅ Reports tool availability percentage
✅ Identifies missing network utilities
```

#### 2. Port Connectivity Testing 🔌
```
Tool: test_port_connectivity
Parameters:
- ports: List of ports to test (e.g., [80, 443, 22, 3306])
- host: Target host (default: "localhost")
- timeout: Connection timeout in seconds (default: 5)

Capabilities:
✅ Tests TCP port accessibility
✅ Measures connection response times
✅ Identifies open, closed, and filtered ports
✅ Provides summary statistics
✅ Handles connection timeouts gracefully
```

#### 3. Network Connectivity Testing 📋
```
Tool: test_network_connectivity
Parameters:
- hosts: List of hosts to test (default: ["8.8.8.8", "google.com", "github.com"])
- ping_count: Number of ping packets (default: 3)

Capabilities:
✅ Tests network reachability using ping
✅ Measures latency and packet loss
✅ Cross-platform ping command support
✅ Parses ping output for statistics
✅ Provides connectivity success rates
```

#### 4. Network Connection Analysis 🔍
```
Tool: analyze_network_connections
Parameters:
- include_listening: Include listening ports analysis (default: true)
- include_established: Include established connections (default: true)
- analyze_traffic: Analyze traffic patterns (default: false)

Capabilities:
✅ Analyzes current network connections
✅ Lists listening ports and services
✅ Shows established connections
✅ Provides network interface information
✅ Cross-platform netstat/ss support
```

#### 5. Comprehensive Network Diagnostics 🎨
```
Tool: diagnose_network_issues
✅ Tests basic connectivity to well-known servers
✅ Validates DNS resolution functionality
✅ Checks common port accessibility
✅ Reports network interface status
✅ Provides overall network health assessment
✅ Generates troubleshooting recommendations
```

## 🔌 **Port and Service Reference**

### Common Network Ports
- **HTTP (80)**: Web traffic (unencrypted)
- **HTTPS (443)**: Secure web traffic
- **SSH (22)**: Secure shell remote access
- **FTP (21)**: File transfer protocol
- **SMTP (25)**: Email sending
- **DNS (53)**: Domain name resolution
- **POP3 (110)**: Email retrieval
- **IMAP (143)**: Email access
- **SNMP (161)**: Network management
- **LDAP (389)**: Directory services

### Database Ports
- **MySQL (3306)**: MySQL database
- **PostgreSQL (5432)**: PostgreSQL database
- **MongoDB (27017)**: MongoDB database
- **Redis (6379)**: Redis in-memory database
- **Oracle (1521)**: Oracle database
- **SQL Server (1433)**: Microsoft SQL Server

### Application Ports
- **Tomcat (8080)**: Apache Tomcat
- **Jenkins (8080)**: Jenkins CI/CD
- **Elasticsearch (9200)**: Elasticsearch search
- **RabbitMQ (5672)**: Message queue
- **Docker (2376)**: Docker daemon
- **Kubernetes (6443)**: Kubernetes API

## 🔧 **Network Troubleshooting Workflows**

### 1. Basic Connectivity Check 🎨
```
Step 1: Test network tools availability
→ tool: test_network_tools_availability

Step 2: Run comprehensive network diagnostics
→ tool: diagnose_network_issues

Step 3: Test specific connectivity
→ tool: test_network_connectivity
→ Include local network and internet hosts

Step 4: Analyze current connections
→ tool: analyze_network_connections
```

### 2. Service Accessibility Testing 🔌
```
Step 1: Test common service ports
→ tool: test_port_connectivity
→ ports: [80, 443, 22, 25, 53]

Step 2: Test application-specific ports
→ tool: test_port_connectivity
→ ports: [3306, 5432, 8080] (adjust for your services)

Step 3: Check listening services
→ tool: analyze_network_connections
→ include_listening: true

Step 4: Verify service responses
→ Use specific tools (curl, telnet) for detailed testing
```

### 3. Performance and Latency Analysis 📊
```
Step 1: Measure baseline connectivity
→ tool: test_network_connectivity
→ Test multiple hosts with increased ping count

Step 2: Test port response times
→ tool: test_port_connectivity
→ Monitor connection times to critical services

Step 3: Analyze connection patterns
→ tool: analyze_network_connections
→ Look for connection bottlenecks

Step 4: Check for network saturation
→ Look for high connection counts or unusual patterns
```

### 4. Security and Monitoring 🔒
```
Step 1: Audit listening ports
→ tool: analyze_network_connections
→ Verify only expected services are listening

Step 2: Check established connections
→ tool: analyze_network_connections
→ Look for suspicious or unauthorized connections

Step 3: Test external connectivity
→ tool: test_network_connectivity
→ Verify outbound access is working as expected

Step 4: Monitor for anomalies
→ Look for unexpected open ports or connections
```

### 5. DNS and Name Resolution 🔍
```
Step 1: Test DNS connectivity
→ tool: test_port_connectivity
→ ports: [53], host: "8.8.8.8"

Step 2: Test name resolution
→ tool: test_network_connectivity
→ Use domain names instead of IP addresses

Step 3: Compare DNS servers
→ Test connectivity to multiple DNS servers
→ Compare response times and reliability

Step 4: Check DNS configuration
→ Review network interface DNS settings
```

## 🎨 **Network Health Assessment**

### Healthy Network ✅
- 80%+ connectivity success rate
- All critical services accessible
- Normal latency (< 50ms local, < 200ms internet)
- DNS resolution working
- No unexpected listening ports
- Reasonable connection counts

### Fair Network ⚠️
- 60-80% connectivity success rate
- Most critical services accessible
- Elevated latency (50-200ms local, 200-500ms internet)
- Occasional DNS failures
- Some service connectivity issues
- Higher than normal connection counts

### Concerning Network ❌
- < 60% connectivity success rate
- Critical services inaccessible
- High latency (> 200ms local, > 500ms internet)
- Frequent DNS failures
- Multiple port connectivity issues
- Network interface problems
- Suspicious listening ports or connections

## 🛠️ **Common Network Issues**

### Connectivity Problems

#### No Internet Access
**Symptoms**: Cannot reach external hosts
**Investigation**:
1. Test local network connectivity
2. Check DNS resolution
3. Test gateway connectivity
4. Verify network interface status

**Common Causes**:
- ISP connectivity issues
- Router/gateway problems
- DNS server failures
- Firewall blocking traffic
- Network interface down

#### Slow Network Performance
**Symptoms**: High latency, slow transfers
**Investigation**:
1. Measure baseline latency
2. Test bandwidth to various hosts
3. Check for network saturation
4. Analyze connection patterns

**Common Causes**:
- Network congestion
- Bandwidth limitations
- Router performance issues
- QoS policies
- Hardware problems

#### Intermittent Connectivity
**Symptoms**: Sporadic connection failures
**Investigation**:
1. Monitor connectivity over time
2. Look for patterns in failures
3. Check for hardware issues
4. Review network logs

**Common Causes**:
- Unstable network hardware
- Interference (wireless)
- Load balancing issues
- Network configuration problems

### Service Accessibility Issues

#### Service Not Responding
**Symptoms**: Cannot connect to specific ports
**Investigation**:
1. Test port connectivity
2. Check if service is listening
3. Verify firewall rules
4. Test from different locations

**Solutions**:
- Start/restart service
- Check service configuration
- Update firewall rules
- Verify network ACLs

#### Service Running but Not Accessible
**Symptoms**: Service listening but connections fail
**Investigation**:
1. Check service binding (0.0.0.0 vs 127.0.0.1)
2. Test local vs remote connectivity
3. Verify firewall rules
4. Check for proxy/load balancer issues

**Solutions**:
- Update service bind address
- Configure firewall rules
- Check proxy configuration
- Review load balancer settings

### DNS Issues

#### DNS Resolution Failures
**Symptoms**: Cannot resolve domain names
**Investigation**:
1. Test DNS server connectivity
2. Try alternative DNS servers
3. Check DNS configuration
4. Test with direct IP addresses

**Solutions**:
- Change DNS servers
- Flush DNS cache
- Check /etc/resolv.conf (Linux)
- Restart DNS client service

## 📊 **Performance Monitoring**

### Latency Monitoring
```
Acceptable Latency Ranges:
- Local network: < 10ms
- Same city: < 50ms
- Same country: < 100ms
- International: < 300ms
- Satellite: < 600ms
```

### Connection Monitoring
```
Typical Connection Counts:
- Desktop: 50-200 connections
- Server: 200-2000 connections
- High-traffic server: 2000+ connections
```

### Bandwidth Considerations
```
Bandwidth Usage Guidelines:
- Normal operation: < 70% of available bandwidth
- Peak usage: < 90% of available bandwidth
- Sustained high usage may indicate issues
```

## 🔍 **Advanced Diagnostics**

### MTU Discovery
```
Test maximum transmission unit:
- Use ping with different packet sizes
- Start with 1500 bytes and work down
- Find largest packet size that doesn't fragment
```

### Traceroute Analysis
```
Network path analysis:
- Identify network hops to destination
- Find where latency increases
- Detect routing issues or bottlenecks
```

### Protocol-specific Testing
```
HTTP/HTTPS Testing:
- Use curl for detailed HTTP diagnostics
- Test SSL/TLS certificate validity
- Check HTTP response codes and timing

SSH Testing:
- Test SSH connectivity and authentication
- Check for connection timeouts
- Verify SSH service configuration
```

## 📎 **Network Diagnostic Checklist**

### Initial Assessment
- [ ] Test network tools availability
- [ ] Run comprehensive network diagnostics
- [ ] Check basic internet connectivity
- [ ] Verify DNS resolution
- [ ] Test critical service ports

### Detailed Analysis
- [ ] Analyze listening ports and services
- [ ] Check established connections
- [ ] Measure latency to key destinations
- [ ] Test bandwidth and throughput
- [ ] Review network interface configuration

### Security Review
- [ ] Audit open ports and services
- [ ] Check for unauthorized connections
- [ ] Verify firewall rules
- [ ] Monitor for suspicious activity
- [ ] Review access logs

### Performance Optimization
- [ ] Identify network bottlenecks
- [ ] Optimize connection parameters
- [ ] Review QoS settings
- [ ] Monitor resource utilization
- [ ] Plan capacity upgrades

## ⚠️ **Important Notes**

### Tool Dependencies
- Network diagnostic tools may not be available on all systems
- Some tools require administrative privileges
- Platform differences affect tool availability and syntax
- Consider installing missing tools for comprehensive diagnostics

### Security Considerations
- Network scanning may trigger security alerts
- Be cautious when testing external hosts
- Respect rate limits and acceptable use policies
- Document authorized testing activities

### Performance Impact
- Network testing consumes bandwidth
- Frequent testing may impact network performance
- Balance monitoring frequency with resource usage
- Consider off-peak testing for comprehensive analysis

This comprehensive network diagnostics system provides detailed insights into network connectivity, performance, and security for effective network administration and troubleshooting.
"""

    @mcp.prompt()
    async def network_troubleshooting_scenarios() -> str:
        """
        Specific troubleshooting scenarios and solutions for common network issues.

        This prompt provides step-by-step guidance for resolving specific
        network problems and connectivity issues.
        """
        return """
# 🔧 Network Troubleshooting Scenarios and Solutions

## 🚫 **"Cannot Connect to Internet" Scenarios**

### Scenario 1: Complete Internet Outage

#### Symptoms
- No websites load
- Ping to external IPs fails
- DNS resolution fails
- Local network may still work

#### Diagnostic Steps
💡 **Step 1: Test Network Tools**
```
Tool: test_network_tools_availability
→ Verify diagnostic tools are available
```

💡 **Step 2: Test Local Network**
```
Tool: test_network_connectivity
Parameters: hosts=["192.168.1.1", "10.0.0.1"] (common gateway IPs)
→ Check if local network/router is reachable
```

💡 **Step 3: Test DNS**
```
Tool: test_port_connectivity
Parameters: ports=[53], host="8.8.8.8"
→ Check if DNS servers are reachable
```

💡 **Step 4: Test External Connectivity**
```
Tool: test_network_connectivity
Parameters: hosts=["8.8.8.8", "1.1.1.1"]
→ Test connectivity to public DNS servers
```

#### Solutions by Root Cause
- **Router/Gateway Issue**: Restart router, check cables
- **ISP Outage**: Contact ISP, wait for restoration
- **DNS Issues**: Change DNS servers to 8.8.8.8, 1.1.1.1
- **Network Interface**: Check interface status, restart network service

### Scenario 2: Slow Internet Performance

#### Symptoms
- Websites load very slowly
- High latency in ping tests
- Downloads/uploads are slow
- Intermittent timeouts

#### Diagnostic Steps
💡 **Step 1: Measure Baseline Performance**
```
Tool: test_network_connectivity
Parameters: hosts=["8.8.8.8", "google.com", "fast.com"], ping_count=10
→ Measure latency to various destinations
```

💡 **Step 2: Test Port Response Times**
```
Tool: test_port_connectivity
Parameters: ports=[80, 443], host="google.com", timeout=10
→ Measure connection establishment times
```

💡 **Step 3: Check Network Utilization**
```
Tool: analyze_network_connections
Parameters: include_established=true
→ Look for high connection counts or unusual traffic
```

#### Performance Benchmarks
- **Good**: < 50ms latency, < 3s connection time
- **Fair**: 50-200ms latency, 3-10s connection time
- **Poor**: > 200ms latency, > 10s connection time

#### Solutions
- **High Latency**: Check for network congestion, QoS settings
- **Bandwidth Issues**: Contact ISP, upgrade plan
- **Local Congestion**: Limit bandwidth-heavy applications
- **DNS Delays**: Switch to faster DNS servers

## 🔌 **"Service Unreachable" Scenarios**

### Scenario 3: Web Server Not Responding

#### Symptoms
- Specific website/service won't load
- Other internet services work fine
- May get "Connection refused" or timeout errors

#### Diagnostic Steps
💡 **Step 1: Test Service Ports**
```
Tool: test_port_connectivity
Parameters: ports=[80, 443], host="target-server.com"
→ Check if web server ports are accessible
```

💡 **Step 2: Test From Different Networks**
```
Tool: test_network_connectivity
Parameters: hosts=["target-server.com"]
→ See if issue is local or server-side
```

💡 **Step 3: Check DNS Resolution**
```
Tool: diagnose_network_issues
→ Verify DNS is resolving the server name correctly
```

#### Root Cause Analysis
- **Port Closed**: Service not running or firewalled
- **Server Down**: Server hardware or software failure
- **DNS Issues**: Domain not resolving correctly
- **Network Route**: Routing issue between you and server

### Scenario 4: Database Connection Failures

#### Symptoms
- Applications can't connect to database
- Database queries timeout
- "Connection refused" on database port

#### Diagnostic Steps
💡 **Step 1: Test Database Port**
```
Tool: test_port_connectivity
Parameters: ports=[3306, 5432, 1433], host="db-server"
→ Test common database ports (MySQL, PostgreSQL, SQL Server)
```

💡 **Step 2: Check Local Database Services**
```
Tool: analyze_network_connections
Parameters: include_listening=true
→ Verify database is listening on expected ports
```

💡 **Step 3: Test Network Path**
```
Tool: test_network_connectivity
Parameters: hosts=["db-server"]
→ Ensure basic connectivity to database server
```

#### Solutions
- **Service Down**: Start database service
- **Firewall**: Configure firewall rules for database port
- **Binding**: Ensure database listens on correct interface
- **Authentication**: Check database user permissions

## 🔒 **Security-Related Network Issues**

### Scenario 5: Suspicious Network Activity

#### Symptoms
- Unexpected outbound connections
- Unknown listening ports
- High network traffic
- Security alerts

#### Investigation Steps
💡 **Step 1: Audit Listening Ports**
```
Tool: analyze_network_connections
Parameters: include_listening=true
→ Identify all services listening for connections
```

💡 **Step 2: Check Established Connections**
```
Tool: analyze_network_connections
Parameters: include_established=true
→ Look for suspicious outbound connections
```

💡 **Step 3: Test Known-Good Services**
```
Tool: test_port_connectivity
Parameters: ports=[22, 80, 443] (known services)
→ Verify legitimate services are still accessible
```

#### Red Flags
- Listening ports you don't recognize
- Connections to suspicious IP addresses
- High-numbered ports with active connections
- Processes you can't identify

#### Response Actions
- **Document**: Record suspicious connections and ports
- **Investigate**: Research unknown processes and connections
- **Block**: Use firewall to block suspicious traffic
- **Monitor**: Increase network monitoring frequency
- **Escalate**: Contact security team if malware suspected

### Scenario 6: Firewall Blocking Legitimate Traffic

#### Symptoms
- Specific services work locally but not remotely
- "Connection refused" errors from external clients
- Services show as listening but aren't accessible

#### Diagnostic Steps
💡 **Step 1: Test Local Access**
```
Tool: test_port_connectivity
Parameters: ports=[service-port], host="localhost"
→ Verify service works locally
```

💡 **Step 2: Test Remote Access**
```
Tool: test_port_connectivity
Parameters: ports=[service-port], host="server-external-ip"
→ Test from external perspective
```

💡 **Step 3: Check Service Binding**
```
Tool: analyze_network_connections
Parameters: include_listening=true
→ Verify service is listening on all interfaces (0.0.0.0)
```

#### Solutions
- **Firewall Rules**: Add rules to allow traffic on required ports
- **Service Binding**: Configure service to listen on all interfaces
- **Network ACLs**: Check router/switch access control lists
- **Cloud Security Groups**: Update cloud firewall rules

## 📊 **Performance Troubleshooting**

### Scenario 7: High Network Latency

#### Symptoms
- Web pages load slowly
- Remote desktop is laggy
- Video calls have poor quality
- File transfers are slow

#### Analysis Steps
💡 **Step 1: Measure Latency Patterns**
```
Tool: test_network_connectivity
Parameters: hosts=["local-router", "ISP-gateway", "remote-server"], ping_count=20
→ Identify where latency is introduced
```

💡 **Step 2: Test Multiple Destinations**
```
Tool: test_network_connectivity
Parameters: hosts=["8.8.8.8", "1.1.1.1", "fast.com", "github.com"]
→ Determine if latency is destination-specific
```

💡 **Step 3: Check Network Utilization**
```
Tool: analyze_network_connections
→ Look for high connection counts that might indicate congestion
```

#### Latency Troubleshooting
- **Local Network**: Check for wireless interference, cable issues
- **ISP Issues**: Contact ISP, check for network congestion
- **Routing Problems**: Use traceroute to identify problem hops
- **QoS Settings**: Adjust quality of service priorities

### Scenario 8: Intermittent Connection Drops

#### Symptoms
- Connections work sometimes, fail other times
- Services become unreachable periodically
- Network tests show inconsistent results

#### Monitoring Approach
💡 **Step 1: Continuous Monitoring**
```
Tool: test_network_connectivity
→ Run repeatedly over time to identify patterns
```

💡 **Step 2: Service-Specific Testing**
```
Tool: test_port_connectivity
→ Test specific services during outage periods
```

💡 **Step 3: Pattern Analysis**
```
Look for patterns:
- Time-based (certain hours, days)
- Load-based (during high usage)
- Service-specific (only certain applications)
```

#### Common Causes
- **Network Hardware**: Failing switches, routers, cables
- **ISP Issues**: Periodic maintenance, overloaded infrastructure
- **Load Balancing**: Misconfigured load balancer health checks
- **DHCP Issues**: IP address lease renewals causing disruption

## 🛠️ **Emergency Network Diagnostics**

### Quick Triage Protocol

#### Phase 1: Immediate Assessment (< 5 minutes)
```
1. Tool: diagnose_network_issues
   → Get overall network health status

2. Tool: test_network_connectivity
   Parameters: hosts=["8.8.8.8", "google.com"]
   → Test basic internet connectivity

3. Decision: Is this a local or widespread issue?
```

#### Phase 2: Targeted Testing (5-15 minutes)
```
If Local Issue:
1. Tool: analyze_network_connections
   → Check for service disruptions

2. Tool: test_port_connectivity
   → Test critical service ports

If Widespread Issue:
1. Tool: test_network_connectivity
   Parameters: hosts=["ISP-gateway", "local-router"]
   → Isolate problem location
```

#### Phase 3: Root Cause Analysis (15+ minutes)
```
1. Detailed service testing
2. Historical pattern analysis
3. External service status checks
4. Hardware diagnostics
```

### Emergency Response Checklist

#### Critical Service Outage
- [ ] Identify affected services
- [ ] Test service ports and connectivity
- [ ] Check service status and logs
- [ ] Verify network path to services
- [ ] Implement temporary workarounds
- [ ] Document timeline and actions

#### Network Performance Crisis
- [ ] Measure current performance baselines
- [ ] Identify performance bottlenecks
- [ ] Check for network congestion
- [ ] Review recent network changes
- [ ] Implement traffic prioritization
- [ ] Monitor improvement

## ⚠️ **Best Practices for Network Troubleshooting**

### Documentation
- Keep baseline network performance metrics
- Document network topology and critical services
- Maintain inventory of network diagnostic tools
- Record historical issues and resolutions

### Monitoring Strategy
- Implement continuous monitoring for critical services
- Set up alerts for connectivity failures
- Monitor network performance trends
- Regular security audits of network connections

### Tool Management
- Ensure network diagnostic tools are available
- Test diagnostic procedures regularly
- Keep tools updated and functional
- Train team members on diagnostic workflows

**Remember**: Network issues often have multiple contributing factors. Start with broad diagnostics to identify the scope, then narrow down to specific components. Always document findings and maintain baseline measurements for comparison.
"""
