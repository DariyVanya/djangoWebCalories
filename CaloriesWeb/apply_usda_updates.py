import csv
import sqlite3
import shutil
import datetime
import os

ROOT = os.path.dirname(__file__)
DB_PATH = os.path.join(ROOT, 'db.sqlite3')
CSV_PATH = os.path.join(ROOT, 'food_usda_compare.csv')
BACKUP_DIR = ROOT

TIMESTAMP = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
BACKUP_PATH = os.path.join(BACKUP_DIR, f'db_backup_{TIMESTAMP}.sqlite3')
APPLIED_CSV = os.path.join(ROOT, f'usda_updates_applied_{TIMESTAMP}.csv')
SKIPPED_CSV = os.path.join(ROOT, f'usda_updates_skipped_{TIMESTAMP}.csv')

print('DB path:', DB_PATH)
print('CSV path:', CSV_PATH)
print('Backup path:', BACKUP_PATH)

# Make backup
shutil.copy2(DB_PATH, BACKUP_PATH)
print('Backup created.')

# Read USDA compare CSV
rows = []
with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        rows.append(r)

# Deduplicate by (name, usda_kcal_100g, usda_protein_100g, usda_carbs_100g, usda_fats_100g)
seen = set()
unique_rows = []
for r in rows:
    key = (r.get('name','').strip(), r.get('usda_kcal_100g','').strip(), r.get('usda_protein_100g','').strip(), r.get('usda_carbs_100g','').strip(), r.get('usda_fats_100g','').strip())
    if key in seen:
        continue
    seen.add(key)
    unique_rows.append(r)

# Prepare updates
updates = []
skipped = []
conn = sqlite3.connect(DB_PATH, timeout=30)
conn.execute('PRAGMA busy_timeout = 30000')
cur = conn.cursor()
for r in unique_rows:
    status = r.get('status','').strip().lower()
    name = r.get('name','').strip()
    if status != 'updated':
        skipped.append({'name': name, 'reason': f'status={status}'})
        continue
    try:
        kcal100 = r.get('usda_kcal_100g','').strip()
        prot100 = r.get('usda_protein_100g','').strip()
        carbs100 = r.get('usda_carbs_100g','').strip()
        fats100 = r.get('usda_fats_100g','').strip()
        if not kcal100:
            skipped.append({'name': name, 'reason': 'missing usda kcal'})
            continue
        kcal100 = float(kcal100)
        prot100 = float(prot100) if prot100 else 0.0
        carbs100 = float(carbs100) if carbs100 else 0.0
        fats100 = float(fats100) if fats100 else 0.0
    except Exception as e:
        skipped.append({'name': name, 'reason': f'parse error {e}'})
        continue

    # Find matching DB rows by name
    cur.execute('SELECT id, grams, calories, protein, carbs, fats FROM meals_food WHERE name = ?', (name,))
    matches = cur.fetchall()
    if not matches:
        skipped.append({'name': name, 'reason': 'missing-db'})
        continue

    for mid, grams, old_cal, old_prot, old_carbs, old_fats in matches:
        try:
            grams = float(grams) if grams not in (None, '', 0) else 100.0
        except Exception:
            grams = 100.0
        factor = grams / 100.0
        new_cal = round(kcal100 * factor, 1)
        new_prot = round(prot100 * factor, 1)
        new_carbs = round(carbs100 * factor, 1)
        new_fats = round(fats100 * factor, 1)
        updates.append((new_cal, new_prot, new_carbs, new_fats, mid, name, grams, old_cal, old_prot, old_carbs, old_fats, r.get('usda_description',''), r.get('match_score','')))

# Apply updates in a transaction
if updates:
    print(f'Applying {len(updates)} updates...')
    cur.executemany('UPDATE meals_food SET calories = ?, protein = ?, carbs = ?, fats = ? WHERE id = ?', [(u[0],u[1],u[2],u[3],u[4]) for u in updates])
    conn.commit()
    print('Updates committed.')
else:
    print('No updates to apply.')

# Write applied CSV
with open(APPLIED_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['id','name','grams','old_calories','old_protein','old_carbs','old_fats','new_calories','new_protein','new_carbs','new_fats','usda_description','match_score'])
    for u in updates:
        mid = u[4]
        name = u[5]
        grams = u[6]
        old_cal = u[7]
        old_prot = u[8]
        old_carbs = u[9]
        old_fats = u[10]
        new_cal = u[0]
        new_prot = u[1]
        new_carbs = u[2]
        new_fats = u[3]
        desc = u[11]
        score = u[12]
        w.writerow([mid, name, grams, old_cal, old_prot, old_carbs, old_fats, new_cal, new_prot, new_carbs, new_fats, desc, score])

# Write skipped CSV
with open(SKIPPED_CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['name','reason'])
    for s in skipped:
        w.writerow([s.get('name'), s.get('reason')])

conn.close()
print('Applied report:', APPLIED_CSV)
print('Skipped report:', SKIPPED_CSV)
print('Done.')
