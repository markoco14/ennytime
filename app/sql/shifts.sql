CREATE TABLE shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            long_name TEXT NOT NULL,
            short_name TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

