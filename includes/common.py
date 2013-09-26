import os
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert
from sqlalchemy import Column, String
import hashlib
import glob

def get_plugin_names():
    return [ os.path.basename(f)[:-3]
        for f in glob.glob("./plugins/*.py")
            if not os.path.basename(f).startswith('__') ]

def get_plugins():
    plugins = []
    for plug in get_plugin_names():
        plug = "plugins." + plug
        m = __import__(plug, fromlist="Snoop").Snoop
        plugins.append(m)
    return plugins


@compiles(Insert)
def replace_string(insert, compiler, **kw):
    s = compiler.visit_insert(insert, **kw)
    s = s.replace("INSERT INTO", "REPLACE INTO")
    return s

salt="50f51d9fdcb6066433431eb8c15214b7"
def snoop_hash(value):
    return hashlib.sha256(str(value)+salt).hexdigest() 
