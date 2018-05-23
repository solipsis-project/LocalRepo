import requests, cfscrape, json, bs4
import os, sys, time
import re
import sqlite3
import PythonRead as readkeys
import FA_db as fadb
import FA_tools as fatl
import FA_var as favar
from .FA_DLSUB import dl_sub, str_clean
from .cookies import cookies_error

section_full = {
    'g' : 'gallery',
    's' : 'scraps',
    'f' : 'favorites',
    'e' : 'extra (partial)',
    'E' : 'extra (full)'
    }
section_db = {
    'g' : 'GALLERY',
    's' : 'SCRAPS',
    'f' : 'FAVORITES',
    'e' : 'EXTRAS',
    'E' : 'EXTRAS'
    }

def ping(url):
    fatl.log(f'PING -> url:{url}')
    try:
        requests.get(url, stream=True)
        fatl.log(f'PING -> OK')
        return True
    except:
        fatl.log(f'PING -> NO')
        return False

def session_make():
    fatl.log('SESSION MAKE')
    Session = cfscrape.create_scraper()
    cookies_file = favar.cookies_file

    for name in ('FA.cookies'):
        if os.path.isfile(name) and not os.path.isfile(cookies_file):
            fatl.log(f'SESSION MAKE -> cookies rename \"{name}\" to \"{cookies_file}\"')
            os.rename(name, cookies_file)
            break

    try:
        fatl.log('SESSION MAKE -> load cookies file')
        with open(cookies_file) as f:
            cookies = json.load(f)
    except FileNotFoundError:
        raise
    except:
        raise

    fatl.log('SESSION MAKE -> load cookies in Session')
    for cookie in cookies: Session.cookies.set(cookie['name'], cookie['value'])

    return Session

def check_cookies(Session):
    fatl.log('COOKIES -> check')
    check_r = Session.get('https://www.furaffinity.net/controls/settings/')
    check_p = bs4.BeautifulSoup(check_r.text, 'lxml')

    if check_p.find('a', id='my-username') is None:
        fatl.log('COOKIES -> check:False')
        return False
    else:
        fatl.log('COOKIES -> check:True')
        return True

def session(Session=None):
    fatl.log('SESSION')
    print('Checking connection ... ', end='', flush=True)
    if ping('http://www.furaffinity.net'):
        print('Done')
    else:
        print('Failed')
        fatl.log('SESSION -> fail')
        return False

    if not Session:
        print('Creating session & adding cookies ... ', end='', flush=True)
        try:
            Session = session_make()
            print('Done')
        except FileNotFoundError:
            print('Failed - Missing Cookies File')
            fatl.log('SESSION -> fail')
            return False
        except:
            print('Failed - Unknown Error')
            fatl.log('SESSION -> fail')
            return False


        print('Checking cookies & bypassing cloudflare ... ', end='', flush=True)
        if check_cookies(Session):
            print('Done')
        else:
            print('Failed')
            fatl.log('SESSION -> fail')
            cookies_error()
            return False

    fatl.log('SESSION -> success')
    return Session

def check_page(Session, url):
    fatl.log(f'CHECK PAGE -> url:{url}')
    page_r = Session.get('https://www.furaffinity.net/'+url)
    page_t = bs4.BeautifulSoup(page_r.text, 'lxml').title.string

    if page_t == 'System Error':
        fatl.log(f'CHECK PAGE -> fail')
        return False
    elif page_t == 'Account disabled. -- Fur Affinity [dot] net':
        fatl.log(f'CHECK PAGE -> fail')
        return False
    elif page_r.status_code == 404:
        fatl.log(f'CHECK PAGE -> fail')
        return False

    fatl.log(f'CHECK PAGE -> success')
    return page_t


