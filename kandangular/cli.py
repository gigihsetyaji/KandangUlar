import argparse
import os
import secrets
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(prog="kandangular")
    parser.add_argument("command", choices=["secret", "serve", "manage", "dashboard"])
    args, remainder = parser.parse_known_args()
    if args.command == "secret":
        print(secrets.token_urlsafe(64))
    elif args.command == "serve":
        import uvicorn
        uvicorn.run("kandangular.asgi:application", host="127.0.0.1", port=8000, proxy_headers=False)
    elif args.command == "manage":
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kandangular.settings")
        from django.core.management import execute_from_command_line
        execute_from_command_line(["kandangular", *remainder])
    else:
        from streamlit.web import cli
        sys.argv = ["streamlit", "run", str(Path(__file__).with_name("dashboard.py")), "--server.address=127.0.0.1", "--server.enableXsrfProtection=true", "--server.enableCORS=true", *remainder]
        cli.main()
