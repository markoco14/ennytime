CREATE TABLE holiday_message (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                holiday_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL, 
                recipient_id INTEGET NOT NULL,
                FOREIGN KEY (holiday_id) REFERENCES holiday(holiday_id),
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id),
                UNIQUE (holiday_id, sender_id, recipient_id)
            );