def dl_page(Session, user, section, db, page_i, page_p, sync=False, speed=1, force=0, quiet=False, db_only=False):
    fatl.log(f'DOWNLOAD PAGE -> user:{user} section:{section} page:{page_i}')
    sub_i = 0
    for sub in page_p.findAll('figure'):
        if fatl.sigint_check(): return 5

        sub_i += 1
        ID = sub.get('id')[4:]
        print(f'{user[0:5]: ^5} {page_i:0>3}/{sub_i:0>2} {section} | {ID:0>10} | ', end='', flush=True)
        folder = f'{favar.files_folder}/{fatl.tiers(ID)}/{ID:0>10}'

        if fadb.usr_src(db, user, ID.zfill(10), section_db[section]):
            fatl.log(f'DOWNLOAD PAGE -> ID:{ID} found in USERS database')
            if sys.platform in ('win32', 'cygwin'):
                cols = os.get_terminal_size()[0] - 44
            else:
                cols = os.get_terminal_size()[0] - 43
            if cols < 0: cols = 0
            title = str_clean(sub.find_all('a')[1].string)[0:cols]
            if quiet and not force:
                print('\r'+' '*30+'\r', end='', flush=True)
            else:
                print('[Repository]'+(' '+title)*bool(title))
            if sync:
                if force > 0 and page_i <= force: continue
                if force == -1: continue
                if sub_i+page_i == 2: return 3
                else: return 2
            continue

        if fatl.sigint_check(): return 5

        t1 = time.time()
        s_ret = dl_sub(Session, ID, folder, db, False, True, speed, db_only)
        t2 = time.time()
        if speed == 0 and t2-t1 < 1.5 and t2-t1 > 0:
            fatl.log(f'DOWNLOAD PAGE -> waiting {t2-t1} seconds')
            time.sleep(t2-t1)

        if s_ret != 3:
            fadb.usr_up(db, user, ID.zfill(10), section_db[section])
            if db_only: time.sleep(1)

        if fatl.sigint_check(): return 5

    return 0

def dl_gs(Session, user, section, db, sync=False, speed=1, force=0, quiet=False, db_only=False):
    fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user}')
    url = 'https://www.furaffinity.net/'
    url += f'{section_full[section]}/{user}/'

    page_i = 0
    while True:
        if fatl.sigint_check(): return 5

        page_i += 1
        fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} page:{page_i}')
        page_r = Session.get(url+str(page_i))
        page_p = bs4.BeautifulSoup(page_r.text, 'lxml')
        page_p = page_p.find('section', id="gallery-gallery")

        if page_p == None:
            fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} section:{section} page:{page_i} empty')
            if page_i == 1:
                fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} section:{section} disabled section')
                print(f"{user[0:12]: ^12} {section} | Section disabled for user")
                return 4
            else:
                return 0

        if page_p.find('figure') is None:
            fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} section:{section} page:{page_i} no subs')
            if page_i == 1:
                if not quiet:
                    print(f"{user[0:5]: ^5} 001/01 {section} | No submissions to download")
                return 1
            else:
                return 0

        if fatl.sigint_check(): return 5

        page_ret = dl_page(Session, user, section, db, page_i, page_p, sync, speed, force, quiet, db_only)

        if page_ret != 0: return page_ret

        if fatl.sigint_check(): return 5

def dl_e(Session, user, section, db, sync=False, speed=1, force=0, quiet=False, db_only=False):
    fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user}')
    url = 'https://www.furaffinity.net/'
    if section == 'e':
        url += f'search/?q=( @message (":icon{user}:" | ":{user}icon:")) | ( @keywords ("{user}"))'
    elif section == 'E':
        url += f'search/?q=( @message (":icon{user}:" | ":{user}icon:" | "{user}")) | ( @keywords ("{user}"))'
    url += f' ! ( @lower {user} )'
    url += '&order-by=date'

    page_i = 0
    while True:
        if fatl.sigint_check(): return 5

        page_i += 1
        fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} page:{page_i}')
        page_r = Session.get(f'{url}&page={page_i}')
        page_p = bs4.BeautifulSoup(page_r.text, 'lxml')
        page_p = page_p.find('section', id="gallery-search-results")

        if page_p == None:
            fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} section:{section} page:{page_i} empty')
            if page_i == 1:
                return 1
            else:
                return 0

        if page_p.find('figure') is None:
            fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} section:{section} page:{page_i} no subs')
            if page_i == 1:
                if not quiet:
                    print(f"{user[0:5]: ^5} 001/01 {section} | No submissions to download")
                return 1
            else:
                return 0

        if fatl.sigint_check(): return 5

        page_ret = dl_page(Session, user, section, db, page_i, page_p, sync, speed, force, quiet, db_only)

        if page_ret != 0: return page_ret

        if fatl.sigint_check(): return 5

