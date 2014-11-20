import argparse
import os.path
import utils

import parser
import xmldiff

COMPARABLE_TYPES = ["primary", "other", "filelists", "group", "updateinfo"]
COMPARABLE_TYPES_ALIAS = {"group": "comps"}


def make_arg_parser():
    ret = argparse.ArgumentParser(description="update info diff tool")
    ret.add_argument("repo_dir1", type=str, help="source filename 1")
    ret.add_argument("repo_dir2", type=str, help="source filename 2")
    ret.add_argument("--destdir", type=str, help="result filename",
                     required=True)
    return ret


if __name__ == "__main__":
    ap = make_arg_parser()
    args = ap.parse_args()

    fst_repo_files = {}
    snd_repo_files = {}
    for target, source in zip((fst_repo_files, snd_repo_files),
                              (args.repo_dir1, args.repo_dir2)):
        p = parser.Parser()
        strbuffer = utils.retrieve(os.path.join(source,
                                                "repodata", "repomd.xml"))
        parsed = p.parse_str(strbuffer.getvalue())
        for data in parsed.get("repomd.data").objects:
            url = data.get("location.href")
            _type = data.get("type")
            target[_type] = os.path.join(source, url)

    missing_in_1 = set(fst_repo_files) - set(snd_repo_files)
    missing_in_2 = set(snd_repo_files) - set(fst_repo_files)
    print "missing types in 1 repo %s" % ",".join(missing_in_1)
    print "missing types in 2 repo %s" % ",".join(missing_in_2)
    common = set(fst_repo_files) & set(snd_repo_files)
    if not os.path.exists(args.destdir):
        os.mkdir(args.destdir)

    for _type in common:
        if _type not in COMPARABLE_TYPES:
            continue
        _type_alias = _type
        print "comparing: %s" % _type_alias
        if _type in COMPARABLE_TYPES_ALIAS:
            _type_alias = COMPARABLE_TYPES_ALIAS[_type]
        conf_mod = __import__("conf.%s" % _type_alias, fromlist=[_type_alias])
        xmldiff.diff(fst_repo_files[_type], snd_repo_files[_type],
                     os.path.join(args.destdir, "%s.xml.diff" % _type),
                     conf_mod.conf)
