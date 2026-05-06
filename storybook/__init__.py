import os

if os.getenv("USE_PYMYSQL", "true").lower() == "true":
    import pymysql
    pymysql.install_as_MySQLdb()
