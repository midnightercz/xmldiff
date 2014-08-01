import pprint
import sys

#import xml.dom.minidom


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

    __slots__ = ["objects", "name", "value", "_type", "str_cache"]

    def __init__(self, name, value=None, _type=None, str_cache=StrCache()):
        self.objects = {}
        self.name = name
        self.value = value
        self._type = _type
        self.str_cache = str_cache

    def __repr__(self):
        if self.value and len(self.value) > 20:
            value = self.value[:20] + "..."
        else:
            value = self.value
        return "(%s value=%s, %s)" % (self.name, value, repr(self.objects))

    def __hash__(self):
        return hash(self.name) ^ hash(self.value) ^\
            hash(self._type) ^\
            hash(frozenset(self.objects.items()))

    def __eq__(self, other):
        return (self.name == other.name
                and self.value == self.value
                and self._type == self._type
                and set(self.objects) == set(other.objects))

    def __richcmp__(self, other, op):
        if op != 2:
            raise NotImplemented
        return (self.name == other.name
                and self.value == other.value
                and self.diff_val == other.diff_val
                and self._type == other._type
                and self.objects == other.objects
                and self.diff_objects == other.diff_objects)

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

    def get_last(self, path):
        """ method simillar to .get, but path doesn't need to contain
        index of item in list in path - last items in lists is accessed
        automaticaly
        """

        current_object = self
        splitted = path.split(".")
        for part in splitted[:-1]:
            if isinstance(current_object, NodeList):
                current_object = current_object._get_last()
            current_object = current_object._get(part, final=False)
        return current_object._get_last(splitted[-1], final=True)

    #_get_last = _get
    def _get_last(self, part, final):
        if (final and hasattr(self.objects[part], "value")
           and self.objects[part].value):
            return self.objects[part].value
        else:
            return self.objects[part]

    def set(self, path, value=None, _type=None):
        """ method for set object to path. Method doesn't work recursively -
        all parts of path have to exit before inserting last - new one part.
        For example you have to call set("some") before you cal
        set("some.foo"). If value is specified, will be assigned to last
        object in path. Method works same way as get - if list of items
        occurs somewhere in path, you need to specify index for concrete item
        """

        splitted = path.split(".")
        current_object = self
        for part in splitted[:-1]:
            current_object = current_object._get(part, final=False)

        if splitted[-1] not in current_object.objects:
            current_object.objects[splitted[-1]] = Node(splitted[-1],
                                                        value, _type)
        else:
            if isinstance(current_object.objects[splitted[-1]], NodeList):
                current_object.objects[splitted[-1]].set(splitted[-1])
            else:
                old = current_object.objects[splitted[-1]]
                current_object.objects[splitted[-1]] = NodeList(splitted[-1])
                current_object.objects[splitted[-1]].objects.append(old)
                current_object.objects[splitted[-1]].set(splitted[-1])

    def fill(self, path, value=None, _type=None):
        """ same as set, but automaticaly traverse path over last items
        in lists"""
        splitted = path.split(".")
        current_object = self
        last_part = splitted[-1]
        last_part = self.str_cache.get(last_part)

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
                    current_object.objects[last_part] = NodeList(last_part)
                    current_object.objects[last_part].objects.append(old)
                    current_object.objects[last_part].set(last_part)
                    return current_object.objects[last_part]._get_last_index("")
                else:
                    current_object.objects[last_part].value = value
                    current_object.objects[last_part]._type = _type
                    return current_object.objects[last_part].value

    def diff(self, other, path="", ids={}):
        """Computes deep difference between two nodes"""

        current_path = "%s.%s" % (path, self.name)
        keys1 = set(self.objects.keys())
        keys2 = set(other.objects.keys())
        common = keys1 & keys2
        missing_in_2 = keys1 - common
        missing_in_1 = keys2 - common

        ret = DiffNode(self.name)
        ret.original_1 = self
        ret.original_2 = other

        for ckey in common:
            item1 = self.objects[ckey]
            item2 = other.objects[ckey]

            if isinstance(item1, NodeList) and not isinstance(item2, NodeList):
                new_list = NodeList(item2.name)
                new_list.objects.append(item2)
                item2 = new_list
            elif isinstance(item2, NodeList) and not isinstance(item1, NodeList):
                new_list = NodeList(item1.name)
                new_list.objects.append(item1)
                item1 = new_list

            item = item1.diff(item2, path=current_path, ids=ids)
            ret.common_objects[ckey] = item

        if self.value is not None:
            if self.value != other.value or self._type != other._type:
                ret.value_diff = True
        for mkey2 in missing_in_1:
            ret.missing_in_1[mkey2] = other.objects[mkey2]
        for mkey1 in missing_in_2:
            ret.missing_in_2[mkey1] = self.objects[mkey1]
        return ret


