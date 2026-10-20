import re
from typing import Any

def extract_docker_stdio_args(command_str: str) -> tuple[str | None, list[str]]:
    """Parse a docker run command to extract the image name and stdio args.
    
    Example: `docker run -i --rm -e MY_VAR=1 my-mcp-server arg1 arg2`
    Returns: ('my-mcp-server', ['arg1', 'arg2'])
    """
    if not command_str.startswith("docker run"):
        return None, []
        
    # Split the command string considering quotes
    import shlex
    try:
        parts = shlex.split(command_str)
    except ValueError:
        return None, []

    if len(parts) < 3 or parts[0] != "docker" or parts[1] != "run":
        return None, []
        
    # Find the image name. The image name is the first non-flag argument after `docker run`
    # unless it's the value of a flag (like -e VAR=val)
    image_name = None
    args_start_idx = -1
    
    skip_next = False
    for i in range(2, len(parts)):
        if skip_next:
            skip_next = False
            continue
            
        part = parts[i]
        if part.startswith("-"):
            # If the flag requires an argument, skip the next part
            if part in ("-v", "--volume", "-p", "--publish", "-e", "--env", "-w", "--workdir", "-u", "--user", "-n", "--name"):
                skip_next = True
            continue
            
        # First non-flag is the image
        image_name = part
        args_start_idx = i + 1
        break
        
    if not image_name:
        return None, []
        
    args = parts[args_start_idx:] if args_start_idx < len(parts) else []
    return image_name, args
