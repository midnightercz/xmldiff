#from path2tree import LightNode
from path2tree import NodeList
from path2tree import DiffNode
from path2tree import DiffNodeList
#from xml.sax.saxutils import XMLGenerator
#from xml.sax.xmlreader import AttributesNSImpl


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
                xmlgenerator.start_element(node.name, attrs, no_content=no_content)
                if node.value:
                    xmlgenerator.cdata(node.value.load())
                stack.insert(i, (node, "end"))
        if action == "end":
            xmlgenerator.end_element()


def diff_tree2xml(xmlgenerator, root_node, required_attrs={}):
    stack = [(root_node, "start_diff")]
    while stack:
        node, action = stack.pop(0)
        if action == "start_diff":
            if isinstance(node, DiffNodeList):
                i = 0
                #print "list", node.name
                empty_common = True
                for obj in node.common_objects:
                    if not obj.is_empty():
                        empty_common = False
                        break
                if not empty_common:
                    stack.insert(i, ("COMMON", "start_xml"))
                    i += 1
                    for obj in node.common_objects:
                        stack.insert(i, (obj, "start_diff"))
                        i += 1
                #print node.missing_in_1
                #print node.missing_in_2
                if node.missing_in_1:
                    stack.insert(i, ("MISSING IN 1", "start_xml"))
                    i += 1
                    for obj in node.missing_in_1:
                        stack.insert(i, (obj, "start_xml"))
                        i += 1
                if node.missing_in_2:
                    stack.insert(i, ("MISSING IN 2", "start_xml"))
                    i += 1
                    for obj in node.missing_in_2:
                        stack.insert(i, (obj, "start_xml"))
                        i += 1
                #for x in stack:
                #    if isinstance(x[0], str):
                #        print x[1], x[0]
                #    else:
                #        print x[1], x[0].name


            elif isinstance(node, DiffNode):
                #print node.name
                if node._type != "attr":
                    if node.is_empty():
                        continue
                    attrs = {}
                    i = 0
                    no_content = True
                    for subnode in node.common_objects.itervalues():
                        #print "subnode", subnode.name
                        _name = subnode.name
                        _dname = "__diff__%s" % subnode.name
                        if (not isinstance(subnode, DiffNodeList) and
                           subnode._type == "attr"):
                            if subnode.differ:
                                attrs[_name] = subnode.value
                                attrs[_dname] = subnode.diff_value
                            if (node.name in required_attrs and
                               subnode.name in required_attrs[node.name]):
                                #print "required", _name,
                                attrs[_name] = subnode.value
                                attrs[_dname] = subnode.diff_value
                        else:
                            if (node.name in required_attrs and
                               subnode.name in required_attrs[node.name]):
                                stack.insert(i, (subnode, "start_xml"))
                            else:
                                stack.insert(i, (subnode, "start_diff"))
                            i += 1
                            no_content = False

                    for subnode in node.missing_in_1.itervalues():
                        _name = "__missing_in_1__%s" % subnode.name
                        if (not isinstance(subnode, NodeList) and
                           subnode._type == "attr"):
                            attrs[_name] = subnode.value
                        else:
                            stack.insert(i, (subnode, "start_xml"))
                            stack.insert(i, ("MISSING IN 1", "start_xml"))
                            i += 2
                            no_content = False

                    for subnode in node.missing_in_2.itervalues():
                        _name = "__missing_in_2__%s" % subnode.name
                        if (not isinstance(subnode, NodeList) and
                           subnode._type == "attr"):
                            attrs[_name] = subnode.value
                        else:
                            stack.insert(i, (subnode, "start_xml"))
                            stack.insert(i, ("MISSING IN 2", "start_xml"))
                            i += 2
                            no_content = False

                    no_content = node.value is None and no_content
                    #print node.name, no_content
                    xmlgenerator.start_element(node.name, attrs, no_content)
                    if node.differ:
                        if node.value:
                            xmlgenerator.comment("MISSING IN 1")
                            xmlgenerator.cdata(node.value.load())
                        if node.diff_value:
                            xmlgenerator.comment("MISSING IN 2")
                            xmlgenerator.cdata(node.diff_value.load())
                    stack.insert(i, (node, "end_diff"))
        elif action == "start_xml":
            if not isinstance(node, str):
                tree2xml(xmlgenerator, node)
            else:
                xmlgenerator.comment(node)
        elif action == "end_diff":
            xmlgenerator.end_element()
