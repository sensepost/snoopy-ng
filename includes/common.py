import os
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert
from sqlalchemy import Column, String, MetaData
import hashlib
import glob

#Set path
snoopyPath=os.path.dirname(os.path.realpath(__file__))
os.chdir(snoopyPath)
os.chdir("..")

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

def get_tables():
    all_tables = []
    for plug in get_plugins():
        tbls = plug.get_tables()
        for tbl in tbls:
            all_tables.append(tbl)
    return all_tables

def create_tables(db):
        tbls = get_tables()
        metadata = MetaData(db)
        for tbl in tbls:
            tbl.metadata = metadata
            if not db.dialect.has_table(db.connect(), tbl.name):
                tbl.create()

@compiles(Insert)
def replace_string(insert, compiler, **kw):
    s = compiler.visit_insert(insert, **kw)
    s = s.replace("INSERT INTO", "REPLACE INTO")
    return s

salt="50f51d9fdcb6066433431eb8c15214b7"
def snoop_hash(value):
    return hashlib.sha256(str(value)+salt).hexdigest() 