def dl_f(Session, user, section, db, sync=False, speed=1, force=0, quiet=False, db_only=False):
    fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user}')
    url = f'https://www.furaffinity.net/favorites/{user}'

    page_i = 0
    url_i = ''
    while True:
        if fatl.sigint_check(): return 5

        page_i += 1
        fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} page:{page_i}')
        page_r = Session.get(url+url_i)
        page_p = bs4.BeautifulSoup(page_r.text, 'lxml')
        page_next = page_p.find('a', {"class": "button mobile-button right"})
        page_p = page_p.find('section', id="gallery-favorites")

        if page_p == None:
            fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} section:{section} page:{page_i} empty')
            if page_i == 1:
                fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} section:{section} disabled section')
                print(f"{user[0:12]: ^12} {section} | Section disabled for user")
                return 4
            else:
                return 0

        if page_p.find('figure') is None:
            fatl.log(f'DOWNLOAD {section_db[section]} -> user:{user} section:{section} page:{page_i} no subs')
            if page_i == 1:
                if not quiet:
                    print(f"{user[0:5]: ^5} 001/01 {section} | No submissions to download")
                return 1
            else:
                return 0

        if fatl.sigint_check(): return 5

        page_ret = dl_page(Session, user, section, db, page_i, page_p, sync, speed, force, quiet, db_only)

        if page_ret != 0: return page_ret

        if fatl.sigint_check(): return 5

        if page_next:
            page_next = page_next['href']
            page_next = page_next.split(user)[-1]
            page_i += 1
        else:
            return 0

def dl_usr(Session, user, section, db, sync=False, speed=1, force=0, quiet=False, db_only=False):
    fatl.log(f'DOWNLOAD USER -> user:{user} section:{section}')
    print(f'{user[0:12]: ^12} {section}\r', end='', flush=True)
    if section in ('g', 's'):
        dl_ret = dl_gs(Session, user, section, db, sync, speed, force, quiet, db_only)
    elif section in ('e', 'E'):
        dl_ret = dl_e(Session, user, section, db, sync, speed, force, quiet, db_only)
    elif section in ('f'):
        dl_ret = dl_f(Session, user, section, db, sync, speed, force, quiet, db_only)

    if dl_ret not in (1, 4):
        if section == 'e':
            fadb.usr_rep(db, user, 'E', 'e', 'FOLDERS')
        elif section == 'E':
            fadb.usr_rep(db, user, 'e', 'E', 'FOLDERS')
        else:
            fadb.usr_up(db, user, section, 'FOLDERS')

    return dl_ret


def update(Session, db, users, sections, speed, force, index, db_only):
    fatl.log('UPDATE -> start')
    if fatl.sigint_check(): return

    print('Update')
    print('USR PAGE SECT. |     ID     | [SUB STATUS] TITLE')
    print('-'*50)

    users_db = db.execute("SELECT user, folders FROM users ORDER BY user ASC")
    t = int(time.time())
    fadb.info_up(db, 'LASTUP', t)
    fadb.info_up(db, 'LASTUPT', 0)
    flag_download = False

    fatl.log(f'UPDATE -> db_users:{len(users_db)}')

    for u in users_db:
        if fatl.sigint_check(): break
        flag_download_u = False

        if users and u[0] not in users:
            continue

        for s in u[1].split(','):
            dl_ret = 0
            if fatl.sigint_check():
                dl_ret = 5
                break
            if len(sections) and s not in sections:
                continue
            if s[-1] == '!' and s[0] not in sections:
                continue

            print(f'{u[0][0:12]: ^12} {s}\r', end='', flush=True)

            dl_ret = dl_usr(Session, u[0], s, db, True, speed, force, True, db_only)
            if dl_ret == 3:
                print('\b \b'*os.get_terminal_size()[0], end='', flush=True)
            if dl_ret in (0,2,4):
                flag_download_u = True
            if dl_ret == 4:
                fadb.usr_rep(db, u[0], s, s+'!', 'FOLDERS')
            if dl_ret == 5 or fatl.sigint_check():
                dl_ret = 5
                break

        if fatl.sigint_check(): break
        if dl_ret == 5:
            break

        if flag_download_u:
            flag_download = True

    if not flag_download:
        print("No new submissions were downloaded")
    elif index:
        print('\nIndexing new entries ... ', end='', flush=True)
        fadb.mkindex(db)
        print('Done')
    elif not index:
        fadb.info_up(db, 'INDEX', 0)

    t = int(time.time()) - t
    fadb.info_up(db, 'LASTUPT', t)

