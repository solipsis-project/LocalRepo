# FALocalRepo

[![pypi version](https://img.shields.io/pypi/v/falocalrepo)](https://pypi.org/project/falocalrepo/)
[![supported Python version](https://img.shields.io/pypi/pyversions/falocalrepo)](https://pypi.org/project/falocalrepo/)
[![license](https://img.shields.io/pypi/l/falocalrepo)](https://pypi.org/project/falocalrepo/)

Pure Python program to download any user's gallery/scraps/favorites from the FurAffinity forum in an easily handled database.

## Introduction

This program was born with the desire to provide a relatively easy-to-use method for FA users to download submissions that they care about from the forum.

This program uses a custom scraping library to get content from FurAffinity. This is developed as a separate package also available on PyPi ([FAAPI@PyPi.org](https://pypi.org/project/faapi/)) and GitLab ([FAAPI@GitLab.com](https://gitlab.com/MatteoCampinoti94/FAAPI)). The data thus collected is then stored into a SQLite3 database and the submissions files are saved in a tiered tree structure based on their ID's.

## Contents

1. [Installation](#installation--requirements)
2. [How to Read Usage Instructions](#how-to-read-usage-instructions)
2. [Cookies](#cookies)
3. [Usage](#usage)
    1. [Help](#help)
    2. [Init](#init)
    3. [Configuration](#configuration)
    4. [Download](#download)
    5. [Database](#database)
4. [Database](#database-1)
5. [Submission Files](#submission-files)
6. [Upgrading from Earlier Versions](#upgrading-from-earlier-versions)
7. [Issues](#issues)
8. [Appendix](#appendix)

## Installation & Requirements

To install the program it is sufficient to use Python pip and get the package `falocalrepo`.

```shell
python3 -m pip install falocalrepo
```

Python 3.8 or above is needed to run this program, all other dependencies are handled by pip during installation. For information on how to install Python on your computer, refer to the official website [Python.org](https://www.python.org/).

The program needs cookies from a logged-in FurAffinity session to download protected pages. Without the cookies the program can still download publicly available pages, but others will return empty. See [#Cookies](#cookies) for more details on which cookies to use.

**Warning**: FurAffinity theme needs to be set to "beta"

## How to Read Usage Instructions

* `command` a static command keyword
* `<arg>` `<param>` `value` an argument, parameter, value, etc... that must be provided to a command
* `[<optional>]` an optional argument that can be omitted

## Cookies

The scraping library used by this program needs two specific cookies from a logged-in FurAffinity session. These are cookie `a` and cookie `b`.

As of 2020-08-09 these take the form of hexadecimal strings like `356f5962-5a60-0922-1c11-65003b703038`.

The easiest way to obtain these cookies is by using a browser extension to extract your cookies and then search for `a` and `b`.<br>
Alternatively, the storage inspection tool of a desktop browser can also be used. For example on Mozilla's Firefox this can be opened with &#8679;F9 shortcut.

To set the cookies use the `config cookies` command. See [#Configuration](#configuration) for more details.

## Usage

To run the program, simply call `falocalrepo` in your shell after installation.

Running without arguments will prompt a help message with all the available options and commands.

Generally, commands need to be in the following format:

```
falocalrepo [-h] [-v] [-d] <command> [<arg1>] ... [<argN>]
```

Available options are:

* `-h, --help` show help message
* `-v, --version` show program version
* `-d, --database` show database version

Available commands are:

* `help` display the manual of a command
* `init` create the database and exit
* `config` manage settings
* `download` perform downloads
* `database` operate on the database

_Note:_ all the commands with the exception of `help` will create and initialise the database if it is not present in the folder

When the database is first initialised, it defaults the submissions files folder to `FA.files`. This value can be changed using the [`config` command](#configuration).

Cookies need to be set manually with the config command before the program will be able to access protected pages.

### Help

`help [<command>]`

The `help` command gives information on the usage of the program and its commands. Run alone for help on the whole program and with a single argument to get help for a specific command.

```
falocalrepo help
```
```
falocalrepo help download
```

### Init

The `init` command initialises the database or, if one is already present, updates to a new version - if available - and then exits.

It can be used to create the database and then manually edit it, or to update it to a new version without calling other commands.

### Configuration

`config [<setting>] [<value1>] ... [<valueN>]`

The `config` command allows to change the settings used by the program.

Running the command alone will show the current values of the settings stored in the database. Running `config <setting>` without value arguments will show the current value of that specific setting.

Available settings are:

* `cookies [<cookie a>] [<cookie b>]` the cookies stored in the database.
```
falocalrepo config cookies 38565475-3421-3f21-7f63-3d341339737 356f5962-5a60-0922-1c11-65003b703038
```
* `files-folder [<new folder>]` the folder used to store submission files. This can be any path relative to the folder of the database. If a new value is given, the program will move any files to the new location.
```
falocalrepo config files-folder SubmissionFiles
```

### Download

`download <operation> [<arg1>] ... [<argN>]`

The `download` command performs all download and repository update operations.

Available operations are:

* `update` update the repository by checking the previously downloaded folders (gallery, scraps or favorites) of each user and stopping when it finds a submission that is already present in the repository. Requires no arguments.
* `users <user1>,...,<userN> <folder1>,...,<folderN>` download specific user folders. Requires two arguments in the format is one of gallery, scraps or favorites.
```
falocalrepo download users tom,jerry gallery,scraps
```
* `submissions <id1> ... [<idN>]` download specific submissions. Requires submission ID's provided as separate arguments.
```
falocalrepo download submissions 12345678 13572468 87651234
```

### Database

`database [<operation>] [<param1>=<value1>] ... [<paramN>=<valueN>]`

The `database` command allows to operate on the database. Used without an operation command shows the database statistics (number of users and submissions and time of last update) and version.

Available operations are:

* `search <param1>=<value1> ... [<paramN>=<valueN>]` search the submissions entries using metadata fields. Search is conducted case-insensitively using the SQLite `like` expression which allows for limited pattern matching. For example this string can be used to search two tags together separated by an unknown amount of characters `cat,%mouse`. The following search parameters are supported:
    * `author` author (uploader) in display format - e.g. with underscores "_" -
    * `title`
    * `date`
    * `description` 
    * `tags` alphabetically sorted tags (keywords)
    * `category`
    * `species`
    * `gender`
    * `rating`
```
falocalrepo database search tags=cat,%mouse date=2020-% category=%artwork%
```
* `manual-entry <param1>=<value1> ... <paramN>=<valueN>` add a submission to the database manually. The submission file is not downloaded and can instead be provided with the extra parameter `file_local_url`. The following parameters are necessary for a submission entry to be accepted:
    * `id` submission id
    * `title`
    * `author`
    * `date` date in the format YYYY-MM-DD
    * `category`
    * `species`
    * `gender`
    * `rating`<br>
The following parameters are optional:
    * `tags` comma-separated tags
    * `description`
    * `file_url` the url of the submission file, not used to download the file
    * `file_local_url` if provided, take the submission file from this path and put it into the database
```
falocalrepo database manual-entry id=12345678 'title=cat & mouse' author=CartoonArtist \
    date=2020-08-09 category=Artwork 'species=Unspecified / Any' gender=Any rating=General \
    tags=cat,mouse,cartoon 'description=There once were a cat named Tom and a mouse named Jerry.' \
    'file_url=http://remote.url/to/submission.file' file_local_url=path/to/submission.file
```
* `check-errors` check the database for common errors and prints a list of entries that contain erroneous data. Requires no arguments.
* `remove-users <user1> ... [<userN>]` remove specific users from the database.
```
falocalrepo database remove-users jerry
```
* `remove-submissions <id1> ... [<idN>]` remove specific submissions from the database.
```
falocalrepo database remove-submissions 12345678 13572468 87651234
```
* `clean` clean the database using the SQLite [VACUUM](https://www.sqlite.org/lang_vacuum.html) function. Requires no arguments.

## Database

To store the metadata of the downloaded submissions, downloaded users, cookies and statistics, the program uses a SQLite3 database. This database is built to be as light as possible while also containing all the metadata that can be extracted from a submission page. 

To store all this information, the database uses three tables: `SETTINGS`, `USERS` and `SUBMISSIONS`.

### `SETTINGS`

The settings table contains settings for the program and statistics of the database.

* `USRN` number of users in the `USERS` table
* `SUBN` number of submissions in the `SUBMISSIONS` table
* `LASTUPDATE` time when the last update was completed (UNIX time in seconds)
* `LASTSTART` time when the program was last started (UNIX time in seconds)
* `COOKIES` cookies for the scraper, stored in JSON format
* `FILESFOLDER` location of downloaded submission files
* `VERSION` database version, this can differ from the program version

### `USERS`

The users table contains a list of all the users that have been download with the program, the folders that have been downloaded and the submissions found in each of those.

Each entry contains the following fields:

* `USERNAME` The URL username of the user (no underscores or spaces)
* `FOLDERS` the folders downloaded for that specific user.
* `GALLERY`
* `SCRAPS`
* `FAVORITES`
* `EXTRAS` this is a legacy entry used by the program up to version 2.11.2

### `SUBMISSIONS`

The submissions table contains the metadata of the submissions downloaded by the program and information on their files 

* `ID` the id of the submission
* `AUTHOR` the username of the author (uploader) in full format
* `TITLE`
* `UDATE` upload date in the format YYYY-MM-DD
* `DESCRIPTION` description in html format
* `TAGS` keywords sorted alphanumerically and comma-separated
* `CATEGORY`
* `SPECIES`
* `GENDER`
* `RATING`
* `FILELINK` the remote URL of the submission file
* `FILEEXT` the extensions of the downloaded file. Can be empty if the file contained errors and could not be recognised upon download
* `FILESAVED` 1 if the file was successfully downloaded and saved, 0 if there was an error during download

## Submission Files

Submission files are saved in a tiered tree structure based on their submission ID. ID's are zero-padded to 10 digits and then broken up in 5 segments of 2 digits; each of this segments represents a folder tha will be created in the tree.

For example, a submission `1457893` will be padded to `0001457893` and divided into `00`, `01`, `45`, `78`, `93`. The submission file will then be saved as `00/01/45/78/93/submission.file` with the correct extension extracted from the file itself - FurAffinity links do not always contain the right extension and often confuse jpg and png -.

## Upgrading from Earlier Versions

When the program starts, it checks the version of the database against the one used by the program and if the latter is more advanced it updates the database.

_Note:_ Versions before 2.7.0 are not supported by falocalrepo version 3.0.0 and above. To update from those to the new version use version 2.11.2 to update the database to version 2.7.0

### 2.7.0 &rarr; 3.0.0

Information from the database are copied over to the new version, but otherwise remain unaltered save for a few changed column names in the `SUBMISSIONS` and `USERS` tables.

Files are moved to the new structure and the old files folder is deleted. Only submissions files are kept starting from version 3.0.0

## Issues

If any problem is encountered during usage of the program, an issue can be opened on the project's Gitlab page: [FALocalRepo/Issues](https://gitlab.com/MatteoCampinoti94/FALocalRepo/issues).

When opening an issue on GitLab, please copy the error message and describe the operation in progress when the error occurred.

## Appendix

### Earlier Releases

Release binaries for versions 2.11.x can be found on GitLab under tags -> [FALocalRepo/tags 2.11](https://gitlab.com/MatteoCampinoti94/FALocalRepo/tags?search=v2.11)

Release binaries before and including 2.10.2 can be found on GitHub -> [Releases](https://github.com/MatteoCampinoti94/FALocalRepo/releases).