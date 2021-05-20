"""
This Sphinx project is used to test the Cyradoc directive
"""

project = 'Test docs for Cyradoc'

extensions = [
    'cyra.cyradoc'
]

source_suffix = '.rst'
language = 'en'

exclude_patterns = ['*/*']
