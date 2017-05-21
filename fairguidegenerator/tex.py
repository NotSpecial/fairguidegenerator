# -*- coding: utf-8 -*-

r"""Create the xelatex files.

The jinja environment and filters are based on a [flask snippet]
(http://flask.pocoo.org/snippets/55/) by Clemens Kaposi.

Some adjustments were made:
* Environment made independent from flask
* New filter to convert '\n' to '\\'

The render_tex function takes care of filename and directory things.
It plugs everything into the template and can return either the .tex file or
start latex and return the .pdf (also removes all non .pdf files)
"""
import subprocess
from os import path
import re
from tempfile import TemporaryDirectory
from jinja2 import Environment, PackageLoader, StrictUndefined


class Error(Exception):
    """Custom Error."""


# Create the jinja env
env = Environment(
    loader=PackageLoader('fairguidegenerator', 'tex_templates'),
    block_start_string='((*',
    block_end_string='*))',
    variable_start_string='(((',
    variable_end_string=')))',
    comment_start_string='((=',
    comment_end_string='=))',
    undefined=StrictUndefined,
    trim_blocks=True,
)


# Add additional filters
def escape_tex(value):
    """Regex for most tex relevant things."""
    if not isinstance(value, str):
        return value
    subs = (
        (re.compile(r'\\'), r'\\textbackslash'),
        (re.compile(r'([{}_#%&$])'), r'\\\1'),
        (re.compile(r'~'), r'\~{}'),
        (re.compile(r'\^'), r'\^{}'),
        (re.compile(r'"'), r"''"),
        (re.compile(r'\.\.\.+'), r'\\ldots'),
    )
    for pattern, replacement in subs:
        value = pattern.sub(replacement, value)

    # Replace newlines
    value = value.replace('\n', r'\\')

    return value


env.filters.update({
    # Escaping for tex, short name because used often
    't': escape_tex,
})


def render_tex(companies):
    """Render the template and return the filename.

    Returns:
        str: filename (including path) to output
    """
    # Render the template
    template = env.get_template("company_page.tex")
    rendered = template.render(companies=companies)

    with TemporaryDirectory() as tempdir:
        # Safe .tex file
        texfile = path.join(tempdir, 'temp.tex')

        with open(texfile, 'wb') as file:
            file.write(rendered.encode('utf-8'))

        # Run XeLaTeX
        commands = ["xelatex",
                    "-output-directory", tempdir,
                    "-interaction=batchmode", texfile]

        try:
            subprocess.check_output(commands)
        except FileNotFoundError:
            # The command was not recognized
            raise Error("The command '%s' failed. Is everything installed?"
                        % commands[0])
        except subprocess.CalledProcessError as e:
            # Try to return tex log in error message
            try:
                with open(path.join(tempdir, 'temp.log'), 'rb') as file:
                    log = file.read().decode('utf-8')
                raise Error("Something went wrong during compilation!\n"
                            "Here is the log content:\n\n %s" % log)
            except FileNotFoundError:
                # No log! Show output of command instead
                raise Error(e.output.decode('utf-8'))

        # Return content of pdf so all files can be removed
        with open(path.join(tempdir, 'temp.pdf'), 'rb') as file:
            return file.read()
