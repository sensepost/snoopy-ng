from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert
import hashlib

@compiles(Insert)
def replace_string(insert, compiler, **kw):
    s = compiler.visit_insert(insert, **kw)
    s = s.replace("INSERT INTO", "REPLACE INTO")
    return s

salt="50f51d9fdcb6066433431eb8c15214b7"
def snoop_hash(value):
    return hashlib.sha256(str(value)+salt).hexdigest() 
