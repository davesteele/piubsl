#!/usr/bin/python

import sys
import re
import urllib
import os

relurls = [ x.group(1) for x in 
               [ re.search( "href=.([^']+log)'", y ) for y in sys.stdin.readlines() ]
               if x ]

urls = [ "http://piuparts.debian.org" + x for x in relurls ]

cmds = [ "echo " + x.split( "/" )[-1] + "\ncurl " + x + " > logs/" + x.split( "/" )[-1] for x in urls ]

for url in urls:
    pkg = url.split( "/" )[-1]

    print pkg

    if not os.path.isfile( "logs/%s" % pkg ):
        f = urllib.urlopen( url )
        logtext = f.read()
        f.close()

        out = open( "logs/%s" % pkg, 'w' )
        out.write( logtext )
        out.close()




