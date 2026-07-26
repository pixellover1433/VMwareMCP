# Writing Tool Descriptions

Treat your tool description as a targeted prompt. It is the most critical factor in whether the agent selects the right tool and uses it correctly.

- Specify the "When" and "How": Don't just state what the tool does. Explicitly state when to use it ("Use this when the user asks for a sales report") and how to use it ("Always start with a broad date range").

- Declare limitations explicitly: If a calculator tool only handles up to two decimal places, or a search tool requires at least two words, put that in the description so the agent doesn't hallucinate capabilities.

- Provide examples for complex inputs: If a tool requires a specific formatting (like a nested JSON object or a specific date format), provide 1-5 realistic examples of a correct input schema payload.

# Responses & Error Handling

When a tool finishes executing, the payload it returns dictates whether the agent can successfully continue its workflow.

- Return high-signal, low-noise data: Do not dump a raw 50-field database row into the tool response. Return only the 5 or 6 fields the agent actually needs to reason about its next step. If the user wants full details, offer a separate getDetailedView tool.

- Make error messages actionable: When a tool call fails, do not just return Error 400 or No results. Tell the model exactly how to fix its mistake. For example: Search failed. The 'query' parameter must contain at least two words. Try again with a broader search term.

- Use server-side logging, safely: For STDIO-based MCP servers (like a local Python script running over standard input/output), never log to stdout (e.g., standard print() in Python or console.log() in JS). This corrupts the JSON-RPC messages and breaks the server. Always log errors to stderr.


# Data format regulations

- Always define "models" to handle JSON data; avoid crude, manual processing using string slicing or similar methods except when absolutely necessary.