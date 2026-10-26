import re

with open("src/mcp_fingerprints/ast_parser.py", "r") as f:
    content = f.read()

# I see the problem. `seen_names` is being populated by `constants` logic? No, the parse_golang_mcp_code in ast_parser is returning BOTH the old logic's results (partially?) and the new.
# Ah, I replaced a block, but maybe not the right one.
