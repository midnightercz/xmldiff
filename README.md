xmldiff
=======

experimental tool for diff two xml files

Requirements to run
-------------------

- python2 > 2.6

Notes
-----

See examples for more information

Repodiff
========

### Run:

    python repodiff.py --destdir diff_dir repo_path1 repo_path2

### Example:

    python repodiff.py --dest diff_dir http://dl.fedoraproject.org/pub/fedora/linux/releases/19/Fedora/x86_64/os/ http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Fedora/x86_64/os/

    python repodiff.py --dest diff_dir file://local_dir_with_repodata1 file://local_dir_with_repodata2

Diff specific repodata files
----------------------------

### Run:

    python repodiff.py --dest out.xml.diff --conf <type> <file1> <file2>

### Example:

    python repodiff.py --dest out.xml.diff --conf comps http://dl.fedoraproject.org/pub/fedora/linux/releases/19/Fedora/x86_64/os/repodata/bf4e62e367e9b80e4f7c75092ef729f69d5d8e2d3eadd3c852ba6c5eb7a85353-Fedora-19-comps.xml http://dl.fedoraproject.org/pub/fedora/linux/releases/20/Fedora/x86_64/os/repodata/ac802acf81ab55a0eca1fe5d1222bd15b8fab45d302dfdf4e626716d374b6a64-Fedora-20-comps.xml