def download(Session, db, users, sections, sync, speed, force, index, db_only):
    fatl.log('DOWNLOAD -> start')
    if fatl.sigint_check(): return

    usr_sec = [[u, "".join(sections)] for u in users]
    print('Checking users:')
    i = -1
    while True:
        if fatl.sigint_check(): return
        i += 1
        if i == len(usr_sec): break
        print(f'  {usr_sec[i][0]} ... ', end='', flush=True)

        page_check = check_page(Session, f'user/{usr_sec[i][0]}')
        if page_check:
            print('Found')
            usr_full = page_check[11:-25].strip()
        else:
            print('Not found')
            usr_sec[i][1] = re.sub('[^eE]', '', usr_sec[i][1])
            usr_full = usr_sec[i][0]

        if len(usr_sec[i][1]) == 0:
            usr_sec = usr_sec[0:i] + usr_sec[i+1:]
            i -= 1
            continue

        fadb.usr_ins(db, usr_sec[i][0], usr_full)

    if fatl.sigint_check(): return

    print()

    fatl.log(f'DOWNLOAD -> users, sections:{usr_sec}')

    if len(usr_sec) == 0:
        print('Nothing to download')
        return
    print('Download')
    print('USR PAGE SECT. |     ID     | [SUB STATUS] TITLE')

    flag_download = False
    t = int(time.time())
    fadb.info_up(db, 'LASTDL', t)
    fadb.info_up(db, 'LASTDLT', 0)

    for usr in usr_sec:
        print('-'*50)
        for i in range(0, len(usr[1])):
            sec = usr[1][i]
            dl_ret = dl_usr(Session, usr[0], sec, db, sync, speed, force, False, db_only)
            if dl_ret in (0,1,2,3,5):
                if sec == 'e':
                    fadb.usr_rep(db, usr[0], 'E', 'e', 'FOLDERS')
                elif sec == 'E':
                    fadb.usr_rep(db, usr[0], 'e', 'E', 'FOLDERS')
                else:
                    fadb.usr_up(db, usr[0], sec, 'FOLDERS')
            elif dl_ret == 4:
                fadb.usr_rep(db, usr[0], sec, sec+'!', 'FOLDERS')
            if dl_ret in (0,2,5):
                flag_download = True
            if dl_ret == 5:
                break
            if i < len(usr[1])-1:
                print('-'*29)
        if fadb.usr_isempty(db, usr[0]):
            fadb.usr_rm(db, usr[0])
            print(f'{usr[0][0:14]: ^14} | No downloads, user deleted')
        if dl_ret == 5:
            break

    t = int(time.time()) - t
    fadb.info_up(db, 'LASTDLT', t)

    if not flag_download:
        print("No new submissions were downloaded")
    elif index:
        print('\nIndexing new entries ... ', end='', flush=True)
        fadb.mkindex(db)
        print('Done')
    elif not index:
        fadb.info_up(db, 'INDEX', 0)

def download_main(Session, db):
    fatl.header('Download & Update')

    while True:
        try:
            users = readkeys.input('Insert username: ').lower()
            sections = readkeys.input('Insert sections: ')
            options = readkeys.input('Insert options: ').lower()
        except:
            return

        fatl.log(f'DOWNLOAD MAIN -> users:"{users}" sections:"{sections}" options:"{options}"')

        users = re.sub('([^a-zA-Z0-9\-., ])', '', users)
        users = re.sub('( )+', ',', users.strip())
        users = sorted(set([u for u in users.split(',') if u != '']))

        sections = re.sub('[^gsfeE]', '', sections)
        sections = list(set(sections))
        sections = [s for s in ('g','s','f','e','E') if s in sections]

        speed = 1 ; upd = False
        sync = False ; force = 0
        quit = False ; index = True
        db_only = False
        if 'quick' in options: speed = 2
        if 'slow' in options: speed = 0
        if 'update' in options: upd = True
        if 'sync' in options: sync = True
        if 'all' in options: force = -1
        if 'noindex' in options: index = False
        if 'dbonly' in options: db_only = True
        if re.search('force[0-9]+', options):
            force = re.search('force[0-9]+', options).group(0)
            force = re.sub('[^0-9]', '', force)
            force = int(force)
        if 'quit' in options: quit = True
        if force != 0: speed = 1

        fatl.log(f'DOWNLOAD MAIN -> upd:{upd} sync:{sync} force:{force} speed:{speed} index:{index} dbonly:{db_only} quit:{quit}')

        if upd or (len(users) > 0 and len(sections) > 0):
            break
        else:
            print()

    print()
    Session = session(Session)
    print()

    if not Session:
        print('Session error')
        return None

    if fatl.sigint_check(): return Session

    if upd:
        update(Session, db, users, sections, speed, force, index, db_only)
    else:
        download(Session, db, users, sections, sync, speed, force, index, db_only)
    fadb.info_up(db, 'USRN', fadb.table_n(db, 'USERS'))
    fadb.info_up(db, 'SUBN', fadb.table_n(db, 'SUBMISSIONS'))

    print()

    if quit:
        fatl.log('DOWNLOAD MAIN -> quit')
        sys.exit(0)
    return Session
