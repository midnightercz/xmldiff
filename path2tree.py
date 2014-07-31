import pprint
import sys

import xml.dom.minidom


class Node(object):
    def __init__(self, name, value=None, _type=None):
        self.objects = {}
        self.name = name
        self.value = value
        self.diff_val = None
        self._type = _type
        self.diff_type = None
        self.diff_objects = {}

    def __repr__(self):
        if self.value and len(self.value) > 20:
            value = self.value[:20]+"..."
        else:
            value = self.value
        return "(%s value=%s, %s)" % (self.name, value, repr(self.objects))

    def __hash__(self):
        return hash(self.name) ^ hash(self.value) ^ hash(self.diff_val) ^\
               hash(self._type) ^\
               hash(frozenset(self.objects.items())) ^\
               hash(frozenset(self.diff_objects.items()))

    def __eq__(self, other):
        return (self.name == other.name
                and self.value == other.value
                and self.diff_val == other.diff_val
                and self._type == other._type
                and self.objects == other.objects
                and self.diff_objects == other.diff_objects)

    def get(self, path):
        current_object = self
        splitted = path.split(".")
        for part in splitted[:-1]:
            current_object = current_object._get(part, final=False)
        return current_object._get(splitted[-1], final=True)

    def _get(self, part, final):
        if (final and hasattr(self.objects[part], "value")
           and self.objects[part].value):
            return self.objects[part].value
        else:
            return self.objects[part]

    def get_last(self, path):
        current_object = self
        splitted = path.split(".")
        for part in splitted[:-1]:
            if isinstance(current_object, NodeList):
                current_object = current_object._get_last()
            current_object = current_object._get(part, final=False)
        return current_object._get_last(splitted[-1], final=True)

    _get_last = _get

    def set(self, path, value=None, _type=None):
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
        splitted = path.split(".")
        current_object = self
        for part in splitted[:-1]:
            current_object = current_object._get_last(part, final=False)

        if isinstance(current_object, NodeList):
            current_object = current_object._get_last_index(part)
        if splitted[-1] not in current_object.objects:
            current_object.objects[splitted[-1]] = Node(splitted[-1],
                                                        value, _type)
        else:
            if isinstance(current_object.objects[splitted[-1]], NodeList):
                current_object.objects[splitted[-1]].set(splitted[-1])
            else:
                if value is None:
                    old = current_object.objects[splitted[-1]]
                    current_object.objects[splitted[-1]] = NodeList(splitted[-1])
                    current_object.objects[splitted[-1]].objects.append(old)
                    current_object.objects[splitted[-1]].set(splitted[-1])
                else:
                    old = current_object.objects[splitted[-1]].value = value
                    old = current_object.objects[splitted[-1]]._type = _type

    def diff(self, other, path="", ids={}):
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
                ret.value = self.value
                ret.diff_value = other.value
                ret._type = other._type
                ret.diff_value = other.value
        for mkey2 in missing_in_1:
            ret.missing_in_1[mkey2] = other.objects[mkey2]
        for mkey1 in missing_in_2:
            ret.missing_in_2[mkey1] = self.objects[mkey1]
        return ret


class NodeList(Node):
    def __init__(self, name):
        self.objects = []
        self.diff_objects = []
        self.name = name

    def __repr__(self):
        return "(%s, %s)" % (self.name, repr(self.objects))

    def __eq__(self, other):
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
        for dest, id_map, source in zip((objects1, objects2),
                                        (o1_by_id, o2_by_id),
                                        (self, other)):
            for o in source.objects:
                if current_path in ids:
                    _id_parts = []
                    for id_part in ids[current_path]:
                        if id_part in o.objects:
                            _id_parts.append(o.get(id_part))
                        else:
                            _id_parts.append("")
                    _id = "".join(_id_parts)
                    id_map[_id] = o
                    dest.add(_id)
                else:
                    dest.add(o)

        common_o = objects1 & objects2
        missing_in_1 = objects2 - common_o
        missing_in_2 = objects1 - common_o

        for o in common_o:
            if current_path in ids:
                ret.common_objects.append(o1_by_id[o].diff(o2_by_id[o],
                                                           path=current_path,
                                                           ids=ids))
            else:
                pass
        for o1 in missing_in_2:
            if current_path in ids:
                ret.missing_in_2.append(o1_by_id[o1])
            else:
                ret.missing_in_2.append(o1)
        for o2 in missing_in_1:
            if current_path in ids:
                ret.missing_in_1.append(o2_by_id[o2])
            else:
                ret.missing_in_1.append(o2)
        return ret


class DiffNode(object):
    def __init__(self, name):
        self.name = name
        self.common_objects = {}
        self.missing_in_1 = {}
        self.missing_in_2 = {}
        self.value = None
        self.diff_value = None
        self._type = None
        self.diff_type = None
        self.original_1 = None
        self.original_2 = None


class DiffNodeList(object):
    def __init__(self, name):
        self.name = name
        self.common_objects = []
        self.missing_in_1 = []
        self.missing_in_2 = []
        self.value = None
        self.diff_value = None
        self._type = None
        self.diff_type = None
