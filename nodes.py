import re
import sys
from io import StringIO

from .elements import Element

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer

from markdown import markdown

from . import constants


def create_node(haml_line):
    stripped_line = haml_line.strip()

    if len(stripped_line) == 0:
        return None

    if (re.match(
            constants.NODES_INLINE_VARIABLE, stripped_line) or
            re.match(constants.NODES_ESCAPED_INLINE_VARIABLE, stripped_line)):
        return PlaintextNode(haml_line)

    if stripped_line[0] == constants.NODES_HAML_ESCAPE:
        return PlaintextNode(
            haml_line.replace(
                constants.NODES_HAML_ESCAPE, '', 1))

    if stripped_line.startswith(constants.NODES_DOCTYPE):

        return DoctypeNode(haml_line)

    if stripped_line[0] in constants.NODES_ELEMENT_CHARACTERS:
        return ElementNode(haml_line)

    if (stripped_line[0:len(constants.NODES_CONDITIONAL_COMMENT)] ==
            constants.NODES_CONDITIONAL_COMMENT):
        return ConditionalCommentNode(haml_line)

    if stripped_line[0] == constants.NODES_HTML_COMMENT:
        return CommentNode(haml_line)

    for comment_prefix in constants.NODES_HAML_COMMENTS:
        if stripped_line.startswith(comment_prefix):
            return HamlCommentNode(haml_line)

    if stripped_line[0] == constants.NODES_VARIABLE:
        return VariableNode(haml_line)

    if stripped_line[0] == constants.NODES_TAG:
        return TagNode(haml_line)

    if stripped_line == constants.NODES_JAVASCRIPT_FILTER:
        return JavascriptFilterNode(haml_line)

    if stripped_line in constants.NODES_COFFEESCRIPT_FILTERS:
        return CoffeeScriptFilterNode(haml_line)

    if stripped_line == constants.NODES_CSS_FILTER:
        return CssFilterNode(haml_line)

    if stripped_line == constants.NODES_STYLUS_FILTER:
        return StylusFilterNode(haml_line)

    if stripped_line == constants.NODES_PLAIN_FILTER:
        return PlainFilterNode(haml_line)

    if stripped_line == constants.NODES_PYTHON_FILTER:
        return PythonFilterNode(haml_line)

    if stripped_line == constants.NODES_CDATA_FILTER:
        return CDataFilterNode(haml_line)

    if stripped_line == constants.NODES_PYGMENTS_FILTER:
        return PygmentsFilterNode(haml_line)

    if stripped_line == constants.NODES_MARKDOWN_FILTER:
        return MarkdownFilterNode(haml_line)

    return PlaintextNode(haml_line)


class TreeNode(object):

    """
    Generic parent/child tree class
    """

    def __init__(self):
        self.parent = None
        self.children = []

    def left_sibling(self):
        siblings = self.parent.children
        index = siblings.index(self)
        return siblings[index - 1] if index > 0 else None

    def right_sibling(self):
        siblings = self.parent.children
        index = siblings.index(self)
        return siblings[index + 1] if index < len(siblings) - 1 else None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)


class RootNode(TreeNode):

    def __init__(self):
        TreeNode.__init__(self)
        self.indentation = -2

        # Number of empty lines to render after node
        self.newlines = 0

        # Rendered text at start of node, e.g. "<p>\n"
        self.before = ''

        # Rendered text at end of node, e.g. "\n</p>"
        self.after = ''

        # Indicates that a node does not render anything (for whitespace
        # removal)
        self.empty_node = False

    def render(self):

        # Render (sets self.before and self.after)
        self._render_children()

        # Post-render (nodes can modify the rendered text of other nodes)
        self._post_render()

        # Generate HTML
        return self._generate_html()

    def render_newlines(self):
        return '\n' * (self.newlines + 1)

    def parent_of(self, node):
        if (self._should_go_inside_last_node(node)):
            ret = self.children[-1].parent_of(node)
            return ret
        else:
            return self

    def should_treat_children_as_multiline(self):

        if self.parent:

            return self.parent.should_treat_children_as_multiline()

        else:

            return True

    def _render_children(self):

        for child in self.children:
            child._render()

    def _post_render(self):
        for child in self.children:
            child._post_render()

    def _generate_html(self):
        output = []
        output.append(self.before)

        for child in self.children:
            output.append(child.before)
            output += [gc._generate_html() for gc in child.children]
            output.append(child.after)

        output.append(self.after)

        return ''.join(output)

    def add_node(self, node):

        if (self._should_go_inside_last_node(node)):

            self.children[-1].add_node(node)

        else:

            self.add_child(node)

    def _should_go_inside_last_node(self, node):

        return self.children and (
            node.indentation > self.children[-1].indentation or
            (node.indentation == self.children[-1].indentation and
                self.children[-1].should_contain(node)))

    def should_contain(self, node):

        return False

    def debug_tree(self):

        return '\n'.join(self._debug_tree([self]))

    def _debug_tree(self, nodes):

        output = []

        for n in nodes:

            output.append('%s%s' % (' ' * (n.indentation + 2), n))

            if n.children:

                output += self._debug_tree(n.children)

        return output

    def __repr__(self):

        return '(%s)' % (self.__class__)


