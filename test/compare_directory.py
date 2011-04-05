#!/usr/bin/env python
from __future__ import division

"""compare_directory.py: compare two directories, using regexes

XXX: want to keep track of all files in new directory
"""

__version__ = "$Revision$"

## Copyright 2011 Michael M. Hoffman <mmh1@uw.edu>

import filecmp
from os import walk
from re import compile as re_compile, escape
import sys

from path import path

from segway._util import maybe_gzip_open

def get_dir_filenames(dirname):
    for dirbasename, dirnames, filenames in walk(dirname):
        dirbasepath = path(dirbasename)
        relative_dirbasename = dirbasename.partition(dirname)[2]

        if relative_dirbasename.startswith("/"):
            relative_dirbasename = relative_dirbasename[1:]

        relative_dirpath = path(relative_dirbasename)

        try:
            dirnames.remove(".svn")
        except ValueError:
            pass

        for filename in filenames:
            filename_relative = str(relative_dirpath / filename)
            # not really absolute, but more so than relative
            filename_absolute = str(dirbasepath / filename)
            yield filename_relative, filename_absolute

# regular expression unescape
re_unescape = re_compile(r"\(%.*?%\)")
def make_regex(text):
    """
    make regex, escaping things that aren't with (% %)
    """
    spans = [match.span() for match in re_unescape.finditer(text)]

    res = ["^"]
    last_end = 0
    for start, end in spans:
        res.append(escape(text[last_end:start]))
        res.append(text[start+2:end-2]) # eliminate (% and %)
        last_end = end
    res.extend([escape(text[last_end:]), "$"])

    return re_compile("".join(res))

def compare_file(template_filename, query_filename):
    # quick comparison without regexes
    if filecmp.cmp(template_filename, query_filename, shallow=False):
        return True # files are identical, skip slow regex stuff

    with maybe_gzip_open(template_filename) as template_file:
        re_template = make_regex(template_file.read())

    with maybe_gzip_open(query_filename) as query_file:
        match = re_template.match(query_file.read())

    return bool(match)

def compare_directory(template_dirname, query_dirname):
    res = 0
    query_filenames = dict(get_dir_filenames(query_dirname))

    template_filenames = get_dir_filenames(template_dirname)
    for template_filename_relative, template_filename in template_filenames:
        re_template_filename_relative = make_regex(template_filename_relative)

        for query_filename_relative, query_filename in query_filenames.iteritems():
            if re_template_filename_relative.match(query_filename_relative):
                del query_filenames[query_filename_relative]
                if not compare_file(template_filename, query_filename):
                    print >>sys.stderr, "%s and %s differ" % (template_filename, query_filename)
                    res = 1

                break
        else:
            print >>sys.stderr, "query directory missing %s" % template_filename
            return 1

    return res

def parse_options(args):
    from optparse import OptionParser

    usage = "%prog [OPTION]... TEMPLATEDIR QUERYDIR"
    version = "%%prog %s" % __version__
    parser = OptionParser(usage=usage, version=version)

    options, args = parser.parse_args(args)

    if not len(args) == 2:
        parser.error("incorrect number of arguments")

    return options, args

def main(args=sys.argv[1:]):
    options, args = parse_options(args)

    return compare_directory(*args)

if __name__ == "__main__":
    sys.exit(main())
