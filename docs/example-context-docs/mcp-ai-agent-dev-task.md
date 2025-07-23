# MCP AI Agent Development Task

## Project Overview
Build a command-line AI agent in Python that connects to and utilizes an MCP (Model Context Protocol) server running on the local network. The agent should provide an interactive CLI interface for users to communicate with the AI while leveraging MCP server capabilities.

## Project Structure
```
mcp-ai-agent/
├── src/
│   ├── __init__.py
│   ├── mcp_client.py      # MCP server connection handling
│   ├── ai_agent.py        # AI agent logic and processing
│   ├── cli.py             # Command-line interface
│   └── config.py          # Configuration management
├── tests/
│   ├── __init__.py
│   ├── test_mcp_client.py
│   ├── test_ai_agent.py
│   └── test_cli.py
├── .env.example
├── requirements.txt
├── setup.py
├── README.md
└── main.py                # Entry point
```

## Development Prompts for Claude Code

### Phase 1: Project Setup and Core Structure

**Prompt 1.1 - Initialize Project**
```
Create a new Python project directory called 'mcp-ai-agent' with the following:
1. Create the directory structure as shown above
2. Initialize a virtual environment
3. Create a requirements.txt with these dependencies:
   - python-dotenv>=1.0.0
   - httpx>=0.24.0
   - websockets>=11.0
   - pydantic>=2.0.0
   - click>=8.1.0
   - rich>=13.0.0
   - pytest>=7.0.0
   - pytest-asyncio>=0.21.0
   - pytest-mock>=3.10.0
4. Create a .env.example file with placeholders for MCP server configuration
5. Create a setup.py for package installation
6. Initialize git repository with appropriate .gitignore
```

**Prompt 1.2 - Configuration Module**
```
Create src/config.py that:
1. Uses pydantic BaseSettings for configuration management
2. Loads environment variables from .env file
3. Includes these configuration fields:
   - MCP_SERVER_URL (with validation for URL format)
   - MCP_SERVER_PORT (integer between 1-65535)
   - MCP_API_KEY (optional, for authenticated servers)
   - AI_MODEL (default to a standard model)
   - LOG_LEVEL (default to INFO)
   - CONNECTION_TIMEOUT (default to 30 seconds)
   - RETRY_ATTEMPTS (default to 3)
4. Implements validation and provides clear error messages
5. Include docstrings explaining each configuration option
```

### Phase 2: MCP Client Implementation

**Prompt 2.1 - MCP Client Base**
```
Create src/mcp_client.py with:
1. An async MCPClient class that handles connection to the MCP server
2. Methods for:
   - connect(): Establish connection (support both HTTP and WebSocket)
   - disconnect(): Clean shutdown
   - send_request(): Send requests to MCP server
   - receive_response(): Handle responses
   - ping(): Health check functionality
3. Implement connection retry logic with exponential backoff
4. Add proper error handling for network issues
5. Include logging for debugging
6. Support both synchronous and asynchronous operation modes
```

**Prompt 2.2 - MCP Protocol Handling**
```
Extend src/mcp_client.py to:
1. Implement the MCP protocol specification:
   - Message formatting (JSON-RPC 2.0 if applicable)
   - Request/response correlation
   - Error response handling
2. Add methods for common MCP operations:
   - list_tools(): Get available tools from server
   - execute_tool(): Execute a specific tool
   - get_context(): Retrieve context information
3. Implement message queuing for concurrent requests
4. Add request/response validation using pydantic models
```

### Phase 3: AI Agent Core

**Prompt 3.1 - AI Agent Implementation**
```
Create src/ai_agent.py with:
1. An AIAgent class that:
   - Initializes with an MCP client instance
   - Maintains conversation context
   - Processes user inputs and generates responses
2. Implement these methods:
   - process_message(): Main message handling
   - use_mcp_tool(): Decide when to use MCP tools
   - format_response(): Format AI responses for CLI
3. Add conversation memory management
4. Implement tool selection logic based on user queries
5. Include error recovery for failed MCP operations
```

**Prompt 3.2 - AI Integration**
```
Enhance src/ai_agent.py to:
1. Integrate with an AI model (use OpenAI API or similar as placeholder)
2. Implement prompt engineering for:
   - System prompts that explain available MCP tools
   - User message formatting
   - Tool usage instructions
3. Add response streaming support
4. Implement token counting and management
5. Add safety checks and content filtering
```

### Phase 4: CLI Interface

