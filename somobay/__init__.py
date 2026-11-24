try:
    import pymysql

    # Fake mysqlclient version so Django accepts PyMySQL for django.db.backends.mysql.
    pymysql.version_info = (2, 2, 1, "final", 0)
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
