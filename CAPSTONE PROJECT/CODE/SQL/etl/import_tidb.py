"""Run the Olist ETL against the project's TiDB Cloud Starter instance."""

from getpass import getpass
import os
from pathlib import Path
import runpy
import sys


ROOT = Path(__file__).resolve().parents[2]
os.environ.update({
    "MYSQL_HOST": "gateway01.ap-northeast-1.prod.aws.tidbcloud.com",
    "MYSQL_PORT": "4000",
    "MYSQL_DATABASE": "olist",
    "MYSQL_ADMIN_USER": "423oDW7YJQNRZn2.root",
    "MYSQL_SSL_CA": str(ROOT / "isrgrootx1.pem"),
})

if not Path(os.environ["MYSQL_SSL_CA"]).is_file():
    raise SystemExit(
        f"Download TiDB's CA certificate to {os.environ['MYSQL_SSL_CA']} before importing."
    )

os.environ["MYSQL_ADMIN_PASS"] = getpass("TiDB password (input hidden): ")
# Existing rows use INSERT IGNORE, so rerunning fills failed tables without dropping imported data.
sys.argv = [str(Path(__file__).with_name("import_olist.py")), "--batch-size", "500"]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
finally:
    os.environ.pop("MYSQL_ADMIN_PASS", None)
