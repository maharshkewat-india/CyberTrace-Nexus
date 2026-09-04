"""
create_admin.py - CLI helper to create the first administrator account.

Usage:
    python -m backend.scripts.create_admin --username admin --password MySecurePass123

The password must be at least 8 characters. The script will refuse to run
if a user already exists in the database.

Security notes:
- The password is never logged or echoed.
- This script should be run ONCE during initial deployment, not on every start.
- After creating the admin, the script can be removed from the deployment.
"""

import argparse
import getpass
import sys
from pathlib import Path

# Ensure the project root is on sys.path so imports work when run as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.auth.authentication import register_user
from app.auth.authorization import DEFAULT_ROLE_PERMISSIONS
from app.database.database import is_fresh_database, initialize_database


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create the initial administrator account for CyberTrace Nexus."
    )
    parser.add_argument(
        "--username",
        help="Administrator username (prompted interactively if omitted).",
    )
    parser.add_argument(
        "--password",
        help="Administrator password (prompted interactively if omitted).",
    )
    parser.add_argument(
        "--role",
        default="ADMINISTRATOR",
        choices=list(DEFAULT_ROLE_PERMISSIONS.keys()),
        help="Role to assign (default: ADMINISTRATOR).",
    )
    args = parser.parse_args()

    username = args.username or input("Username: ").strip()
    if not username:
        print("ERROR: Username cannot be empty.", file=sys.stderr)
        sys.exit(1)

    if args.password:
        password = args.password
    else:
        password = getpass.getpass("Password: ")

    if not password:
        print("ERROR: Password cannot be empty.", file=sys.stderr)
        sys.exit(1)

    # Initialize database schema if needed
    initialize_database()

    # Refuse to overwrite an existing user
    if not is_fresh_database():
        print(
            "ERROR: A user already exists in the database. "
            "This script is intended for initial setup only.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        user_data = register_user(username, password, args.role)
    except (ValueError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Administrator account created successfully.")
    print(f"  Username: {user_data['username']}")
    print(f"  Role:     {user_data['role_name']}")
    print(f"  User ID:  {user_data['id']}")
    print("You can now start the backend and log in with these credentials.")


if __name__ == "__main__":
    main()