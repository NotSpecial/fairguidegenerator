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
import contextlib
import os
import re
from jinja2 import Environment, PackageLoader, StrictUndefined

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

def render_tex(companies, output_dir):
    """Render the template and return the filename.

    Returns:
        str: filename (including path) to output
    """
    # Render the template
    template = env.get_template("company_page.tex")
    rendered = template.render(companies=companies)

    # Create filenames and directory (if needed)
    # Tex is stupid with spaces in filename, replace them
    if len(list(companies)) == 1:
        name = companies[0]['name'].replace(' ', '_')
    else:
        name = 'all'

    filename = os.path.join(output_dir, name)
    texname = filename + '.tex'

    os.makedirs(output_dir, exist_ok=True)

    with open(texname, 'wb') as file:
        file.write(rendered.encode('utf-8'))

    commands = ["xelatex",
                "-output-directory", output_dir,
                "-interaction=batchmode", texname]

    # Capture output with PIPE (just to keep console clean)
    # Check true requires status code 0
    subprocess.run(commands, stdout=subprocess.PIPE, check=True)

    # Clean up
    with contextlib.suppress(FileNotFoundError):
        for ending in ['.tex', '.aux', '.log']:
            os.remove('%s%s' % (filename, ending))

    return filename + '.pdf'
