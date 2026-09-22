---
classification: internal
project: proj-lessons
doc_type: lesson
---

# An Unpinned mcp Package Install Breaks the Course MCP Server

What happened: registering the course-provided `coursetools_server.py` MCP server failed with the unhelpful message `MCP error -32000: Connection closed`. No further detail was visible through `claude mcp add` itself.

What was learned: `pip install mcp` with no version constraint installs the latest release, currently 2.x, in which `mcp.server.fastmcp.FastMCP` was renamed to `mcp.server.mcpserver.MCPServer`. The course script still imports the old v1 path, so the server process crashes immediately on startup with a `ModuleNotFoundError` -- but that real error is invisible through the MCP registration flow, which only ever surfaces the generic `-32000: Connection closed` regardless of the actual underlying cause.

How to apply it: pin `mcp<2` explicitly wherever this project installs it. If a similar opaque `-32000` connection error shows up again for a different MCP server, don't trust the generic message -- run the server script directly (`python3 path/to/server.py`) to see the real Python traceback before assuming the cause.
