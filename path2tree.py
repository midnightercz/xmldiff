import parser
import collections


class PathNotFound(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return "Path '%s' not found" % self.path


class StrCache(object):
    def __init__(self):
        self.cache = []

    def get(self, key):
        if key not in self.cache:
            self.cache.append(key)
            return key
        else:
            return self.cache[self.cache.index(key)]


class Node(object):
    """ Basic object encapsulating path node"""

    __slots__ = ["objects", "name", "value", "_type", "str_cache", "_hash"]

    def __init__(self, name, value=None, _type=None, str_cache=StrCache()):
        self.objects = {}
        self.name = name
        self.value = value
        self._type = _type
        self.str_cache = str_cache
        self._hash = None

    def __repr__(self):
        if self.value and len(self.value) > 20:
            value = self.value[:20] + "..."
        else:
            value = self.value
        return "(%s value=%s, %s)" % (self.name, value, repr(self.objects))

    def __hash__(self):
        if not self._hash:
            self._hash = (hash(self.name) ^ hash(self.value) ^
                          hash(self._type) ^
                          hash(frozenset(self.objects.items())))
        return self._hash

    def __eq__(self, other):
        return hash(self) == hash(other)

    def get(self, path):
        """ method for get objects occuring in specified path.
        if object has value, method returns value of object. Otherwise
        returning whole object. If Node contains some list of subnodes
        somewhere in path, index of concrete item is required in path
        """

        current_object = self
        splitted = path.split(".")
        try:
            part_path = []
            for part in splitted[:-1]:
                current_object = current_object._get(part, final=False)
                part_path.append(part)
        except KeyError:
            raise PathNotFound(".".join(part_path))
        return current_object._get(splitted[-1], final=True)

    def _get(self, part, final):
        if (final and hasattr(self.objects[part], "value")
           and self.objects[part].value):
            return self.objects[part].value
        else:
            return self.objects[part]

    # This method is not required by Node to be full operational,
    # but could be usefull
    #def get_last(self, path):
    #    """ method simillar to .get, but path doesn't need to contain
    #    index of item in list in path - last items in lists is accessed
    #    automaticaly
    #    """
    #
    #    current_object = self
    #    splitted = path.split(".")
    #    for part in splitted[:-1]:
    #        if isinstance(current_object, NodeList):
    #            current_object = current_object._get_last()
    #        current_object = current_object._get(part, final=False)
    #    return current_object._get_last(splitted[-1], final=True)

    def _get_last(self, part, final):
        if (final and hasattr(self.objects[part], "value")
           and self.objects[part].value):
            return self.objects[part].value
        else:
            return self.objects[part]
    _get_last_light = _get_last

    def set(self, path, value=None, _type=None):
        """ method for set object to path. Method doesn't work recursively -
        all parts of path have to be inserted before
        inserting last - new one part.
        For example you have to call set("some") before you call
        set("some.foo"). If value is specified, will be assigned to last
        object in path. Method works same way as get - if list of items
        occurs somewhere in path, you need to specify index of concrete item
        """

        splitted = path.split(".")
        last_part = self.str_cache.get(splitted[-1])
        current_object = self
        for part in splitted[:-1]:
            current_object = current_object._get(part, final=False)

        if last_part not in current_object.objects:
            current_object.objects[last_part] = Node(last_part,
                                                     value, _type,
                                                     str_cache=self.str_cache)
        else:
            if isinstance(current_object.objects[last_part], NodeList):
                current_object.objects[last_part].set(last_part)
            else:
                old = current_object.objects[last_part]
                current_object.objects[last_part] = NodeList(last_part)
                current_object.objects[last_part].objects.append(old)
                current_object.objects[last_part].set(last_part)

    def fill(self, path, value=None, _type=None):
        """ same as set, but automaticaly traverse path over last items
        in lists"""
        splitted = path.split(".")
        current_object = self
        last_part = self.str_cache.get(splitted[-1])

        for part in splitted[:-1]:
            part = self.str_cache.get(part)
            current_object = current_object._get_last(part, final=False)

        if isinstance(current_object, NodeList):
            current_object = current_object._get_last_index(part)
        if last_part not in current_object.objects:
            current_object.objects[last_part] = Node(last_part, value, _type,
                                                     str_cache=self.str_cache)
            return current_object.objects[last_part]
        else:
            if isinstance(current_object.objects[last_part], NodeList):
                current_object.objects[last_part].set(last_part)
                return current_object.objects[last_part]._get_last_index("")
            else:
                if value is None:
                    old = current_object.objects[last_part]
                    current_object.objects[last_part] = NodeList(
                        last_part,
                        str_cache=self.str_cache)
                    current_object.objects[last_part].objects.append(old)
                    current_object.objects[last_part].set(last_part)
                    return current_object.objects[last_part]._get_last_index("")
                else:
                    current_object.objects[last_part].value = value
                    current_object.objects[last_part]._type = _type
                    return current_object.objects[last_part].value

    def fill_light(self, path, _type, source, index, _len):
        """ same as fill, but create LightNode instead Node"""
        splitted = path.split(".")
        current_object = self
        if isinstance(current_object, LightNode):
            return current_object

        last_part = self.str_cache.get(splitted[-1])

        for part in splitted[:-1]:
            part = self.str_cache.get(part)
            if isinstance(current_object, LightNode):
                break
            current_object = current_object._get_last_light(part, final=False)
        if isinstance(current_object, LightNode):
            return current_object

        if isinstance(current_object, NodeList):
            current_object = current_object._get_last_index(part)
        if isinstance(current_object, LightNode):
            return None

        if last_part not in current_object.objects:
            current_object.objects[last_part] = LightNode(
                last_part, _type,
                source, index, _len,
                str_cache=self.str_cache)
            return current_object.objects[last_part]
        elif not isinstance(current_object, LightNode):
            if isinstance(current_object.objects[last_part], NodeList):
                current_object.objects[last_part].set_light(
                    last_part, _type, source, index, _len, self.str_cache)
                return current_object.objects[last_part]._get_last_index("")
            else:
                old = current_object.objects[last_part]
                current_object.objects[last_part] = NodeList(
                    last_part,
                    str_cache=self.str_cache)
                current_object.objects[last_part].objects.append(old)
                current_object.objects[last_part].objects.append(
                    LightNode(last_part, _type, source, index, _len))
                return current_object.objects[last_part]._get_last_index("")

    def diff(self, other, path="", ids={}, required={}):
        """Computes deep differences between two nodes. This operation
        doesn't preserve content of self and other objects - unneeded objects
        are deleted due memory save up"""

        current_path = "%s.%s" % (path, self.name)
        self_objects = self.objects
        other_objects = other.objects

        keys1 = set(self_objects.keys())
        keys2 = set(other_objects.keys())
        common = keys1 & keys2
        missing_in_2 = keys1 - common
        missing_in_1 = keys2 - common
        del keys1, keys2

        ret = DiffNode(self.name)

        for ckey in common:
            item1 = self_objects[ckey]
            item2 = other_objects[ckey]

            if isinstance(item1, NodeList) and not isinstance(item2,
                                                              NodeList):
                new_list = NodeList(item2.name)
                new_list.objects.append(item2)
                item2 = new_list
            elif isinstance(item2, NodeList) and not isinstance(item1,
                                                                NodeList):
                new_list = NodeList(item1.name)
                new_list.objects.append(item1)
                item1 = new_list

            items_diff = item1.diff(item2, path=current_path, ids=ids,
                                    required=required)
            if not items_diff.is_empty() or (self.name in required and
                                             ckey in required[self.name]):
                ret.common_objects[ckey] = items_diff

        ret._type = self._type
        ret.value = self.value

        if self.value is not None:
            if self.value != other.value or self._type != other._type:
                ret.diff_value = other.value
                ret.diff_type = other._type
                ret.differ = True
            else:
                if not isinstance(self, LightNode):
                    del self.value
                    del self.objects
                if not isinstance(other, LightNode):
                    del other.value
                    del other.objects

        for mkey2 in missing_in_1:
            ret.missing_in_1[mkey2] = other_objects[mkey2]
        for mkey1 in missing_in_2:
            ret.missing_in_2[mkey1] = self_objects[mkey1]
        if missing_in_1 or missing_in_2:
            ret.differ = True
        return ret


class NodeList(object):
    """List of Nodes or LightNodes"""

    __slots__ = ["objects", "name", "_type", "str_cache", "_hash"]

    def __init__(self, name, str_cache=StrCache()):
        self.objects = collections.deque()
        self.name = str_cache.get(name)
        self.str_cache = str_cache
        self._hash = None

    def __repr__(self):
        return "(%s, %s)" % (self.name, repr(self.objects))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def _get_last(self, part, final=False):
        return self.objects[-1].objects[part]

    def _get_last_light(self, part, final=False):
        if isinstance(self.objects[-1], LightNode):
            return self.objects[-1]
        return self.objects[-1].objects[part]

    def _get_last_index(self, part, final=False):
        return self.objects[-1]

    def _get(self, part, final):
        return self.objects[int(part)]

    def set(self, name):
        self.objects.append(Node(name, str_cache=self.str_cache))

    def set_light(self, name, _type, source, index, _len, str_cache):
        self.objects.append(LightNode(name, _type, source, index, _len,
                                      str_cache=self.str_cache))

    def diff(self, other, path="", ids={}, required={}):
        """Computes deep differences between two node lists. This operation
        doesn't preserve content of self and other objects - unneeded objects
        are deleted due memory save up"""

        current_path = "%s.%s" % (path, self.name)
        ret = DiffNodeList(self.name)
        objects1 = set()
        objects2 = set()
        o1_by_id = {}
        o2_by_id = {}
        use_ids = False
        if current_path in ids:
            use_ids = True
        self_objects = self.objects
        other_objects = other.objects
        for dest, id_map, objects in zip((objects1, objects2),
                                         (o1_by_id, o2_by_id),
                                         (self_objects, other_objects)):
            for o in objects:
                if use_ids:
                    # id compute
                    _id_parts = []
                    for id_part in ids[current_path]:
                        if id_part in o.objects:
                            val = o.get(id_part)
                            if isinstance(val, unicode):
                                _id_parts.append(val)
                            elif isinstance(val, LightNode):
                                if isinstance(val.value, unicode):
                                    _id_parts.append(val.value.load())
                                else:
                                    _id_parts.append(val.value)
                            elif isinstance(val, Node):
                                _id_parts.append(str(hash(val)))
                            else:
                                _id_parts.append(val.load())
                        else:
                            _id_parts.append("")
                    _id = "".join([x for x in _id_parts if x])
                    id_map[_id] = o
                    # add id
                    dest.add(_id)
                else:
                    # add whole object
                    dest.add(o)

        common_o = objects1 & objects2
        missing_in_1 = objects2 - common_o
        missing_in_2 = objects1 - common_o

        for o in common_o:
            # if id is used, calculate diff, because two objects with same
            # id don't have to be same in general
            if use_ids:
                common_current_path = ".".join(current_path.split(".")[:-1])
                diff_obj = o1_by_id[o].diff(o2_by_id[o],
                                            path=common_current_path,
                                            ids=ids, required=required)
                if not diff_obj.is_empty():
                    ret.common_objects.append(diff_obj)

        for o1 in missing_in_2:
            if use_ids:
                ret.missing_in_2.append(o1_by_id[o1])
            else:
                ret.missing_in_2.append(o1)
        for o2 in missing_in_1:
            if use_ids:
                ret.missing_in_1.append(o2_by_id[o2])
            else:
                ret.missing_in_1.append(o2)
        if not ret.differ:
            for obj in ret.common_objects:
                if not obj.is_empty():
                    ret.differ = True
                    break
        return ret


class DiffNode(object):
    """Structure holding results of two nodes diff"""

    __slots__ = ["name", "common_objects", "missing_in_1", "missing_in_2",
                 "value", "diff_value", "_type",
                 "diff_type", "differ"]

    def __init__(self, name):
        self.name = name
        self.common_objects = {}
        self.missing_in_1 = {}
        self.missing_in_2 = {}
        self.value = None
        self.diff_value = None
        self._type = None
        self.diff_type = None
        self.differ = False

    def is_empty(self):
        """Check if diff_node contain any changed - if
        copared nodes were different"""

        if self.differ:
            return False
        for item in self.common_objects.itervalues():
            if not item.is_empty():
                return False
        if self.missing_in_1 or self.missing_in_2:
            return False
        return True


class DiffNodeList(object):
    """Structure holding results of two node lists diff"""

    __slots__ = ["name", "common_objects", "missing_in_1", "missing_in_2",
                 "value", "diff_value", "_type",
                 "diff_type", "differ"]

    def __init__(self, name):
        self.name = name
        self.common_objects = collections.deque()
        self.missing_in_1 = collections.deque()
        self.missing_in_2 = collections.deque()
        self.differ = False

    def is_empty(self):
        """same as DiffNode.is_empty()"""

        if self.differ:
            return False
        for item in self.common_objects:
            if not item.is_empty:
                return False
        if self.missing_in_1 or self.missing_in_2:
            return False
        return True


class LightNode(Node):
    """Light version of Node. Content is not loaded into memory, but
    only offset in source file(or source str stream) and length of content
    is stored. LightNode has extremely small memory footprint, but all
    operations consume more time than i case of Node"""

    __slots__ = ["_type", "name", "source", "offset", "_len", "str_cache",
                 "_hash"]

    def __init__(self, name, _type,
                 source, offset, _len, str_cache=StrCache()):
        self._type = _type
        self.name = str_cache.get(name)
        self.source = source
        self.offset = offset
        self._len = _len
        self.str_cache = str_cache
        self._hash = None

    @property
    def objects(self):
        p = parser.Parser()
        p.depth_limit = 1
        oldpos = self.source.tell()
        self.source.seek(self.offset)
        _str = self.source.read(self._len)
        self.source.seek(oldpos)
        ret = p.parse_str(_str)
        return ret.objects[self.name].objects

    @property
    def value(self):
        p = parser.Parser()
        oldpos = self.source.tell()
        self.source.seek(self.offset)
        _str = self.source.read(self._len)
        self.source.seek(oldpos)
        ret = p.parse_str(_str)
        return ret.objects[self.name].value