class HamlNode(RootNode):

    def __init__(self, haml):
        RootNode.__init__(self)
        self.haml = haml.strip()
        self.raw_haml = haml
        self.indentation = (len(haml) - len(haml.lstrip()))
        self.spaces = ''.join(haml[0] for i in range(self.indentation))

    def replace_inline_variables(self, content):
        content = re.sub(
            constants.NODES_INLINE_VARIABLE, r'{{ \2 }}',
            content)
        content = re.sub(
            constants.NODES_ESCAPED_INLINE_VARIABLE, r'\1',
            content)
        return content

    def __repr__(self):

        return '(%s in=%d, nl=%d: %s)' % (
            self.__class__,
            self.indentation,
            self.newlines, self.haml)


class PlaintextNode(HamlNode):

    """
    Node that is not modified or processed when rendering
    """

    def _render(self):

        self.before = '%s%s' % (
            self.spaces,
            self.replace_inline_variables(self.haml))

        if self.children:

            self.before += self.render_newlines()

        else:

            self.after = self.render_newlines()

        self._render_children()


class ElementNode(HamlNode):

    '''Node which represents a HTML tag'''

    def __init__(self, haml):
        HamlNode.__init__(self, haml)
        self.django_variable = False

    def _render(self):
        self.element = Element(self.haml)
        self.django_variable = self.element.django_variable
        self.before = self._render_before(self.element)
        self.after = self._render_after(self.element)
        self._render_children()

    def _render_before(self, element):
        '''Render opening tag and inline content'''
        start = ["%s<%s" % (self.spaces, element.tag)]
        if element.id:
            start.append(" id='%s'" %
                         self.replace_inline_variables(element.id))
        if element.classes:
            start.append(" class='%s'" %
                         self.replace_inline_variables(element.classes))
        if element.attributes:
            start.append(
                ' ' + self.replace_inline_variables(element.attributes))

        content = self._render_inline_content(self.element.inline_content)

        if element.nuke_inner_whitespace and content:
            content = content.strip()

        if element.self_close and not content:
            start.append(" />")
        elif content:
            start.append(">%s" % (content))
        elif self.children:
            start.append(">%s" % (self.render_newlines()))
        else:
            start.append(">")
        return ''.join(start)

    def _render_after(self, element):
        '''Render closing tag'''
        if element.inline_content:
            return "</%s>%s" % (element.tag, self.render_newlines())
        elif element.self_close:
            return self.render_newlines()
        elif self.children:
            return "%s</%s>\n" % (self.spaces, element.tag)
        else:
            return "</%s>\n" % (element.tag)

    def _post_render(self):
        # Inner whitespace removal
        if self.element.nuke_inner_whitespace:
            self.before = self.before.rstrip()
            self.after = self.after.lstrip()

            if self.children:
                node = self
                # If node renders nothing, do removal on its first child
                # instead
                if node.children[0].empty_node:

                    node = node.children[0]

                if node.children:
                    node.children[0].before = node.children[0].before.lstrip()

                node = self

                if node.children[-1].empty_node:

                    node = node.children[-1]

                if node.children:

                    node.children[-1].after = node.children[-1].after.rstrip()

        # Outer whitespace removal
        if self.element.nuke_outer_whitespace:
            left_sibling = self.left_sibling()
            if left_sibling:
                # If node has left sibling, strip whitespace after left sibling
                left_sibling.after = left_sibling.after.rstrip()
                left_sibling.newlines = 0
            else:
                # If not, whitespace comes from it's parent node,
                # so strip whitespace before the node
                self.parent.before = self.parent.before.rstrip()
                self.parent.newlines = 0

            self.before = self.before.lstrip()
            self.after = self.after.rstrip()

            right_sibling = self.right_sibling()
            if right_sibling:
                right_sibling.before = right_sibling.before.lstrip()
            else:
                self.parent.after = self.parent.after.lstrip()
                self.parent.newlines = 0

        super(ElementNode, self)._post_render()

    def _render_inline_content(self, inline_content):
        if inline_content is None or len(inline_content) == 0:

            return None

        if self.django_variable:

            content = "{{ " + inline_content.strip() + " }}"

            return content

        else:

            return self.replace_inline_variables(inline_content)


