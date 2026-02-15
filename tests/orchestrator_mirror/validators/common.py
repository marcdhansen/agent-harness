import re
import subprocess


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def check_mark(passed: bool) -> str:
    """Return colored check or X mark."""
    if passed:
        return f"{Colors.GREEN}✅{Colors.END}"
    return f"{Colors.RED}❌{Colors.END}"


def warning_mark() -> str:
    """Return warning symbol."""
    return f"{Colors.YELLOW}⚠️{Colors.END}"


def check_tool_available(tool: str) -> bool:
    """Check if a command-line tool is available."""
    try:
        result = subprocess.run(
            ["which", tool],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return result.returncode == 0
    except Exception:
        return False


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse version string into a tuple of integers."""
    match = re.search(r"(\d+(?:\.\d+)+)", version_str)
    if match:
        return tuple(map(int, match.group(1).split(".")))
    return ()


def check_tool_version(
    tool: str, min_version: str, version_flag: str = "--version"
) -> tuple[bool, str]:
    """Check if a tool's version meets the minimum requirement."""
    if not check_tool_available(tool):
        return False, f"Tool '{tool}' not installed"

    try:
        result = subprocess.run([tool, version_flag], capture_output=True, text=True, timeout=5)
        if result.returncode != 0:
            output = result.stdout.strip() or result.stderr.strip()
            if not output:
                return False, f"Could not get version for '{tool}'"
        else:
            output = result.stdout.strip() or result.stderr.strip()

        current_v = parse_version(output)
        required_v = parse_version(min_version)

        if not current_v:
            return False, f"Could not parse version from: {output}"

        if current_v < required_v:
            return (
                False,
                f"Version for '{tool}' is too old: {output} (Required: {min_version})",
            )

        return True, f"{tool} version {'.'.join(map(str, current_v))} is OK"
    except Exception as e:
        return False, f"Error checking {tool} version: {e}"
