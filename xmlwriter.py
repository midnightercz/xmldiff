from xml.sax.saxutils import escape, quoteattr
# import sys


class XMLWriter(object):
    """ Simple XML writer similar to xml.sax.saxutils.XMLGenerator.
    write xml output sequentialy (without building tree in memory)
    to stream"""

    def __init__(self, stream, lvl_sep='    ', encoding="utf-8"):
        self.stream = stream
        self.indent_lvl = 0
        self.indent_sep = lvl_sep
        self.no_content = False
        self.no_cdata = True
        self._encoding = encoding
        self.elem_stack = []
        self.last_action = ""

    def _start_elem_str(self, name, attrs, no_content):
        attrs_str = " ".join(["%s=%s" % (k, quoteattr(v))
                              for k, v in attrs.iteritems() if v is not None])
        end_mark = "/>\n" if no_content else ">"

        if attrs:
            fmt_str = "<%%s %%s %s" % end_mark
            return fmt_str % (name, attrs_str)
        else:
            fmt_str = "<%%s%s" % end_mark
            return fmt_str % (name)

    def start_document(self):
        self.stream.write(u'<?xml version="1.0" encoding="%s"?>\n' % self._encoding)

    def end_document(self):
        self.stream.flush()
        self.stream.close()

    def start_element(self, name, attrs, no_content=False):
        self.indent_lvl += 1
        if self.no_cdata and self.last_action == "start":
            self.stream.write("\n")
        if not no_content:
            self.elem_stack.append(name)
        else:
            self.no_content = True
        self.last_action = "start"

        self.no_cdata = True
        self.stream.write(self.indent_sep * self.indent_lvl)
        self.stream.write(self._start_elem_str(name, attrs, no_content))
        if no_content:
            self.indent_lvl -= 1

    def end_element(self):
        if not self.no_content:
            if self.no_cdata:
                self.stream.write(self.indent_sep * self.indent_lvl)
            self.stream.write("</%s>\n" % self.elem_stack.pop())
            self.indent_lvl -= 1
        else:
            self.no_content = False
        self.no_cdata = True
        self.last_action = "end"

    def cdata(self, content):
        self.no_cdata = False
        self.stream.write(escape(content).encode("utf-8"))

    def comment(self, comment):
        if self.no_cdata and self.last_action == "start":
            self.stream.write("\n")
        self.stream.write(self.indent_sep * (self.indent_lvl+1))
        self.stream.write("<!-- %s -->\n" % comment)
        self.last_action = "end"
