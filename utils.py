import bz2
import gzip
import tempfile
from StringIO import StringIO

import pycurl


def get_archive_type(fname):
    fp = open(fname, "rb")
    head = fp.read(3)
    fp.close()
    if head == "\x1f\x8b\x08":
        return "gzip"
    elif head == "\x42\x5A\x68":
        return "bzip"
    else:
        return False


def ungzip(fname):
    tmp_fname = tempfile.mkstemp()[1]
    tmpf = open(tmp_fname, "w")
    gz = gzip.open(fname)
    tmpf.write(gz.read())
    tmpf.close()
    return tmp_fname


def unbzip(fname):
    tmp_fname = tempfile.mkstemp()[1]
    tmpf = open(tmp_fname, "w")
    bz = bz2.open(fname)
    tmpf.write(bz.read())
    tmpf.close()
    return tmp_fname


def retrieve(uri):
    _buffer = StringIO()
    c = pycurl.Curl()
    #if uri.startswith("file://"):
    if isinstance(uri, unicode):
        uri = uri.encode("utf-8")
    c.setopt(c.URL, uri)
    #elif uri.startswith("http://") or uri.startswith("https://"):
    #c.setopt(c.FILE, uri)
    c.setopt(c.WRITEFUNCTION, _buffer.write)
    c.setopt(c.FOLLOWLOCATION, True)
    c.perform()
    c.close()
    return _buffer
