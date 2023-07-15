import sqlite3
from sqlite3 import Connection


class AccountsDB:

    def __init__(self, db_path: str):
        self.connect = sqlite3.connect(db_path)
        cursor = self.connect.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts(
                qid INT PRIMARY KEY,
                user_name TEXT,
                password TEXT,
                friend_code TEXT
            )
        ''')
        print("用户数据库初始化完成")
        self.connect.commit()

    def query_account_by_qid(self, qid: int) -> dict:
        cursor = self.connect.execute(f'''
            SELECT user_name, password, friend_code FROM accounts where qid = {qid}
        ''')
        for row in cursor:
            return {"username": row[0], "password": row[1], "friendCode": row[2]}
        return {}

    def insert_account(self, qid: int, user_name: str, password: str, friend_code: str,
                       del_before_ins: bool = True) -> None:
        if del_before_ins:
            sql = f'''
                DELETE FROM accounts WHERE qid = {qid}
            '''
            print("sql: ", sql)
            self.connect.execute(sql)

        sql = '''
            INSERT INTO accounts VALUES ('{qid}', '{user_name}', '{password}', '{friend_code}')
        '''.format(qid=qid, user_name=user_name, password=password, friend_code=friend_code)
        print("sql: ", sql)
        self.connect.execute(sql)

    def close(self):
        self.connect.close()


if __name__ == "__main__":
    db = AccountsDB("../pycq_bot/accounts.db")
    db.insert_account(2720299091, "Cody", "password", "123456789")
    db.insert_account(2720299091, "Cody", "password", "114514")
    db.connect.execute("SELECT * FROM ACCOUNTS")
    print("query for 2720299091: ", db.query_account_by_qid(2720299091))
    print("query for 114514: ", db.query_account_by_qid(1145144))
    print("dict size: ", len(db.query_account_by_qid(2720299091)))
