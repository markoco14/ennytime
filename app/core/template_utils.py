"""
Calendar related routes
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape
from jinja2_fragments.fastapi import Jinja2Blocks

from fastapi.templating import Jinja2Templates

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(['html', 'xml'])
)

templates = Jinja2Templates(directory="templates")
block_templates = Jinja2Blocks(directory="templates")


def is_user_shift(shift_type_id, shifts):
    return any(shift['type_id'] == shift_type_id for shift in shifts)

env.filters['is_user_shift'] = is_user_shift

# Add the custom filter to Jinja2 environment
templates.env = env
block_templates.env = env