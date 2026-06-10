#!/usr/bin/env python3
"""
Trace Clearance Utility for CL Chat
Clears local traces, memory, and terminal history.
"""

import os
import sys
import gc


def clear_memory():
    """Force garbage collection to free memory."""
    gc.collect()
    print("Memory cleared")


def clear_terminal():
    """Clear terminal screen and scrollback buffer."""
    if os.name == 'nt':
        os.system('cls')
    else:
        print('\033[3J\033[H\033[2J', end='')
    print("Terminal cleared")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="CL Chat - Trace Clearance")
    parser.add_argument("--local-only", action="store_true", help="Only clear memory (skip terminal)")
    args = parser.parse_args()

    if args.local_only:
        clear_memory()
    else:
        clear_memory()
        clear_terminal()


if __name__ == "__main__":
    main()
