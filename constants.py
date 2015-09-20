import re

ELEMENTS_SELF_CLOSING_TAGS = (
    'meta',
    'img',
    'link',
    'br',
    'hr',
    'input',
    'source',
    'track'
)


ELEMENTS_DEPRECATION_WARNING = (
    "\n---------------------\n"
    "DEPRECATION WARNING: {tag}"
    "\nThe Django attribute variable feature is deprecated and may be "
    "removed in future versions.\n"
    "Please use inline variables ={...} instead."
    "\n-------------------\n")

HAMLPY_VALID_EXTENSIONS = ['haml', 'hamlpy']

NODES_ELEMENT = '%'
NODES_ID = '#'
NODES_CLASS = '.'
NODES_DOCTYPE = '!!!'
NODES_HTML_COMMENT = '/'
NODES_CONDITIONAL_COMMENT = '/['
NODES_HAML_COMMENTS = ['-#', '=#']
NODES_VARIABLE = '='
NODES_TAG = '-'
NODES_INLINE_VARIABLE = re.compile(
    r'(?<!\\)([#=]\{\s*([a-zA-Z0-9\.\_]+)\s*\})')
NODES_ESCAPED_INLINE_VARIABLE = re.compile(
    r'\\([#=]\{\s*([a-zA-Z0-9\.\_]+)\s*\})')
NODES_COFFEESCRIPT_FILTERS = [':coffeescript', ':coffee']
NODES_JAVASCRIPT_FILTER = ':javascript'
NODES_CSS_FILTER = ':css'
NODES_STYLUS_FILTER = ':stylus'
NODES_PLAIN_FILTER = ':plain'
NODES_PYTHON_FILTER = ':python'
NODES_MARKDOWN_FILTER = ':markdown'
NODES_CDATA_FILTER = ':cdata'
NODES_PYGMENTS_FILTER = ':highlight'
NODES_ELEMENT_CHARACTERS = (NODES_ELEMENT, NODES_ID, NODES_CLASS)
NODES_HAML_ESCAPE = '\\'

NODES_DOCTYPE_EMPTY = ''
NODES_DOCTYPE_STRICT = 'Stict'
NODES_DOCTYPE_FRAMESET = 'Frameset'
NODES_DOCTYPE_5 = '5'
NODES_DOCTYPE_1_1 = '1.1'

NODES_DOCTYPES = {
    NODES_DOCTYPE_EMPTY: (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">'),
    NODES_DOCTYPE_STRICT: (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 '
        'Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">'),
    NODES_DOCTYPE_FRAMESET: (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Frameset//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-frameset.dtd">'),
    NODES_DOCTYPE_5: '<!DOCTYPE html>',
    NODES_DOCTYPE_1_1: (
        '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" '
        '"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">')
}
