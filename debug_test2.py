from mcp_fingerprints.go_sdk_parser import parse_official_go_tools

code = """
        package main
        const (
            ToolName1 = "first_tool"
            ToolName2 = "second_tool"
            Desc1 = "First description"
        )
        func main() {
            t1 := mcp.Tool{
                Name: ToolName1,
                Description: Desc1,
            }
            t2 := mcp.Tool{
                Name: ToolName2,
            }
            server.AddTool(&t1, h)
            server.AddTool(&t2, h)
        }
        """

print(parse_official_go_tools(code))
