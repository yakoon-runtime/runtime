import asyncio
import getpass


async def safe_input(ps1: str = "$ ", prefix: str = "") -> str:
    """
    Asynchronously reads user input from stdin without creating extra closures or tasks.

    This function avoids memory growth issues associated with standard ainput()
    by offloading input() to a thread executor.

    Args:
        prompt (str): Optional prompt to display.

    Returns:
        str: The entered user input.
    """
    print(prefix + ps1, end="", flush=True)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, input)


async def safe_input_secret(ps1: str = "$ ", prefix: str = "") -> str:
    """
    Reads a secret from stdin without echoing (terminal-dependent).
    Uses getpass in a thread executor to avoid blocking the event loop.
    """
    print(prefix + ps1, end="", flush=True)
    loop = asyncio.get_running_loop()
    # getpass reads from the terminal and disables echo.
    return await loop.run_in_executor(None, getpass.getpass, "")