class CommentNode(HamlNode):

    def _render(self):
        self.after = "-->\n"

        if self.children:

            self.before = "<!-- %s" % (self.render_newlines())
            self._render_children()

        else:

            self.before = "<!-- %s " % (
                self.haml.lstrip(constants.NODES_HTML_COMMENT).strip())


class ConditionalCommentNode(HamlNode):

    def _render(self):
        conditional = self.haml[1: self.haml.index(']') + 1]

        if self.children:
            self.before = "<!--%s>\n" % (conditional)
        else:
            content = self.haml[
                len(
                    constants.NODES_CONDITIONAL_COMMENT) +
                len(conditional) - 1:]
            self.before = "<!--%s>%s" % (conditional, content)

        self.after = "<![endif]-->"
        self._render_children()


class DoctypeNode(HamlNode):

    def _render(self):
        doctype = self.haml.lstrip(constants.NODES_DOCTYPE).strip()

        parts = doctype.split()
        if parts and parts[0] == "XML":
            encoding = parts[1] if len(parts) > 1 else 'utf-8'
            self.before = "<?xml version='1.0' encoding='%s' ?>" % encoding
        else:
            types = constants.NODES_DOCTYPES

            if doctype in types:
                self.before = types[doctype]

        self.after = self.render_newlines()


class HamlCommentNode(HamlNode):

    def _render(self):
        self.after = self.render_newlines()[1:]

    def _post_render(self):
        pass


class VariableNode(ElementNode):

    def __init__(self, haml):
        ElementNode.__init__(self, haml)
        self.django_variable = True

    def _render(self):
        tag_content = self.haml.lstrip(VARIABLE)
        self.before = "%s%s" % (
            self.spaces, self._render_inline_content(tag_content))
        self.after = self.render_newlines()

    def _post_render(self):
        pass


class TagNode(HamlNode):
    self_closing = {'for': 'endfor',
                    'if': 'endif',
                    'ifchanged': 'endifchanged',
                    'ifequal': 'endifequal',
                    'ifnotequal': 'endifnotequal',
                    'block': 'endblock',
                    'filter': 'endfilter',
                    'autoescape': 'endautoescape',
                    'with': 'endwith',
                    'blocktrans': 'endblocktrans',
                    'spaceless': 'endspaceless',
                    'comment': 'endcomment',
                    'cache': 'endcache',
                    'localize': 'endlocalize',
                    'compress': 'endcompress'}
    may_contain = {'if': ['else', 'elif'],
                   'ifchanged': 'else',
                   'ifequal': 'else',
                   'ifnotequal': 'else',
                   'for': 'empty',
                   'with': 'with'}

    def __init__(self, haml):
        HamlNode.__init__(self, haml)
        self.tag_statement = self.haml.lstrip(constants.NODES_TAG).strip()
        self.tag_name = self.tag_statement.split(' ')[0]

        if (self.tag_name in list(self.self_closing.values())):

            raise TypeError(
                "Do not close your Django tags manually.  "
                "It will be done for you.")

    def _render(self):
        self.before = "%s{%% %s %%}" % (self.spaces, self.tag_statement)
        if (self.tag_name in list(self.self_closing.keys())):
            self.before += self.render_newlines()
            self.after = '%s{%% %s %%}%s' % (
                self.spaces,
                self.self_closing[self.tag_name],
                self.render_newlines())
        else:
            if self.children:

                self.before += self.render_newlines()

            else:

                self.after = self.render_newlines()

        self._render_children()

    def should_contain(self, node):

        return (
            isinstance(node, TagNode) and
            node.tag_name in self.may_contain.get(self.tag_name, ''))


