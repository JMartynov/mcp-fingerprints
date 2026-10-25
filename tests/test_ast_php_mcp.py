import pytest
from mcp_fingerprints.ast_parser import parse_php_mcp_code, parse_mcp_source_code

def test_php_attribute_tools():
    code = """
    <?php
    class MyTools {
        #[McpTool(name: 'weather_tool', description: 'Get weather')]
        public function weather(string $city, ?int $days = 3) {}

        #[Tool('echo')]
        public function echoTool(string $message) {}
    }
    """
    tools = parse_php_mcp_code(code)
    assert len(tools) == 2
    
    t1 = next(t for t in tools if t['name'] == 'weather_tool')
    assert t1['description'] == 'Get weather'
    assert 'city' in t1['inputSchema']['properties']
    assert t1['inputSchema']['properties']['city']['type'] == 'string'
    assert 'days' in t1['inputSchema']['properties']
    assert t1['inputSchema']['properties']['days']['type'] == 'integer'
    assert 'city' in t1['inputSchema']['required']
    assert 'days' not in t1['inputSchema']['required']

    t2 = next(t for t in tools if t['name'] == 'echo')
    assert t2['description'] == 'echo'
    assert 'message' in t2['inputSchema']['properties']
    assert 'message' in t2['inputSchema']['required']

def test_php_class_based_tools():
    code = r"""
    <?php
    namespace App\Tools;

    class WeatherTool extends Tool {
        /**
         * Get the weather for a city.
         */
        protected string $name = "weather";
        protected string $description = "Get the current weather";
    }

    class CalculatorTool implements McpToolInterface {
        public function getName(): string { return 'calculator'; }
        
        /**
         * Performs math operations
         */
    }
    """
    tools = parse_php_mcp_code(code)
    assert len(tools) == 2

    t1 = next(t for t in tools if t['name'] == 'weather')
    assert t1['description'] == 'Get the current weather'
    assert t1['inputSchema']['properties'] == {}

    t2 = next(t for t in tools if t['name'] == 'calculator')
    assert t2['description'] == 'Performs math operations'

def test_php_server_register_tool():
    code = """
    <?php
    $server->registerTool("echo_server");
    $mcp->registerTool("hello");
    """
    tools = parse_php_mcp_code(code)
    assert len(tools) == 2
    assert tools[0]['name'] == 'echo_server'
    assert tools[1]['name'] == 'hello'

def test_parse_mcp_source_code_routing():
    code = """
    <?php
    #[McpTool('router')]
    function route() {}
    """
    tools = parse_mcp_source_code(code)
    assert len(tools) == 1
    assert tools[0]['name'] == 'router'

    tools2 = parse_mcp_source_code(code, language='php')
    assert len(tools2) == 1
    assert tools2[0]['name'] == 'router'
