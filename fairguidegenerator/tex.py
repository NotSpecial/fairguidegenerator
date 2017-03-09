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

Important note on date output:

The filter will use the %A option in date formatting. This will set the week-
day depending on the locale. So make sure to actually set the locale to
something german so it fits the rest of the contract. Example:

>>> import locale
>>> locale.setlocale(locale.LC_TIME, "de_CH.UTF-8")

Done! (This is not done automatically since available locales are not
guaranteed)


"""

from jinja2 import Environment, PackageLoader, StrictUndefined
import subprocess
import os
import re

# Create the jinja env
texenv = Environment(
    loader=PackageLoader('fairguidegenerator', 'tex_templates'))
texenv.block_start_string = '((*'
texenv.block_end_string = '*))'
texenv.variable_start_string = '((('
texenv.variable_end_string = ')))'
texenv.comment_start_string = '((='
texenv.comment_end_string = '=))'
texenv.undefined = StrictUndefined
texenv.trim_blocks = True


# Add additional filters
def escape_tex(value):
    """Regex for most tex relevant things."""
    subs = (
        (re.compile(r'\\'), r'\\textbackslash'),
        (re.compile(r'([{}_#%&$])'), r'\\\1'),
        (re.compile(r'~'), r'\~{}'),
        (re.compile(r'\^'), r'\^{}'),
        (re.compile(r'"'), r"''"),
        (re.compile(r'\.\.\.+'), r'\\ldots'),
    )

    newval = value
    for pattern, replacement in subs:
        newval = pattern.sub(replacement, newval)
    return newval

texenv.filters.update({
    # Escaping for tex, short name because used often
    'l': escape_tex,

    # Escape newline
    'newline': lambda x: x.replace('\n', r'\\'),
})


template = texenv.get_template("company_page.tex")


def render_tex(output_dir, **companydata):
    """Render the template and return the filename.

    Returns:
        str: filename (including path) to output
    """
    # Render the template
    rendered = template.render(**companydata)

    # Create filenames and directory (if needed)
    filename = os.path.join(output_dir, companydata['name'])
    texname = filename + '.tex'

    os.makedirs(output_dir, exist_ok=True)

    with open(texname, 'wb') as f:
        f.write(rendered.encode('utf-8'))

    commands = ["pdflatex",
                "-output-directory", output_dir,
                "-interaction=batchmode", texname]

    # Capture output with PIPE (just to keep console clean)
    # Check true requires status code 0
    subprocess.run(commands, stdout=subprocess.PIPE, check=True)

    # Clean up
    for ending in ['.tex', '.aux', '.log']:
        os.remove('%s%s' % (filename, ending))

    return filename + '.pdf'
