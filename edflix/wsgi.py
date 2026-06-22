import os
import shutil
from pathlib import Path

# On Vercel the repo filesystem is read-only. Copy db to /tmp so Django can read/write.
if os.environ.get('VERCEL_ENV'):
    src = Path(__file__).resolve().parent.parent / 'db.sqlite3'
    dst = Path('/tmp/db.sqlite3')
    if not dst.exists() and src.exists():
        shutil.copy(src, dst)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edflix.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
