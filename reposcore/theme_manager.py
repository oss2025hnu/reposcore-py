class ThemeManager:
    def __init__(self) -> None:
        self.themes = {}
        self.current_theme = 'default'
        self._initialize_default_themes()

    def _initialize_default_themes(self) -> None:
        self.themes['default'] = {
            'colors': {
                'primary': '#007bff',
                'secondary': '#6c757d',
                'background': '#ffffff',
                'text': '#212529'
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
                'text': '#f8f9fa'
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
