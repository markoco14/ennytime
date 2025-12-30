CREATE TABLE holiday (
                holiday_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                iso_date TEXT,
                template_name TEXT,
                script_name TEXT
                );