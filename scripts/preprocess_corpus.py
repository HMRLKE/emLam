#!/usr/bin/env python3
"""
Preprocesses the specified corpus. Converters should be put into the
emLam.corpus package. Currently, converters exist for the Szeged Treebank,
Webcorpus and MNSZ2.
"""

from __future__ import absolute_import, division, print_function
from argparse import ArgumentParser
from functools import partial
import os
import os.path as op

from emLam.corpus import get_all_corpora
from emLam.utils import run_function


def parse_arguments():
    parser = ArgumentParser(
        description='Preprocesses the specified corpus.')
    parser.add_argument('--source-dir', '-s', required=True,
                        help='the source directory.')
    parser.add_argument('--target-dir', '-t', required=True,
                        help='the target directory.')
    parser.add_argument('--processes', '-p', type=int, default=1,
                        help='the number of files to process parallelly.')
    subparsers = parser.add_subparsers(
        title='Corpus selection',
        description='This section lists the corpora processor available for '
                    'selection. For help on a specific corpus, call the '
                    'script with the `<corp> -h` arguments.',
        dest='corpus', help='the corpora processors available.')
    corpora = get_all_corpora()
    for _, corpus_class in sorted(corpora.items()):
        corpus_class.parser(subparsers)

    args = parser.parse_args()
    print(args)
    if args.source_dir == args.target_dir:
        parser.error('Source and target directories must differ.')
    args.corpus = corpora[args.corpus].instantiate(**args.__dict__)

    return args


def walk_non_hidden(directory):
    """Walks directory as os.walk, skipping hidden files and directories."""
    def delete_hidden(lst):
        for i in range(len(lst) - 1, -1, -1):
            if lst[i][0] == '.':
                del lst[i]

    for tup in os.walk(directory):
        dirpath, dirnames, filenames = tup
        delete_hidden(dirnames)
        delete_hidden(filenames)
        yield tup


def source_target_file_list(source_dir, target_dir):
    source_dir = op.abspath(source_dir)
    target_dir = op.abspath(target_dir)
    source_files = [op.abspath(op.join(d, f))
                    for d, _, fs in walk_non_hidden(source_dir) for f in fs]
    target_files = []
    for sf in source_files:
        sf_rel = sf[len(source_dir):].lstrip(os.sep)
        tf = op.join(target_dir, sf_rel)
        td = op.dirname(tf)
        if not op.isdir(td):
            os.makedirs(td)
        target_files.append(tf)
    return zip(source_files, target_files)


def process_file(source_target_files, preprocessor):
    preprocessor.preprocess_files(*source_target_files)


def main():
    args = parse_arguments()
    os.nice(20)  # Play nice

    source_target_files = source_target_file_list(args.source_dir, args.target_dir)

    run_function(partial(process_file, preprocessor=args.corpus),
                 source_target_files, args.processes)


if __name__ == '__main__':
    main()