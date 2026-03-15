import sqlite3
import os
import shutil
from datetime import datetime
import zipfile
import json


class DatabaseManager:
    def __init__(self, db_path='database/attendance.db'):
        self.db_path = db_path

    def backup_database(self, backup_dir='database/backups'):
        """Create a timestamped backup of the database"""
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'{backup_dir}/attendance_backup_{timestamp}.db'
        shutil.copy2(self.db_path, backup_path)

        # Also create a compressed version
        with zipfile.ZipFile(f'{backup_path}.zip', 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(backup_path, os.path.basename(backup_path))

        return backup_path

    def restore_database(self, backup_file):
        """Restore database from backup"""
        if os.path.exists(backup_file):
            # Create a backup of current database before restore
            if os.path.exists(self.db_path):
                current_backup = f'database/pre_restore_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
                shutil.copy2(self.db_path, current_backup)

            shutil.copy2(backup_file, self.db_path)
            return True
        return False

    def get_database_stats(self):
        """Get database size and table stats"""
        stats = {
            'size_mb': round(os.path.getsize(self.db_path) / (1024 * 1024), 2),
            'tables': {},
            'last_modified': datetime.fromtimestamp(os.path.getmtime(self.db_path)).strftime('%Y-%m-%d %H:%M:%S')
        }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            stats['tables'][table_name] = count

        conn.close()
        return stats

    def optimize_database(self):
        """Optimize database (VACUUM and ANALYZE)"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('VACUUM;')
        conn.execute('ANALYZE;')
        conn.close()
        return True

    def export_to_json(self, export_dir='database/exports'):
        """Export all tables to JSON files"""
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        exported_files = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()

            # Convert to list of dicts
            data = [dict(row) for row in rows]

            # Save to JSON
            json_path = f'{export_dir}/{table_name}_{timestamp}.json'
            with open(json_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            exported_files.append(json_path)

        conn.close()
        return exported_files

    def list_backups(self, backup_dir='database/backups'):
        """List all available backups"""
        if not os.path.exists(backup_dir):
            return []

        backups = []
        for file in os.listdir(backup_dir):
            if file.endswith('.db') or file.endswith('.zip'):
                file_path = os.path.join(backup_dir, file)
                backups.append({
                    'name': file,
                    'size_mb': round(os.path.getsize(file_path) / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                })

        return sorted(backups, key=lambda x: x['modified'], reverse=True)

    def cleanup_old_backups(self, keep_days=7, backup_dir='database/backups'):
        """Remove backups older than specified days"""
        from datetime import datetime, timedelta

        if not os.path.exists(backup_dir):
            return 0

        cutoff = datetime.now() - timedelta(days=keep_days)
        removed = 0

        for file in os.listdir(backup_dir):
            if file.endswith('.db') or file.endswith('.zip'):
                file_path = os.path.join(backup_dir, file)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff:
                    os.remove(file_path)
                    removed += 1

        return removed

    def import_from_json(self, json_file, table_name):
        """Import data from JSON file to specified table"""
        if not os.path.exists(json_file):
            return False

        with open(json_file, 'r') as f:
            data = json.load(f)

        if not data:
            return False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get column names from first record
        columns = list(data[0].keys())
        placeholders = ','.join(['?' for _ in columns])
        column_names = ','.join(columns)

        # Insert data
        for record in data:
            values = [record[col] for col in columns]
            try:
                cursor.execute(f"INSERT OR IGNORE INTO {table_name} ({column_names}) VALUES ({placeholders})", values)
            except Exception as e:
                print(f"Error inserting record: {e}")

        conn.commit()
        conn.close()
        return True