try:
    import pymysql

    # Django 3.1 requires mysqlclient >= 1.4.0 when using django.db.backends.mysql.
    pymysql.version_info = (1, 4, 2, "final", 0)
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
