import xml.dom.minidom

from path2tree import Node, NodeList, DiffNode, DiffNodeList


def tree2xml(root_node, doc=None, _parent_elem=None):
    return_list = False
    if isinstance(root_node, NodeList):
        return_list = True
    stack = [(_parent_elem, root_node)]
    elems = []
    while stack:
        parent_elem, current_node = stack.pop(0)
        if isinstance(current_node, NodeList):
            i = 0
            for obj in current_node.objects:
                stack.insert(i, (parent_elem, obj))
                i += 1
        else:
            if current_node._type != "attr":  # value node, not attribute
                current_elem = doc.createElement(current_node.name)
                elems.append(current_elem)
                if parent_elem:
                    parent_elem.appendChild(current_elem)
                if current_node.value:
                    cnode = doc.createTextNode(current_node.value)
                    current_elem.appendChild(cnode)

                for subnode in current_node.objects.itervalues():
                    stack.insert(0, (current_elem, subnode))

            else:
                parent_elem.setAttribute(current_node.name, current_node.value)
    if not return_list and not _parent_elem:
        return elems[0]
    else:
        return elems


def diff_tree2xml(root_node, doc=None, root_parent=None, allow_empty=False,
                  required_attrs={}):
    return_list = False
    if isinstance(root_node, DiffNodeList):
        return_list = True
    stack = [(root_parent, root_node, allow_empty)]
    elems = []
    while stack:
        parent_elem, current_node, allow_empty = stack.pop(0)
        #print "current node", current_node.name, current_node.value
        if isinstance(current_node, DiffNodeList):
            #if current_node.common_objects:
            #    parent_elem.appendChild(doc.createComment(" - COMMON - "))
            for obj in current_node.common_objects:
                ret = diff_tree2xml(obj,
                                    doc=doc,
                                    required_attrs=required_attrs)
                if (isinstance(ret, xml.dom.minidom.Comment)
                   or ret.hasAttributes() or ret.hasChildNodes()):
                    parent_elem.appendChild(ret)

            if parent_elem.hasAttributes() or parent_elem.hasChildNodes():
                parent_elem.insertBefore(doc.createComment(" - COMMON - "),
                                         parent_elem.firstChild)

            if current_node.missing_in_1:
                parent_elem.appendChild(doc.createComment(
                    " - MISSING IN 1"))
            for obj in current_node.missing_in_1:
                ret = tree2xml(obj, doc=doc)
                parent_elem.appendChild(ret)

            if current_node.missing_in_2:
                parent_elem.appendChild(doc.createComment(
                    " - MISSING IN 2"))
            for obj in current_node.missing_in_2:
                ret = tree2xml(obj, doc=doc)
                parent_elem.appendChild(ret)

        elif isinstance(current_node, DiffNode):
            #print "current node", current_node.name, current_node.value, current_node.diff_value
            if current_node._type != "attr":
                current_elem = doc.createElement(current_node.name)
                elems.append(current_elem)

                for subnode in current_node.common_objects.itervalues():
                    ret = diff_tree2xml(subnode, doc=doc,
                                        root_parent=current_elem,
                                        required_attrs=required_attrs)
                    if isinstance(ret, list):
                        for el in ret:
                            current_elem.appendChild(el)
                    elif (isinstance(ret, xml.dom.minidom.Comment)
                          or ret.hasAttributes()
                          or ret.hasChildNodes()):
                        current_elem.appendChild(ret)
                i = 0
                if current_node.missing_in_1:
                    current_elem.appendChild(doc.createComment(
                        " - MISSING IN 1 - "))
                    i = 1
                for subnode in current_node.missing_in_1.itervalues():
                    #print "missing in 1", subnode.name
                    if subnode._type == "attr":
                        subnode.name = "__missing_in_1__%s" % subnode.name
                    ret = tree2xml(subnode, _parent_elem=current_elem, doc=doc)
                    i += 1
                if current_node.missing_in_2:
                    current_elem.appendChild(doc.createComment(
                        " - MISSING IN 2 - "))
                    i += 1
                #print "missing in 2", current_node.missing_in_2
                for subnode in current_node.missing_in_2.itervalues():
                    #print "subnode", subnode.name
                    #print "missing in 2", subnode.name
                    if not (isinstance(subnode, DiffNodeList) and
                            subnode._type == "attr"):
                        subnode.name = "__missing_in_2__%s" % subnode.name
                    ret = tree2xml(subnode, _parent_elem=current_elem, doc=doc)
                    i += 1

                if ((current_elem.hasAttributes()
                   or current_elem.hasChildNodes())
                   and current_node.name in required_attrs):
                    for subnode_name in required_attrs[current_node.name]:
                        if subnode_name not in current_node.common_objects:
                            continue
                        subnode = current_node.common_objects[subnode_name]
                        ret = tree2xml(subnode.original_1,
                                       _parent_elem=current_elem,
                                       doc=doc)
                        if not ret:
                            continue
                        first_child = current_elem.firstChild
                        if first_child:
                            current_elem.insertBefore(ret[0], first_child)
                        else:
                            current_elem.appendChild(ret[0])
                if current_node.diff_value:
                    current_elem.appendChild(doc.createComment(
                        " - MISSING IN 1 - "))
                    cnode = doc.createTextNode(current_node.value)
                    current_elem.appendChild(cnode)
                    current_elem.appendChild(doc.createComment(
                        " - MISSING IN 2 - "))
                    cnode = doc.createTextNode(current_node.diff_value)
                    current_elem.appendChild(cnode)
                if parent_elem:
                    if (isinstance(current_elem, xml.dom.minidom.Comment)
                       or current_elem.hasAttributes()
                       or current_elem.hasChildNodes()
                       or allow_empty):
                        parent_elem.appendChild(current_elem)
            else:
                parent_elem.setAttribute(current_node.name, current_node.value)
                parent_elem.setAttribute("__diff__%s" % current_node.name,
                                         current_node.diff_value)

    if not return_list:
        if elems:
            return elems[0]
        else:
            return []
    else:
        return elems
