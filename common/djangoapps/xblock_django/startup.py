""" will register signal handlers, moved out of __init__.py to ensure correct loading order post Django 1.7 """
import xblock_django.signals           # pylint: disable=unused-import