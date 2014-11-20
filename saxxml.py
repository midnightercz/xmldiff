from path2tree import NodeList
from path2tree import DiffNode
from path2tree import DiffNodeList


def tree2xml(xmlgenerator, root_node):
    stack = [(root_node, "start")]
    while stack:
        node, action = stack.pop(0)
        if action == "start":
            if isinstance(node, NodeList):
                if hasattr(node, "objects"):
                    i = 0
                    for obj in node.objects:
                        stack.insert(i, (obj, "start"))
                        i += 1
            else:
                no_content = True
                attrs = {}
                i = 0
                if hasattr(node, "objects"):
                    for subnode in node.objects.itervalues():
                        if (not isinstance(subnode, NodeList) and
                           subnode._type == "attr"):
                            attrs[subnode.name] = subnode.value
                        else:
                            stack.insert(i, (subnode, "start"))
                            i += 1
                            no_content = False
                no_content = node.value is None and no_content
                xmlgenerator.start_element(node.name, attrs,
                                           no_content=no_content)
                if node.value:
                    xmlgenerator.cdata(node.value.load())
                stack.insert(i, (node, "end"))
        if action == "end":
            xmlgenerator.end_element()


def diff_tree2xml(xmlgenerator, root_node, required_attrs={}):
    stack = [(root_node, "start_diff", ".root")]
    while stack:
        node, action, current_path = stack.pop(0)
        if action == "start_diff":
            if isinstance(node, DiffNodeList):
                i = 0
                empty_common = True
                for obj in node.common_objects:
                    if not obj.is_empty():
                        empty_common = False
                        break
                if not empty_common:
                    stack.insert(i, ("COMMON", "start_xml", current_path))
                    i += 1
                    for obj in node.common_objects:
                        stack.insert(i, (obj, "start_diff", current_path))
                        i += 1
                if node.missing_in_1:
                    stack.insert(i, ("MISSING IN 1", "start_xml", current_path))
                    i += 1
                    for obj in node.missing_in_1:
                        stack.insert(i, (obj, "start_xml", current_path))
                        i += 1
                if node.missing_in_2:
                    stack.insert(i, ("MISSING IN 2", "start_xml", current_path))
                    i += 1
                    for obj in node.missing_in_2:
                        stack.insert(i, (obj, "start_xml", current_path))
                        i += 1

            elif isinstance(node, DiffNode):
                if node._type != "attr":
                    if node.is_empty():
                        continue
                    attrs = {}
                    i = 0
                    no_content = True
                    for subnode in node.common_objects.itervalues():
                        _name = subnode.name
                        _dname = "__diff__%s" % subnode.name
                        if (not isinstance(subnode, DiffNodeList) and
                           subnode._type == "attr"):
                            if subnode.differ:
                                attrs[_name] = subnode.value
                                attrs[_dname] = subnode.diff_value
                            if (current_path in required_attrs and
                               subnode.name in required_attrs[current_path]):
                                attrs[_name] = subnode.value
                                attrs[_dname] = subnode.diff_value
                        else:
                            if (current_path in required_attrs and
                               subnode.name in required_attrs[current_path]):
                                stack.insert(i, (subnode, "start_xml",
                                                 "%s.%s" % (current_path,
                                                            subnode.name)))
                            else:
                                stack.insert(i, (subnode, "start_diff",
                                                 "%s.%s" % (current_path,
                                                            subnode.name)))
                            i += 1
                            no_content = False

                    for subnode in node.missing_in_1.itervalues():
                        _name = "__missing_in_1__%s" % subnode.name
                        if (not isinstance(subnode, NodeList) and
                           subnode._type == "attr"):
                            attrs[_name] = subnode.value
                        else:
                            stack.insert(i, (subnode, "start_xml", current_path))
                            stack.insert(i, ("MISSING IN 1", "start_xml", current_path))
                            i += 2
                            no_content = False

                    for subnode in node.missing_in_2.itervalues():
                        _name = "__missing_in_2__%s" % subnode.name
                        if (not isinstance(subnode, NodeList) and
                           subnode._type == "attr"):
                            attrs[_name] = subnode.value
                        else:
                            stack.insert(i, (subnode, "start_xml", current_path))
                            stack.insert(i, ("MISSING IN 2", "start_xml", current_path))
                            i += 2
                            no_content = False

                    no_content = node.value is None and no_content
                    xmlgenerator.start_element(node.name, attrs, no_content)
                    if node.differ:
                        if node.value:
                            xmlgenerator.comment("MISSING IN 1")
                            xmlgenerator.cdata(node.value.load())
                        if node.diff_value:
                            xmlgenerator.comment("MISSING IN 2")
                            xmlgenerator.cdata(node.diff_value.load())
                    stack.insert(i, (node, "end_diff", current_path))
        elif action == "start_xml":
            if not isinstance(node, str):
                tree2xml(xmlgenerator, node)
            else:
                xmlgenerator.comment(node)
        elif action == "end_diff":
            xmlgenerator.end_element()
