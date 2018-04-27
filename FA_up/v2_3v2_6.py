import sqlite3
import os
import sys
from math import log10

def temp_new():
    print('Creating temporary database ... ', end='', flush=True)
    if os.path.isfile('FA.v2_3.db'): os.remove('FA.v2_3.db')
    db_new = sqlite3.connect('FA.v2_3.db')
    print('Done')

    db_old = sqlite3.connect('FA.db')
    db_old.execute("ATTACH DATABASE 'FA.v2_3.db' AS db_new")

    print('Copying INFOS data ... ', end='', flush=True)
    db_old.execute("CREATE TABLE IF NOT EXISTS db_new.INFOS AS SELECT * FROM main.INFOS")
    db_new.execute(f"UPDATE infos SET value = '2.6' WHERE field = 'VERSION'")
    db_old.commit()
    db_new.commit()
    print('Done')

    print('Grabbing USERS data .. ', end='', flush=True)
    usrs_old = db_old.execute("SELECT * FROM users ORDER BY name ASC")
    usrs_old = usrs_old.fetchall()
    print('Done')

    print('Grabbing SUBMISSIONS data .. ', end='', flush=True)
    subs_old = db_old.execute("SELECT * FROM submissions ORDER BY id ASC")
    subs_old = subs_old.fetchall()
    db_old.close()
    print('Done')

    print('Creating new USERS table ... ', end='', flush=True)
    db_new.execute('''CREATE TABLE IF NOT EXISTS USERS
        (USER TEXT UNIQUE PRIMARY KEY NOT NULL,
        USERFULL TEXT NOT NULL,
        FOLDERS TEXT NOT NULL,
        GALLERY TEXT,
        SCRAPS TEXT,
        FAVORITES TEXT,
        EXTRAS TEXT);''')
    db_new.commit()
    print('Done')

    print('Creating new SUBMISSIONS table ... ', end='', flush=True)
    db.execute('''CREATE TABLE IF NOT EXISTS SUBMISSIONS
        (ID INT UNIQUE PRIMARY KEY NOT NULL,
        AUTHOR TEXT NOT NULL,
        AUTHORURL TEXT NOT NULL,
        TITLE TEXT,
        UDATE CHAR(10) NOT NULL,
        DESCRIPTION TEXT,
        TAGS TEXT,
        CATEGORY TEXT,
        SPECIES TEXT,
        GENDER TEXT,
        RATING TEXT,
        FILELINK TEXT,
        FILENAME TEXT,
        LOCATION TEXT NOT NULL,
        SERVER INT);''')
    db_new.commit()
    print('Done')

    print('Editing SUBMISSIONS data to add new values ... ', end='', flush=True)
    subs_new = [s[0:4] + [None] + s[4:] for s in subs_old]
    print('Done')

    print('Copying USERS data ... ', end='', flush=True)
    for u in usrs_old:
        db_new.execute(f'''INSERT INTO USERS
            (USER,USERFULL,FOLDERS,GALLERY,SCRAPS,FAVORITES,EXTRAS)
            VALUES (?, ?, ?, ?, ?, ?, ?)''', u)
    db_new.commit()
    print('Done')

    print('Adding SUBMISSIONS data ... ', end='', flush=True)
    for s in subs_new:
        db_new.execute(f'''INSERT INTO SUBMISSIONS
            (ID,AUTHOR,AUTHORURL,TITLE,UDATE,DESCRIPTION,TAGS,CATEGORY,SPECIES,GENDER,RATING,FILELINK,FILENAME,LOCATION,SERVER)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', s)
    db_new.commit()
    print('Done')

    subs_new = [[s[0], 0, s[13]] for s in subs_new]

    db_new.close()
    return subs_new

def temp_import():
    print('Opening temporary database ... ', end='', flush=True)
    db_new = sqlite3.connect('FA.v2v2_3.db')
    print('Done')

    print('Checking temporary database ... ', end='', flush=True)
    infos = bool(db_new.execute('SELECT EXISTS(SELECT name FROM sqlite_master WHERE type = "table" AND name = "INFOS")'))
    users = bool(db_new.execute('SELECT EXISTS(SELECT name FROM sqlite_master WHERE type = "table" AND name = "USERS")'))
    subs = bool(db_new.execute('SELECT EXISTS(SELECT name FROM sqlite_master WHERE type = "table" AND name = "SUBMISSIONS")'))
    if not(infos == users == subs == True):
        print('Tables error')
        return False

    db_old = sqlite3.connect('FA.db')
    subs_old = db_old.execute('SELECT id FROM submissions').fetchall()
    subs_new = db_new.execute('SELECT id FROM submissions').fetchall()
    if len(subs_new) != len(subs_old):
        print('Submissions error')
        return False

    print('Done')

    print('Importing temporary data ... ', end='', flush=True)
    subs_new1 = db_new.execute('SELECT id, location FROM submissions WHERE description != NULL').fetchall()
    subs_new2 = db_new.execute('SELECT id, location FROM submissions WHERE description == NULL').fetchall()
    subs_new1 = [[s[0], 1, s[1]] for s in subs_new1]
    subs_new2 = [[s[0], 0, s[1]] for s in subs_new2]
    subs_new = subs_new1 + subs_new2

    db_old.close()
    db_new.close()
    return subs_new

def db_upgrade_v2v2_3():
    print('The database needs to be upgraded to version 2.6')
    print('This procedure is required to continue using the program')
    print('The current database will be saved in a backup file named FA.v2_3.db')
    print('This procedure can take a long time, do you want to continue? ', end='', flush=True)
    c = ''
    while c not in ('y','n'):
        c = readkeys.getkey().lower()
        if c in ('\x03', '\x04'):
            print('n')
            sys.exit(130)
    print(c)
    if c == 'n':
        sys.exit(0)

    print()

    if os.path.isfile('FA.v2v2_3.db'):
        subs_new = temp_import()
        if not subs_new:
            subs_new = temp_new()
    else:
        subs_new = temp_new()
    db_new = sqlite3.connect('FA.v2v2_3.db')

    print('Saving DESCRIPTIONS ... ', end='', flush=True)
    N = len(subs_new)
    Nl = int(log10(N)+1)
    Ni = 0
    for s in subs_new:
        Ni += 1
        print(f'{Ni:0>{Nl}}/{N}', end='', flush=True)
        if s[1]:
            continue
        desc =  'FA.files/' + s[2] + '/description.html'

        if not os.path.isfile(desc):
            desc = ''
        else:
            with open(desc, 'r') as f:
                desc = '\n'.join(f.readlines())

        db_new.execute(f"UPDATE submissions SET description = ? WHERE id = {s[0]}", (desc,))
    db_new.commit()
