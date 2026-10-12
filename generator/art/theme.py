"""Visual themes. Select with the AUG_THEME environment variable (roman, steampunk, stoneage).

generate.py sets AUG_THEME from its --theme option before the art modules are imported.
"""
import os

NAME = os.environ.get("AUG_THEME", "roman")

THEMES = {
    "roman": {
        "title": "Augustus",
        "roof": (178, 82, 50), "plaster": (226, 210, 176), "ochre": (204, 160, 96), "marble": (232, 228, 218),
        "stone": (168, 160, 146), "wood": (130, 90, 50), "canvas": (222, 206, 166),
        "skin": (214, 160, 112), "hair": (70, 44, 24),
        "ui_parchment": (222, 200, 150), "ui_stone": (146, 132, 108), "ui_bronze": (176, 128, 64),
        "ui_gold": (214, 172, 66), "ui_border": (120, 84, 46), "ui_inner": (64, 52, 40), "ui_topbar": (150, 120, 80),
        "ui_sidebar": (124, 108, 86),
        "climate_tint": None,
    },
    "steampunk": {
        "title": "Augustus: Steam Age",
        "roof": (64, 120, 108), "plaster": (150, 76, 56), "ochre": (122, 96, 78), "marble": (196, 158, 74),
        "stone": (110, 104, 100), "wood": (92, 62, 40), "canvas": (176, 160, 130),
        "skin": (222, 176, 140), "hair": (40, 30, 24),
        "ui_parchment": (206, 182, 136), "ui_stone": (92, 74, 58), "ui_bronze": (196, 150, 58),
        "ui_gold": (226, 176, 70), "ui_border": (150, 100, 40), "ui_inner": (42, 36, 34), "ui_topbar": (88, 66, 48),
        "ui_sidebar": (78, 62, 50),
        # terrain: sootier, olive grass, murky water
        "climate_tint": {"grass": (1.05, 0.86, 0.62), "grass2": (1.08, 0.88, 0.62), "water": (0.95, 1.05, 0.72),
                         "dirt": (0.82, 0.76, 0.72), "tree": (1.0, 0.82, 0.62), "meadow": (1.1, 0.95, 0.6),
                         "sand": (0.9, 0.85, 0.8), "rock": (0.8, 0.78, 0.8)},
    },
    "stoneage": {
        "title": "Augustus: Stone Age",
        "roof": (186, 156, 92), "plaster": (156, 120, 84), "ochre": (140, 104, 70), "marble": (150, 146, 138),
        "stone": (132, 126, 116), "wood": (104, 72, 44), "canvas": (176, 140, 100),
        "skin": (196, 140, 96), "hair": (50, 32, 20),
        "ui_parchment": (196, 164, 122), "ui_stone": (128, 122, 112), "ui_bronze": (120, 96, 70),
        "ui_gold": (170, 140, 90), "ui_border": (96, 86, 74), "ui_inner": (58, 50, 42), "ui_topbar": (120, 112, 100),
        "ui_sidebar": (112, 104, 94),
        "climate_tint": {"grass": (0.85, 1.12, 0.7), "grass2": (0.9, 1.14, 0.7), "tree": (0.8, 1.1, 0.75),
                         "meadow": (1.0, 1.08, 0.7), "water": (0.8, 1.05, 1.05)},
    },
}

T = THEMES.get(NAME, THEMES["roman"])


def is_(name):
    return NAME == name
