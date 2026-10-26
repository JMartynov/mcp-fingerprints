from mcp_fingerprints.go_sdk_parser import parse_official_go_tools

code = """
        package main
        func main() {
            server.AddTool(&mcp.Tool{
                Name: "example_tool",
                Description: "A control tool",
            }, handler)
        }
        """

print(parse_official_go_tools(code))
