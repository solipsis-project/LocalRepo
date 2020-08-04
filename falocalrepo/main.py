from datetime import datetime
from os import getcwd
from os.path import abspath
from os.path import join as path_join
from sys import argv

from faapi import FAAPI

from .console import main_console
from .database import Connection
from .database import connect_database
from .database import make_database
from .interactive import main_menu
from .settings import setting_write


def main():
    # Get current work directory
    workdir: str = abspath(getcwd())

    # Initialise api and database
    api: FAAPI = FAAPI()
    db: Connection = connect_database(path_join(workdir, "FA.db"))

    # Prepare database
    make_database(db)
    setting_write(db, "LASTSTART", str(datetime.now().timestamp()))

    # Run main program
    if argv[1:] and argv[1] == "interactive":
        main_menu(workdir, api, db)
    else:
        main_console(workdir, api, db, argv[1:])

    # Close database
    db.commit()
    db.close()
