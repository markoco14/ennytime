CREATE TABLE shares (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER UNIQUE NOT NULL,
            receiver_id INTEGER UNIQUE NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT,
            FOREIGN KEY(sender_id) references users(id) ON DELETE CASCADE,
            FOREIGN KEY(receiver_id) references users(id) ON DELETE CASCADE
        );
