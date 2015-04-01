import os
import sys

sys.path.insert(0, os.path.realpath(os.path.realpath(__file__) + "/../../../"))

def application(environ, start_response):
    from includes.webserver import prep, app
    prep(environ['SNOOPY_DBMS'])
    return app(environ, start_response)
