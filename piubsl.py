#!/usr/bin/python

import sys
import argparse
import textwrap
import sqlite3
import os
import re

def init_db( args ):

    try:
        os.unlink( args.dbfile )
    except:
        pass

    conn = sqlite3.connect( args.dbfile )

    c = conn.cursor()

    c.execute( """create table pkgs
         ( pkg_name VARCHAR( 120 ),
          pkg_cnt INT DEFAULT 1 )""" )

    c.execute( """create table symlinks
         ( sym_name VARCHAR( 120 ),
          sym_cnt INT DEFAULT 1 )""" )

    c.execute( """create table links
        ( symlink VARCHAR( 120 ),
          pkg VARCHAR( 120 ) )""" )

    conn.commit()
    c.close()

def parse_log_text( log_text ):

    log_split = log_text.split( "\n" )

    package = re.search( "Package: (.+)$", log_split[2] ).groups(1)[0]

    installed = list( { y.group(1) for y in 
                  [re.search( "^  ([^\s]+)\s+install$", x ) for x in log_split]
                    if y } )

    links = list( { y.group(1) for y in
                  [re.search( "^  ([^\s]+ -> [^\s]+)$", x ) for x in log_split]
                    if y } )

    print package

    return( (package, installed, links) )

def add_entry( connector, (package, installed, links) ):

    connector.execute( """select pkg from links
                  where pkg = ?""", (package,) )

    for row in connector:
        raise( BaseException )

    for link in links:
        connector.execute( """insert into links ( pkg, symlink )
                          values ( ?, ? )""", (package, link) )

        # increment the package count
        connector.execute( """select pkg_cnt from pkgs 
                              where pkg_name = ?""", (package,) )
        row = connector.fetchone()

        if row:
            connector.execute( """update pkgs set pkg_cnt = ?
                               where pkg_name = ?""", ( row[0]+1, package ) )
        else:
            connector.execute( """insert into pkgs ( pkg_name )
                values( ? )""", (package,) )

        # increment the symlink count
        connector.execute( """select sym_cnt from symlinks 
                              where sym_name = ?""", (link,) )
        row = connector.fetchone()

        if row:
            connector.execute( """update symlinks set sym_cnt = ?
                               where sym_name = ?""", ( row[0]+1, link ) )
        else:
            connector.execute( """insert into symlinks ( sym_name )
                values( ? )""", (link,) )


def add_log( args ):

    logfiles = args.logfiles

    conn = sqlite3.connect( args.dbfile )
    c = conn.cursor()

    if len( logfiles ) == 0:

        logtext = sys.stdin.read()
        add_entry( c, parse_log_text( logtext ) )
    else:
        for logfile in logfiles:
            print logfile
            f = open( logfile, 'r' )
            logtext = f.read()
            f.close()

            add_entry( c, parse_log_text( logtext ) )
            conn.commit()

    conn.commit()
    c.close()
    conn.close()

def link_report( args ):

    conn = sqlite3.connect( args.dbfile )
    c = conn.cursor()

    c.execute( """select sym_cnt, sym_name from symlinks
                  order by sym_cnt desc""" )

    print " count broken symlink"
    for row in c:
        count, link = row
        print " %5d %s" % ( count, link )

def link_detail( args ):
    pass

def main( args ):

    parser = argparse.ArgumentParser( 
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
            Analyze Piuparts broken symlinks

            Using log files available under e.g.

                http://piuparts.debian.org/sid/broken_symlinks_issue.html

            analyze the frequency and source of "Broken symlink" warnings
            '''),
        epilog = "use '%(prog)s <cmd> -h for command-specific help\n" )

    subparsers = parser.add_subparsers( help='command help' )

    # the 'initdb' command
    parser_initdb = subparsers.add_parser( 'initdb', 
            help='initialize the database file' ,
            description = 
              'Initialize the sqlite database file to contain symlink stats' )
    parser_initdb.add_argument( 'dbfile', help='the name of the database file' )
    parser_initdb.set_defaults( func=init_db )

    # the 'addlog' command
    parser_addlog = subparsers.add_parser( 'addlog', 
            help='add a log file to the database',
            description = 'parse a single Piuparts log file into the database' )
    parser_addlog.add_argument( 'dbfile', help='the name of the database file' )
    parser_addlog.add_argument( 'logfiles', nargs='*',
               help='the name of the logfile (omit for a single file to stdin)' )
    parser_addlog.set_defaults( func=add_log )

    # the 'linkreport' command
    parser_linkrep = subparsers.add_parser( 'linkreport',
            help='print a summary of broken symlinks found',
            description = 
              'Print a report of broken symlinks found in the log files' )
    parser_linkrep.add_argument( 'dbfile', 
            help='the name of the database file' )
    parser_linkrep.set_defaults( func=link_report )

    # the 'linkdetail' command
    parser_linkdetail = subparsers.add_parser( 'linkdetail',
            help='print a summary of packages related to a broken link',
            description = 
              'Print a package summary for a single broken symlink' )
    parser_linkdetail.add_argument( 'link',
            help='the link, as output by \'linkreport\'' )
    parser_linkdetail.set_defaults( func=link_detail )

    parser.add_argument( '-v', dest='verbose', action='store_true',
            help='verbose output' )


    parsed_args = parser.parse_args( args )

    parsed_args.func(parsed_args)

if __name__ == "__main__":
    main( sys.argv[1:] )
