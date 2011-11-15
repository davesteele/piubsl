#!/usr/bin/python -tt

import unittest
import re
import os.path
import time
import sqlite3

import sys
sys.path.append( '.' )

import piubsl

class Args():
    pass

dbfl = "testdb"

class TestBSL( unittest.TestCase ):

    def setUp( self ):
        
        self.args = Args()

        self.args.dbfile = dbfl

        try:
            os.unlink( dbfl )
        except:
            pass

        fp = open( "data/openbox_3.5.0-2.log.txt", 'r' )
        self.log_text = fp.read()
        fp.close()

    def tearDown( self ):
        try:
            os.unlink( dbfl )
        except:
            pass

    def test_init_db( self ):
        self.assertTrue( not os.path.isfile( dbfl ) )
        piubsl.init_db( self.args )
        self.assertTrue(  os.path.isfile( dbfl ) )

        ctm = os.path.getctime( dbfl )
        time.sleep( 0.001 )
        piubsl.init_db( self.args )
        self.assertNotEqual( ctm, os.path.getctime( dbfl ) )

    def test_parse_log_text( self ):
        (package, installed, links ) = piubsl.parse_log_text( self.log_text )

        self.assertEquals( package,  "openbox" )

        self.assertEquals( type( installed ), type ([]) )
        self.assertEquals( len( installed ), 117 )
        self.assertTrue( 'apt' in installed )

        self.assertEquals( type( links ), type ([]) )
        self.assertEquals( len( links ), 2 )
        self.assertTrue( "/etc/motd -> /var/run/motd" in links )
        self.assertTrue( "/etc/fonts/conf.d/30-defoma.conf -> /var/lib/defoma/fontconfig.d/fonts.conf" in links )

    def test_add_entry( self ):
        piubsl.init_db( self.args )

        conn = sqlite3.connect( dbfl )
        c = conn.cursor()

        piubsl.add_entry( c, ("foo", [], [ "sym1", "sym2" ]) )
        conn.commit()
        piubsl.add_entry( c, ("bar", [], [ "sym1", "sym3" ]) )
        conn.commit()

        with self.assertRaises( BaseException ):
            piubsl.add_entry( c, ("bar", [], [ "sym1", "sym3" ]) )
            conn.commit()


if __name__ == "__main__":
    unittest.main()