class FilterNode(HamlNode):

    def add_node(self, node):
        self.add_child(node)

    def should_treat_children_as_multiline(self):
        return False

    def _render_children_as_plain_text(self, remove_indentation=True):
        if self.children:
            initial_indentation = len(self.children[0].spaces)
        for child in self.children:
            child.before = ''
            if not remove_indentation:
                child.before = child.spaces
            else:
                child.before = child.spaces[initial_indentation:]
            child.before += child.haml
            child.after = child.render_newlines()

    def _post_render(self):
        # Don't post-render children of filter nodes as we don't want them to
        # be interpreted as HAML
        pass


class PlainFilterNode(FilterNode):

    def __init__(self, haml):
        FilterNode.__init__(self, haml)
        self.empty_node = True

    def _render(self):

        if self.children:

            first_indentation = self.children[0].indentation

        self._render_children_as_plain_text()


class PythonFilterNode(FilterNode):

    def _render(self):
        if self.children:
            self.before = self.render_newlines()[1:]
            indent_offset = len(self.children[0].spaces)
            code = "\n".join([node.raw_haml[indent_offset:]
                              for node in self.children]) + '\n'
            compiled_code = compile(code, "", "exec")

            buffer = StringIO()
            sys.stdout = buffer
            try:
                exec(compiled_code)
            except Exception as e:
                # Change exception message to let developer know
                # that exception comes from
                # a PythonFilterNode
                if e.args:
                    args = list(e.args)
                    args[0] = "Error in :python filter code: " + e.message
                    e.args = tuple(args)
                raise e
            finally:
                # restore the original stdout
                sys.stdout = sys.__stdout__
            self.before += buffer.getvalue()
        else:
            self.after = self.render_newlines()


class JavascriptFilterNode(FilterNode):

    def _render(self):
        self.before = '<script type=\'text/javascript\'>\n// <![CDATA[%s' % (
            self.render_newlines())
        self.after = '// ]]>\n</script>\n'
        self._render_children_as_plain_text(remove_indentation=False)


class CoffeeScriptFilterNode(FilterNode):

    def _render(self):
        self.before = '<script type=\'text/coffeescript\'>\n#<![CDATA[%s' % (
            self.render_newlines())
        self.after = '#]]>\n</script>\n'
        self._render_children_as_plain_text(remove_indentation=False)


class CssFilterNode(FilterNode):

    def _render(self):
        self.before = '<style type=\'text/css\'>\n/*<![CDATA[*/%s' % (
            self.render_newlines())
        self.after = '/*]]>*/\n</style>\n'
        self._render_children_as_plain_text(remove_indentation=False)


class StylusFilterNode(FilterNode):

    def _render(self):
        self.before = '<style type=\'text/stylus\'>\n/*<![CDATA[*/%s' % (
            self.render_newlines())
        self.after = '/*]]>*/\n</style>\n'
        self._render_children_as_plain_text()


class CDataFilterNode(FilterNode):

    def _render(self):
        self.before = self.spaces + '<![CDATA[%s' % (self.render_newlines())
        self.after = self.spaces + ']]>\n'
        self._render_children_as_plain_text(remove_indentation=False)


class PygmentsFilterNode(FilterNode):

    def _render(self):
        if self.children:
            self.before = self.render_newlines()
            indent_offset = len(self.children[0].spaces)
            text = ''.join(
                ''.join(
                    [c.spaces[indent_offset:], c.haml, c.render_newlines()])
                for c in self.children)
            self.before += highlight(
                text, guess_lexer(self.haml), HtmlFormatter())
        else:
            self.after = self.render_newlines()


class MarkdownFilterNode(FilterNode):

    def _render(self):
        if self.children:
            self.before = self.render_newlines()[1:]
            indent_offset = len(self.children[0].spaces)
            text = ''.join(
                ''.join(
                    [c.spaces[indent_offset:], c.haml, c.render_newlines()])
                for c in self.children)
            self.before += markdown(text)
        else:
            self.after = self.render_newlines()