class NodeList(object):
    __slots__ = ["objects", "name", "value", "_type", "str_cache"]

    def __init__(self, name, str_cache=StrCache()):
        self.objects = []
        self.name = name
        self.str_cache = str_cache

    def __repr__(self):
        return "(%s, %s)" % (self.name, repr(self.objects))

    def __eq__(self, other):
        return (self.name == other.name
                and set(self.objects) == set(other.objects))

    def __richcmp__(self, other, op):
        if op != 2:
            raise NotImplemented
        return (self.name == other.name
                and set(self.objects) == set(other.objects)
                and set(self.diff_objects) == set(other.diff_objects))

    def _get_last(self, part, final=False):
        return self.objects[-1].objects[part]

    def _get_last_index(self, part, final=False):
        return self.objects[-1]

    def _get(self, part, final):
        return self.objects[int(part)]

    def set(self, name):
        self.objects.append(Node(name))

    def diff(self, other, path="", ids={}):
        current_path = "%s.%s" % (path, self.name)
        ret = DiffNodeList(self.name)
        objects1 = set()
        objects2 = set()
        o1_by_id = {}
        o2_by_id = {}
        use_ids = False
        if current_path in ids:
            use_ids = True
        for dest, id_map, source in zip((objects1, objects2),
                                        (o1_by_id, o2_by_id), (self, other)):
            for o in source.objects:
                if use_ids:
                    # id compute
                    _id_parts = []
                    for id_part in ids[current_path]:
                        if id_part in o.objects:
                            val = o.get(id_part)
                            if isinstance(val, unicode):
                                _id_parts.append(val)
                            else:
                                _id_parts.append(val.load())
                        else:
                            _id_parts.append("")
                    _id = "".join(_id_parts)
                    id_map[_id] = o
                    # add id
                    dest.add(_id)
                else:
                    # add whole object
                    print hash(o)
                    dest.add(o)

        common_o = objects1 & objects2
        print "COMMON"
        print common_o
        missing_in_1 = objects2 - common_o
        print "MISSING IN 1"
        print missing_in_1
        missing_in_2 = objects1 - common_o
        print "MISSING IN 2"
        print missing_in_2
    
        for o in common_o:
            # if id is used, calculate diff, because two objects with same
            # id don't have to be same in general
            if use_ids:
                ret.common_objects.append(o1_by_id[o].diff(o2_by_id[o],
                                                           path=current_path,
                                                           ids=ids))
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
        return ret


class DiffNode(object):
    __slots__ = ["name", "common_objects", "missing_in_1", "missing_in_2",
                 "original_1", "original_2", "value_diff"]

    def __init__(self, name):
        self.name = name
        self.common_objects = {}
        self.missing_in_1 = {}
        self.missing_in_2 = {}
        self.original_1 = None
        self.original_2 = None
        self.value_diff = False


class DiffNodeList(object):
    __slots__ = ["name", "common_objects", "missing_in_1", "missing_in_2",
                 "original_1", "original_2", "value_diff"]

    def __init__(self, name):
        self.name = name
        self.common_objects = []
        self.missing_in_1 = []
        self.missing_in_2 = []
