#!/usr/bin/env python
import sys
sys.path.insert(0, ".")

from proekt.backend.database import SessionLocal
from proekt.backend.models import File, User

db = SessionLocal()

print("\n=== PUBLIC FOLDERS ===")
public_folders = db.query(File).filter(File.is_public == True, File.file_type == "folder").all()
if public_folders:
    for f in public_folders:
        owner = db.query(User).filter(User.id == f.user_id).first()
        print("Folder: %s (ID: %s)" % (f.filename, f.folder_id))
        print("Owner: %s (ID: %d)" % (owner.email if owner else 'unknown', f.user_id))
else:
    print("No public folders")

print("\n=== ADMINS ===")
admins = db.query(User).filter(User.role == "admin").all()
for admin in admins:
    print("Admin: %s (ID: %d)" % (admin.email, admin.id))

db.close()
