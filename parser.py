import xml.parsers.expat
import StringIO
#import pyximport; pyximport.install()

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


class XMLProperty(object):
    def __init__(self, source, offset, _len):
        self.source = source
        self.offset = offset
        self._len = _len

    def load(self):
        self.source.seek(self.offset)
        ret = self.source.read(self._len).strip()
        return ret

    def store(self, source, offset, _len):
        self.source = source
        self.offset = offset
        self._len = _len

    def __eq__(self, other):
        return self.load().strip() == other.load().strip()

    def __ne__(self, other):
        return self.load().strip() != other.load().strip()


class Parser(object):
    def __init__(self):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.start_el_handler
        self.parser.EndElementHandler = self.end_el_handler
        self.parser.CharacterDataHandler = self.char_data_handler
        self.el_stack = []
        self.obj_stack = []
        self.path = ""
        self.cdata = None
        self.tree = path2tree.Node(u"root")

    def start_el_handler(self, name, attrs):
        self.el_stack.append({"name": name, "attrs": attrs})
        self.path = ".".join([el["name"] for el in self.el_stack])
        self.tree.fill(self.path)
        for key, val in attrs.iteritems():
            self.tree.fill("%s.%s" % (self.path, key), value=val, _type=u"attr")
        self.cdata = None
        #self.cdata_xml = XMLProperty(self.source, self.parser.CurrentByteIndex,
        #                             0)

    def end_el_handler(self, name):
        if self.cdata is not None and self.cdata.strip():
            self.cdata_xml._len = self.parser.CurrentByteIndex - self.cdata_xml.offset
            #self.tree.fill(self.path, value=self.cdata.strip(), _type="content")
            self.tree.fill(self.path, value=self.cdata_xml, _type=u"content")
        self.el_stack.pop()
        self.path = ".".join([el["name"] for el in self.el_stack])
        self.cdata = None

    def char_data_handler(self, text):
        if self.cdata is None:
            self.cdata = text
            self.cdata_xml = XMLProperty(self.source,
                                         self.parser.CurrentByteIndex,
                                         0)
        else:
            self.cdata += text

    def parse_file(self, fp):
        self.source = fp
        self.parser.ParseFile(fp)
        return self.tree

    def parse_str(self, _str):
        self.source = StringIO.StringIO(_str)
        self.parser.Parse(_str, True)
        return self.tree
