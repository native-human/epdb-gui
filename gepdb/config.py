"Module to manage the configuration file"
import os.path
import sqlite3
import datetime

CONFIG_DIR = os.path.expanduser("~/.config/gepdb")
CONFIG_NAME = "gepdb"
CONFIG_FULL_NAME = os.path.join(CONFIG_DIR, CONFIG_NAME)

if not os.path.exists(CONFIG_DIR):
    os.mkdir(CONFIG_DIR)

conn = None
if not os.path.exists(CONFIG_FULL_NAME):
    conn = sqlite3.connect(CONFIG_FULL_NAME,
                detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    with conn:
        # Create table
        conn.execute('''create table recently_used_programs
            (filename text, last_access timestamp)''')
    
        conn.execute('''create table recently_used_files
            (filename text, last_access timestamp)''')
    
        # Save (commit) the changes
        conn.commit()
else:
    conn = sqlite3.connect(CONFIG_FULL_NAME)

def delete_program(filename):
    with conn:
        conn.execute("delete from recently_used_programs "
                           "where filename = ?", (filename,))

def delete_file(filename):
    with conn:
        conn.execute("delete from recently_used_files "
                           "where filename = ?", (filename,))

def save_program_access(filename, now=None):
    """Save access to a program to the configuration file"""
    with conn:
        if not now:
            now = datetime.datetime.now()
        cur = conn.execute("select * from recently_used_programs "
                           "where filename = ?", (filename,))
        if not cur.fetchone():
            conn.execute("insert into recently_used_programs "
                         "values (?, ?)", (filename, now))
        else:
            conn.execute("update recently_used_programs SET "
                         "last_access = ? where filename = ?", (now, filename))

def save_file_access(filename, now=None):
    """Save access to a file to the configuration file"""
    with conn:
        if not now:
            now = datetime.datetime.now()
        cur = conn.execute("select * from recently_used_files "
                           "where filename = ?", (filename,))
        if not cur.fetchone():
            conn.execute("""insert into recently_used_files
                values (?, ?)""", (filename, now))
        else:
            conn.execute("update recently_used_files SET last_access = ? "
                         "where filename = ?", (now, filename))

def get_latest_programs(howmany=10):
    "returns a list of the latest started programs."
    with conn:
        cur = conn.execute("select * from recently_used_programs order by "
                           "last_access desc LIMIT 0, ?", (howmany,))
        return cur.fetchall()
    
def get_latest_files(howmany=10):
    "returns a list of the latest opened files."
    with conn:
        cur = conn.execute("select * from recently_used_files order by "
                           "last_access desc LIMIT 0, ?", (howmany,))
        return cur.fetchall()