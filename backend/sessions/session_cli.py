import argparse
import sys

from session_manager import (
    PLATFORMS,
    delete_session,
    is_session_saved,
    load_session,
    save_session,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage saved browser sessions for supported job platforms."
    )
    parser.add_argument(
        "command",
        choices=["save", "load", "check", "delete", "list"],
        help="Action to run.",
    )
    parser.add_argument(
        "platform",
        nargs="?",
        choices=sorted(PLATFORMS.keys()),
        help="Platform to target.",
    )
    return parser


def require_platform(parser: argparse.ArgumentParser, platform: str | None) -> str:
    if platform is None:
        parser.error("the following argument is required for this command: platform")
    return platform


def handle_load(platform: str) -> int:
    result = load_session(platform)
    if not result or result[0] is None:
        return 1

    p, browser, context = result
    page = context.new_page()
    destination = PLATFORMS[platform]

    if platform == "linkedin":
        destination = "https://www.linkedin.com/feed"

    page.goto(destination, wait_until="domcontentloaded")
    input("Press ENTER to close browser...")
    browser.close()
    p.stop()
    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "list":
        print("Supported platforms:")
        for platform in sorted(PLATFORMS.keys()):
            print(f"- {platform}")
        return 0

    platform = require_platform(parser, args.platform)

    if args.command == "save":
        save_session(platform)
        return 0

    if args.command == "load":
        return handle_load(platform)

    if args.command == "check":
        if is_session_saved(platform):
            print(f"✅ Saved session found for {platform.capitalize()}.")
            return 0

        print(f"⚠️  No saved session found for {platform.capitalize()}.")
        return 1

    if args.command == "delete":
        delete_session(platform)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
