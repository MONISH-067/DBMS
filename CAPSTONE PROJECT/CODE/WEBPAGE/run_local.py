"""Start the dashboard against this computer's MySQL only."""
import os
from pathlib import Path
import runpy
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env.local', override=True)
os.environ['MYSQL_HOST'] = '127.0.0.1'
os.environ['MYSQL_PORT'] = '3306'
runpy.run_module('marketplace.server', run_name='__main__')
