import sqlite3 as sq


def create_database():
    global conn, cur
    conn = sq.connect('base.db')
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS list (steamlogin TEXT, mail TEXT, empass TEXT)")

    conn.commit()
    conn.close()
create_database()

async def sql_add_command(state):
    async with state.proxy() as data:
        conn = sq.connect('base.db')
        cur = conn.cursor()
        cur.execute("INSERT OR IGNORE INTO list(steamlogin, mail, empass) VALUES(?, ?, ?)", tuple(data.values()))
        conn.commit()
        conn.close()

async def sql_read(cur, message):
    for ret in cur.execute('SELECT * FROM list').fetchall():
        await message.answer(f'Имя: {ret[0]}\nВаш адрес: {ret[1]}\nНомер телефона: {ret[2]}')

async def sql_read2(cur):
    return cur.execute('SELECT * FROM list').fetchall()

async def sql_delete_command(data):
    conn = sq.connect('base.db') 
    cur = conn.cursor()
    
    try:
        cur.execute('DELETE FROM list WHERE steamlogin = ?', (data,))
        conn.commit() 
    except sq.Error as e:
        print(f"Ошибка при удалении записи: {e}")
    finally:
        cur.close()  # Закрываем курсор
        conn.close()