class ThemeManager:
    def __init__(self):
        self.themes = {}
        self.current_theme = 'default'
        self._initialize_default_themes()

    def _initialize_default_themes(self):
        self.themes['default'] = {
            'colors': {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'background': '#ffffff',
                'text': '#212529',
                'grade_colors': {
                    'A': '#28a745',
                    'B': '#17a2b8',
                    'C': '#ffc107',
                    'D': '#fd7e14',
                    'E': '#dc3545',
                    'F': '#6c757d'
                }
            },
            'table': {
                'style': {
                    'header_color': 'yellow',
                    'border_color': 'grey'
                }
            },
            'chart': {
                'style': {
                    'background': '#ffffff',
                    'text': '#212529',
                    'grid': '#e9ecef',
                    'colormap': 'viridis'
                }
            }
        }

        self.themes['dark'] = {
            'colors': {
                'primary': '#0d6efd',
                'secondary': '#6c757d',
                'background': '#212529',
                'text': '#f8f9fa',
                'grade_colors': {
                    'A': '#2dce89',
                    'B': '#11cdef',
                    'C': '#fb6340',
                    'D': '#f5365c',
                    'E': '#8965e0',
                    'F': '#adb5bd'
                }
            },
            'table': {
                'style': {
                    'header_color': 'cyan',
                    'border_color': 'white'
                }
            },
            'chart': {
                'style': {
                    'background': '#212529',
                    'text': '#f8f9fa',
                    'grid': '#495057',
                    'colormap': 'plasma'
                }
            }
        }
