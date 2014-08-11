import xml.parsers.expat
import StringIO
import collections

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
    __slots__ = ("source", "offset", "_len", "_hash", "stream")

    def __init__(self, source, offset, _len):
        self.source = source
        self.offset = offset
        self._len = _len
        self._hash = None
        self.stream = None

    def _stream_load(self):
        old_pos = self.source.tell()
        self.source.seek(self.offset)
        content = self.source.read(self._len)
        self.stream = StringIO.StringIO(content)
        self.source.seek(old_pos)

    def load(self):
        self.source.seek(self.offset)
        ret = self.source.read(self._len).strip()
        ret = ret.decode("utf-8")
        return ret

    def store(self, source, offset, _len):
        self.source = source
        self.offset = offset
        self._len = _len

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) != hash(other)

    def __len__(self):
        return self._len

    def __repr__(self):
        self.source.seek(self.offset)
        ret = self.source.read(self._len).strip()
        return ret

    def __getitem__(self, _len):
        start = _len.start if _len.start else 0
        stop = _len.stop if _len.stop else 0
        self.source.seek(self.offset + start)
        ret = self.source.read(stop).strip()
        return ret

    def __hash__(self):
        if not self._hash:
            self.source.seek(self.offset)
            ret = self.source.read(self._len).strip()
            self._hash = hash(ret)
        return self._hash


class Parser(object):
    def __init__(self):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.start_el_handler
        self.parser.EndElementHandler = self.end_el_handler
        self.parser.CharacterDataHandler = self.char_data_handler
        self.el_stack = collections.deque()
        self.path = ""
        self.cdata = False
        self.tree = path2tree.Node("root")
        self.light_ended = False

    def start_el_handler(self, name, attrs):
        if self.light_ended:
            self.start_el_light_ended(name, attrs)
        if len(self.el_stack) > 3:
            self.start_el_light(name, attrs)
        else:
            self.start_el_normal(name, attrs)

    def start_el_normal(self, name, attrs):
        self.path = ".".join([el["name"] for el in self.el_stack] + [name])
        added = self.tree.fill(self.path, value=None, _type="content")
        self.el_stack.append({"name": name, "attrs": attrs, "node": added})
        for key, val in attrs.iteritems():
            self.tree.fill("%s.%s" % (self.path, key),
                           value=val, _type="attr")
        self.cdata = None

    def start_el_light_ended(self, name, attrs):
        node = self.el_stack[-1]["node"]
        if self.light_ended and node:
            stack_item = self.el_stack.pop()
            node = stack_item["node"]
            node._len = self.parser.CurrentByteIndex - node.offset
            self.path = ".".join([el["name"] for el in self.el_stack])
            self.light_ended = False

    def start_el_light(self, name, attrs):
        self.path = ".".join([el["name"] for el in self.el_stack] + [name])
        added = self.tree.fill_light(self.path, "content", self.source,
                                     self.parser.CurrentByteIndex, 0)
        self.el_stack.append({"name": name, "attrs": attrs, "node": added})
        self.cdata = None

    def end_el_handler(self, name):
        self.start_el_light_ended(name, None)
        node = self.el_stack[-1]["node"]
        if not node or isinstance(node, path2tree.LightNode):
            self.end_el_light(name)
        else:
            self.end_el_normal(name)
        self.path = ".".join([el["name"] for el in self.el_stack])

    def end_el_light(self, name):
        node = self.el_stack[-1]["node"]
        if node:
            self.light_ended = True
        else:
            self.el_stack.pop()

    def end_el_normal(self, name):
        stack_item = self.el_stack.pop()
        node = stack_item["node"]
        self.path = ".".join([el["name"] for el in self.el_stack])
        if self.cdata:
            self.cdata_xml._len = self.parser.CurrentByteIndex - self.cdata_xml.offset
            node.value = self.cdata_xml
            node._type = "content"
        self.cdata = None

    def char_data_handler(self, text):
        node = self.el_stack[-1]["node"]
        if not node or isinstance(node, path2tree.LightNode):
            self.char_data_light(text)
        else:
            self.char_data_normal(text)

    def char_data_light(self, text):
        pass

    def char_data_normal(self, text):
        if self.cdata is None:
            self.cdata = False
            self.cdata_xml = XMLProperty(self.source,
                                         self.parser.CurrentByteIndex, 0)
        if not self.cdata and text.strip():
            self.cdata = True

    def parse_file(self, fp):
        self.source = fp
        self.parser.ParseFile(fp)

        if self.light_ended:
            stack_item = self.el_stack.pop()
            node = stack_item["node"]
            node._len = self.parser.CurrentByteIndex - node.offset
            self.path = ".".join([el["name"] for el in self.el_stack])
            self.light_ended = False

        return self.tree

    def parse_str(self, _str):
        self.source = StringIO.StringIO(_str)
        self.parser.Parse(_str, True)

        if self.light_ended:
            stack_item = self.el_stack.pop()
            node = stack_item["node"]
            node._len = self.parser.CurrentByteIndex - node.offset
            self.path = ".".join([el["name"] for el in self.el_stack])
            self.light_ended = False

        return self.tree