**Prompt 4.1 - CLI Implementation**
```
Create src/cli.py using Click framework:
1. Main command group with these subcommands:
   - start: Start interactive chat session
   - list-tools: Show available MCP tools
   - config: Display current configuration
   - test-connection: Test MCP server connectivity
2. For the interactive chat:
   - Use Rich for colorful output
   - Show typing indicators during processing
   - Support multi-line input (Ctrl+Enter)
   - Add command history
   - Include /help, /clear, /exit commands
3. Add progress bars for long operations
4. Implement graceful shutdown on Ctrl+C
```

**Prompt 4.2 - Enhanced CLI Features**
```
Extend src/cli.py with:
1. Session management:
   - Save/load conversation history
   - Export conversations to markdown
2. Advanced commands:
   - /tools: List and describe available tools
   - /use <tool>: Explicitly use a specific tool
   - /context: Show current context
   - /stats: Display session statistics
3. Add syntax highlighting for code blocks
4. Implement auto-completion for commands
5. Add configuration override options via CLI flags
```

### Phase 5: Testing Suite

**Prompt 5.1 - Unit Tests**
```
Create comprehensive unit tests:
1. tests/test_mcp_client.py:
   - Test connection establishment
   - Mock server responses
   - Test retry logic
   - Verify error handling
2. tests/test_ai_agent.py:
   - Test message processing
   - Mock MCP tool usage
   - Verify context management
3. tests/test_cli.py:
   - Test command parsing
   - Verify output formatting
   - Test interactive mode
4. Use pytest fixtures for common test setup
5. Aim for >80% code coverage
```

**Prompt 5.2 - Integration Tests**
```
Create tests/test_integration.py with:
1. End-to-end tests using a mock MCP server
2. Test full conversation flows
3. Verify tool execution chains
4. Test error recovery scenarios
5. Performance tests for concurrent operations
6. Create docker-compose.yml for test environment
```

### Phase 6: Main Entry Point and Documentation

**Prompt 6.1 - Main Application**
```
Create main.py that:
1. Serves as the application entry point
2. Handles initialization of all components
3. Implements proper async context management
4. Adds global exception handling
5. Includes signal handlers for graceful shutdown
6. Provides --debug flag for verbose logging
```

**Prompt 6.2 - Documentation**
```
Create comprehensive documentation:
1. README.md with:
   - Project description and features
   - Installation instructions
   - Quick start guide
   - Configuration options
   - Usage examples
   - Troubleshooting section
2. Add inline code documentation following Google style
3. Create docs/ directory with:
   - Architecture overview
   - MCP protocol details
   - API reference
   - Contributing guidelines
```

### Phase 7: Advanced Features

**Prompt 7.1 - Plugin System**
```
Implement a plugin system:
1. Create src/plugins/ directory structure
2. Define plugin interface for extending functionality
3. Add plugin loader in main application
4. Create example plugins:
   - Custom output formatters
   - Additional CLI commands
   - Response processors
5. Document plugin development
```

**Prompt 7.2 - Performance and Monitoring**
```
Add performance monitoring:
1. Implement metrics collection:
   - Response times
   - Token usage
   - Error rates
   - MCP server latency
2. Add optional Prometheus metrics endpoint
3. Create performance profiling mode
4. Add request/response logging with rotation
5. Implement caching for frequently used MCP tools
```

## Testing Instructions

### Manual Testing Checklist
1. **Connection Testing**
   - Test with valid MCP server
   - Test with invalid server URL
   - Test connection timeout
   - Test authentication (if applicable)

2. **Functionality Testing**
   - Send various user queries
   - Test all CLI commands
   - Verify tool execution
   - Test error scenarios

3. **Performance Testing**
   - Test with concurrent requests
   - Measure response times
   - Check memory usage
   - Test with long conversations

### Automated Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_mcp_client.py

# Run integration tests
pytest tests/test_integration.py -v
```

## Deployment Considerations

1. **Security**
   - Never commit .env files
   - Use secure communication with MCP server
   - Implement rate limiting
   - Add input sanitization

2. **Scalability**
   - Design for horizontal scaling
   - Implement connection pooling
   - Add request queuing
   - Consider caching strategies

3. **Monitoring**
   - Set up logging aggregation
   - Implement health checks
   - Add alerting for failures
   - Monitor resource usage

## Example Usage

```bash
# Install the package
pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your MCP server details

# Test connection
mcp-agent test-connection

# Start interactive session
mcp-agent start

# List available tools
mcp-agent list-tools

# Start with debug logging
mcp-agent --debug start
```

## Additional Notes

- Ensure all async operations use proper context managers
- Implement graceful degradation when MCP server is unavailable
- Add comprehensive error messages for better user experience
- Consider implementing a web UI as a future enhancement
- Keep dependencies minimal and well-maintained
- Follow semantic versioning for releases