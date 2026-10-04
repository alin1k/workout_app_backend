"""Operator commands, run with `flask --app app <command>`."""

import click
from flask import Flask

from app.services import admin_service
from app.services.errors import ServiceError


def register_cli(app: Flask) -> None:
    # Bootstrap only. Accounts are normally created by an admin from the app,
    # which needs an admin to exist first — and the app itself can only mint
    # normal users. This is how the first one (or any further one) gets in.
    @app.cli.command("create-admin")
    @click.argument("username")
    @click.password_option(help="Prompted for (twice) when omitted.")
    def create_admin(username: str, password: str) -> None:
        """Create an administrator account."""
        try:
            user = admin_service.create_user(
                {"username": username, "password": password},
                is_admin=True,
                created_by="cli",
            )
        except ServiceError as err:
            raise click.ClickException(str(err))
        click.echo(f"Created admin {user['username']!r} (id={user['id']})")
