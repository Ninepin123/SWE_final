"""NUKSAMS 資料庫初始化 / 更新腳本（由 scripts/start.ps1 呼叫；組長維護）。

行為：
1. 用 backend/.env 的 DATABASE_URL 嘗試連線。
2. 連不上且原因是「資料庫不存在 / 帳號不存在」→ 引導輸入 MySQL root 密碼，
   執行 00_create_database.sql 建庫與開發帳號（每台電腦只需一次）。
3. 依編號執行 database/schema/01~99 的所有 SQL。
   所有 SQL 都要求可重複執行（IF NOT EXISTS / INSERT IGNORE），
   所以每次啟動都會跑一遍，確保拿到別人最新的資料表。

也可以單獨執行：backend\\.venv\\Scripts\\python scripts\\init_db.py
"""
import getpass
import re
import sys
from pathlib import Path

try:
    import pymysql
    from pymysql.constants import CLIENT
except ImportError:
    sys.exit("[X] 找不到 pymysql，請直接執行 start.bat（它會先安裝後端套件）")

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "database" / "schema"

ERR_ACCESS_DENIED = 1045
ERR_UNKNOWN_DB = 1049
ERR_CANT_CONNECT = 2003


def parse_database_url():
    env_file = ROOT / "backend" / ".env"
    if not env_file.exists():
        sys.exit("[X] 找不到 backend/.env，請直接執行 start.bat（它會自動建立）")
    url = None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL="):
            url = line.split("=", 1)[1].strip()
    if not url:
        sys.exit("[X] backend/.env 內缺少 DATABASE_URL")
    m = re.match(r"mysql\+pymysql://([^:]+):([^@]*)@([^:/]+)(?::(\d+))?/([^?]+)", url)
    if not m:
        sys.exit(f"[X] 無法解析 DATABASE_URL：{url}")
    user, password, host, port, db = m.groups()
    return {
        "user": user,
        "password": password,
        "host": host,
        "port": int(port or 3306),
        "db": db,
    }


def connect(host, port, user, password, db=None):
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=db,
        charset="utf8mb4",
        autocommit=True,
        client_flag=CLIENT.MULTI_STATEMENTS,  # 一次執行整份 .sql 檔
    )


def run_sql_file(conn, path):
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
        while cur.nextset():  # 消化多語句的所有結果
            pass


def bootstrap_as_root(cfg):
    """建立資料庫與開發帳號（每台電腦只需一次）。

    先試 root 無密碼（start.bat 下載的可攜版 MySQL 預設如此，全自動）；
    不行才詢問密碼（組員自己裝的 MySQL 才會走到這步）。
    """
    root_conn = None
    for attempt in ("auto", "ask"):
        if attempt == "auto":
            root_pwd = ""
        else:
            print("偵測到你使用自己安裝的 MySQL：需要 root 密碼建立資料庫與開發帳號（只需一次）。")
            root_pwd = getpass.getpass("請輸入 MySQL root 密碼：")
        try:
            root_conn = connect(cfg["host"], cfg["port"], "root", root_pwd)
            break
        except pymysql.err.OperationalError as e:
            if e.args[0] == ERR_ACCESS_DENIED:
                continue
            if e.args[0] == ERR_CANT_CONNECT:
                sys.exit(
                    f"[X] 連不到 MySQL（{cfg['host']}:{cfg['port']}）。\n"
                    "    請直接執行 start.bat（它會自動下載並啟動可攜版 MySQL）。"
                )
            raise
    if root_conn is None:
        sys.exit("[X] root 登入失敗，請確認密碼後重試。")
    run_sql_file(root_conn, SCHEMA_DIR / "00_create_database.sql")
    root_conn.close()
    print("  v 已建立資料庫 nuksams 與開發帳號 nuksams_dev")


def main():
    cfg = parse_database_url()
    try:
        conn = connect(cfg["host"], cfg["port"], cfg["user"], cfg["password"], cfg["db"])
    except pymysql.err.OperationalError as e:
        code = e.args[0]
        if code == ERR_CANT_CONNECT:
            sys.exit(
                f"[X] 連不到 MySQL（{cfg['host']}:{cfg['port']}）。\n"
                "    請直接執行 start.bat（它會自動下載並啟動可攜版 MySQL）；\n"
                "    若你在 backend/.env 指定了自己的 MySQL，請先把它啟動。"
            )
        if code in (ERR_ACCESS_DENIED, ERR_UNKNOWN_DB):
            bootstrap_as_root(cfg)
            try:
                conn = connect(cfg["host"], cfg["port"], cfg["user"], cfg["password"], cfg["db"])
            except pymysql.err.OperationalError as e2:
                sys.exit(
                    f"[X] 建庫後仍連線失敗：{e2.args[1]}\n"
                    "    請檢查 backend/.env 的 DATABASE_URL 帳密是否與 "
                    "database/schema/00_create_database.sql 內的開發帳號一致。"
                )
        else:
            raise

    schema_files = sorted(f for f in SCHEMA_DIR.glob("*.sql") if not f.name.startswith("00_"))
    for f in schema_files:
        try:
            run_sql_file(conn, f)
            print(f"  v {f.relative_to(ROOT)}")
        except pymysql.err.MySQLError as e:
            sys.exit(f"[X] 執行 {f.relative_to(ROOT)} 失敗：{e}\n    請通知該檔負責人修正。")
    conn.close()
    print("資料庫已是最新狀態。")


if __name__ == "__main__":
    main()
