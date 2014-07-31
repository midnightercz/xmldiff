import xml.parsers.expat
import path2tree


class UnknownElementError(Exception):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "UnknownElementError: element '%s'" % self.name

    def __str__(self):
        return "UnknownXMLStructureError: path '%s'" % self.name


class UnknownXMLStructureError(Exception):
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return "UnknownXMLStructureError: path '%s'" % self.path

    def __str__(self):
        return "UnknownXMLStructureError: path '%s'" % self.path


class Parser(object):
    def __init__(self):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.start_el_handler
        self.parser.EndElementHandler = self.end_el_handler
        self.parser.CharacterDataHandler = self.char_data_handler
        self.el_stack = []
        self.obj_stack = []
        self.path = ""
        self.cdata = ""
        self.tree = path2tree.Node("root")

    #def handle_elem(self):
    #    try:
    #        return self.ELEM_HANDLERS[self.root_str]
    #    except KeyError:
    #        raise UnknownElementError(self.root_str)

    def start_el_handler(self, name, attrs):
        self.el_stack.append({"name": name, "attrs": attrs})
        self.path = ".".join([el["name"] for el in self.el_stack])
        self.tree.fill(self.path)
        for key, val in attrs.iteritems():
            self.tree.fill("%s.%s" % (self.path, key), value=val, _type="attr")

    def end_el_handler(self, name):
        if self.cdata.strip():
            self.tree.fill(self.path, value=self.cdata.strip(), _type="content")
        self.el_stack.pop()
        self.path = ".".join([el["name"] for el in self.el_stack])
        self.cdata = ""

    def char_data_handler(self, text):
        self.cdata += text

    def parse_file(self, fp):
        self.parser.ParseFile(fp)
        return self.tree

    def parse_str(self, _str):
        self.parser.Parse(_str, True)
        return self.tree
