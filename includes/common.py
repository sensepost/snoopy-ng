from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert

@compiles(Insert)
def replace_string(insert, compiler, **kw):
    s = compiler.visit_insert(insert, **kw)
    s = s.replace("INSERT INTO", "REPLACE INTO")
    return s
