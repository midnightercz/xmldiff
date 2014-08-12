import urllib2
import sys

import parser
import saxxml
import xmlwriter

# In this example we make diff between fedora 19 and fedora 20 comps file

# Download and store f20 comps file
f = open("f20-comps.xml", "w")
response = urllib2.urlopen("http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Fedora/x86_64/os/repodata/ac802acf81ab55a0eca1fe5d1222bd15b8fab45d302dfdf4e626716d374b6a64-Fedora-20-comps.xml")
f.write(response.read())
f.close()

# Same for f19 comps file
f = open("f19-comps.xml", "w")
response = urllib2.urlopen("http://dl.fedoraproject.org/pub/fedora/linux/releases/19/Fedora/x86_64/os/repodata/58d3d79e79810d9494d706bc4e1e6cfec685cb5c0b287cfe71804303ece26ee2-Fedora-19-comps.xml.gz")
f.write(response.read())
f.close()

# Make parsers and load data
p = parser.Parser()
parsed1 = p.parse_file(open("f20-comps.xml"))
p = parser.Parser()
parsed2 = p.parse_file(open("f19-comps.xml"))


# Comps files contains groups, categories and environments. We don't want
# compare whole structures of for example groups, but compare them only
# by their id sub element. So two groups with different structure but
# same id are considered as equal. So two groups with same id will be
# in COMMON part of diff output. But of course sub-parts of groups that are
# different will be outputed as MISSING IN 1 or MISSING IN 1 or DIFF.

# format of IDS is:
# "path.to.element": ["list", "of", "subelements", "forming", "together",
#                     "unique", "id"]

IDS = {".root.comps.group.group": ["id"],
       ".root.comps.group": ["id"],
       ".root.comps.category": ["id"],
       ".root.comps.category.category": ["id"],
       ".root.comps.environment": ["id"],
       ".root.comps.environment.environment": ["id"]}

# This thing make output more human friendly. Because xml output is containing
# only elements and attributes which are different. But of course you want
# to know at least id of group that contains different sub-elements.
# REQUIRED_ATTRS ensure you, that if specified objects are different at least
# at one pair attributes, output will contain also elements or attributes
# from first source which are specified in REQUIRED_ATTRS.

REQUIRED_ATTRS = {"group": ["id"],
                  "category": ["id"],
                  "environment": ["id"]}


# makes diff thing. Path parameter is needed because diff method is called
# recursively. So we start with empty path

diffed = parsed1.diff(parsed2, path="", ids=IDS, required=REQUIRED_ATTRS)

# Remove original structures, because they are changed and useless now.
# And also because this example and whole tool is memory green.

del parsed1, parsed2

writer = xmlwriter.XMLWriter(sys.stdout, encoding="utf-8")
writer.start_document()

# write output to stdout. In saxxml module is also method tree2xml
# rendering ordinary xml.
# So you can call - but not at this point becaused parsed1 is already deleted
# saxxml.tree2xml(writer, parsed1)
# to render xml from parsed structure

saxxml.diff_tree2xml(writer, diffed, required_attrs=REQUIRED_ATTRS)

writer.end_document()
