# coding: utf-8
from __future__ import unicode_literals, division, print_function, absolute_import

from .codegen import CodeGenerator, get_col_doc


import argparse
import codecs
import sys

from sqlalchemy.engine import create_engine
from sqlalchemy.schema import MetaData


def cmd_main():
    parser = argparse.ArgumentParser(description='Generates SQLAlchemy model code from an existing database.')
    parser.add_argument('url', nargs='?', help='SQLAlchemy url to the database')
    parser.add_argument('--version', action='store_true', help="print the version number and exit")
    parser.add_argument('--schema', help='load tables from an alternate schema')
    parser.add_argument('--tables', help='tables to process (comma-separated, default: all)')
    parser.add_argument('--noviews', action='store_true', help="ignore views")
    parser.add_argument('--noindexes', action='store_true', help='ignore indexes')
    parser.add_argument('--noconstraints', action='store_true', help='ignore constraints')
    parser.add_argument('--nojoined', action='store_true', help="don't autodetect joined table inheritance")
    parser.add_argument('--noinflect', action='store_true', help="don't try to convert tables names to singular form")
    parser.add_argument('--noclasses', action='store_true', help="don't generate classes, only tables")
    parser.add_argument('--nocomments', action='store_true', help="don't add comments to columns")
    parser.add_argument('--outfile', help='file to write output to (default: stdout)')

    fix_args = None
    args = parser.parse_args(fix_args)
    if not args.url:
        print ('You must supply a url\n', file=sys.stderr)
        parser.print_help()
        return

    engine = create_engine(args.url)
    metadata = MetaData(engine)
    tables = args.tables.split(',') if args.tables else None
    metadata.reflect(engine, args.schema, not args.noviews, tables)

    outfile = codecs.open(args.outfile, 'w', encoding='utf-8') if args.outfile else sys.stdout
    generator = CodeGenerator(metadata, args.noindexes, args.noconstraints, args.nojoined, args.noinflect,
                              args.noclasses)

    db_comments_map = {} if args.nocomments else get_col_doc(engine)
    generator.render(outfile, db_comments_map)