"""
Add script name to holiday
"""

from yoyo import step

__depends__ = {'20251223_01_Qyxon-create-holiday-message-table'}

steps = [
    step("ALTER TABLE holiday ADD COLUMN script_name TEXT;")
]
