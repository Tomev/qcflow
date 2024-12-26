import click

from qcflow.server.auth.db import cli as db_cli


@click.group()
def commands():
    pass


commands.add_command(db_cli.commands)
