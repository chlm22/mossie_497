"""Mossie application launcher."""

import os
import sys
import click
from flask.cli import with_appcontext
from temp import app, models

# Initialize the database with the app
models.init_app(app)

# Add CLI commands
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Initialize the database tables."""
    models.init_db()
    click.echo('Initialized the database.')


@click.command('init-db-schema')
@click.argument('schema_path', type=click.Path(exists=True))
@with_appcontext
def init_db_schema_command(schema_path):
    """Initialize the database from schema file."""
    models.init_db_from_schema(schema_path)
    click.echo(f'Initialized the database from schema: {schema_path}')


@click.command('create-user')
@click.argument('username')
@click.argument('password')
@with_appcontext
def create_user_command(username, password):
    """Create a new user."""
    if models.create_user(username, password):
        click.echo(f'User {username} created successfully.')
    else:
        click.echo(f'User {username} already exists.')


# Register CLI commands with the app
app.cli.add_command(init_db_command)
app.cli.add_command(init_db_schema_command)
app.cli.add_command(create_user_command)


if __name__ == '__main__':
    # Check if a command was passed
    if len(sys.argv) > 1:
        # Use Flask CLI
        os.environ['FLASK_APP'] = 'temp.app'
        os.system(' '.join(['flask'] + sys.argv[1:]))
    else:
        # Run the app in debug mode
        app.run(debug=True)
