CREATE TABLE schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(shift_id) REFERENCES shifts(id),
            FOREIGN KEY(user_id) REFERENCES users(id) 
        );

