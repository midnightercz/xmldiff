#!/bin/env python

import argparse
import os
# import sys
import tempfile

import parser
import saxxml
import utils
import xmlwriter


def make_arg_parser():
    ret = argparse.ArgumentParser(description="update info diff tool")
    ret.add_argument("source1", type=str, help="source filename 1")
    ret.add_argument("source2", type=str, help="source filename 2")
    ret.add_argument("--dest", type=str, help="result filename")
    ret.add_argument("--conf", type=str, help="configuration for diff",
                     required=True)
    return ret


def process_source(source):
    fname = None
    _buffer = utils.retrieve(source)
    (_, tmpfname) = tempfile.mkstemp()
    tmpf = open(tmpfname, "w")
    tmpf.write(_buffer.getvalue())
    tmpf.close()

    archive = utils.get_archive_type(tmpfname)
    if archive == "gzip":
        fname = utils.ungzip(tmpfname)
        os.remove(tmpfname)
    elif archive == "bzip":
        fname = utils.unbzip(tmpfname)
        os.remove(tmpfname)
    elif archive is False:
        fname = tmpfname
    return (fname, True)


def diff(source1, source2, dest, config):
    IDS = config["IDS"]
    REQUIRED_ATTRS = config["REQUIRED_ATTRS"]
    (fname1, need_cleanup1) = process_source(source1)
    (fname2, need_cleanup2) = process_source(source2)
    try:
        p = parser.Parser()
        parsed1 = p.parse_file(open(fname1))
        p = parser.Parser()
        parsed2 = p.parse_file(open(fname2))
        dest = open(dest, "w")
        diffed = parsed1.diff(parsed2, path="", ids=IDS,
                              required=REQUIRED_ATTRS)
        del parsed1, parsed2

        writer = xmlwriter.XMLWriter(dest, encoding="utf-8")
        writer.start_document()
        saxxml.diff_tree2xml(writer, diffed, required_attrs=REQUIRED_ATTRS)
        writer.end_document()

    except Exception:
        raise
    finally:
        if need_cleanup1:
            os.remove(fname1)
        if need_cleanup2:
            os.remove(fname2)

if __name__ == "__main__":
    ap = make_arg_parser()
    args = ap.parse_args()
    conf_mod = __import__("conf.%s" % args.conf, fromlist=[args.conf])
    diff(args.source1, args.source2, args.dest, conf_mod.conf)
