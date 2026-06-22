import sys
import requests
import geopandas as gpd
import os

from bokeh.plotting import figure
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    GeoJSONDataSource,
    Legend,
    LegendItem,
    FactorRange,
    ColumnDataSource,
    HoverTool,
    CheckboxGroup,
    CustomJS,
    TabPanel,
    Tabs,
    Wedge
)
from bokeh.layouts import column
from bokeh.embed import file_html
from bokeh.resources import INLINE

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView


# Stadionok adatai
stadiums = {
    "Groupama Aréna (Ferencváros)": (47.4769, 19.0963),
    "Pancho Aréna (Puskás Akadémia)": (47.4536, 18.5750),
    "Hidegkúti Nándor Stadion (MTK Budapest)": (47.4920, 19.4057),
    "Széktói Stadion (Kecskemét)": (46.8971, 19.6860),
    "Paksi Stadion (Paks)": (46.6188, 18.8540),
    "Nyíregyháza Városi Stadion (Nyíregyháza)": (47.970278, 21.712778),
    "Nagyerdei Stadion (Debrecen)": (47.5510, 21.6218),
    "DVTK Stadion (Diósgyőr)": (48.0887, 20.7917),
    "ZTE Stadion (Zalaegerszeg)": (46.8504, 16.8436),
    "ETO Park (Győr)": (47.695769, 17.663827),
    "Szusza Ferenc Stadion (Újpest)": (47.6639, 19.0853),
    "Sóstói Stadion (Videoton)": (47.1830, 18.4223)
}

stadium_colors = {
    "Groupama Aréna (Ferencváros)": 'green',
    "Pancho Aréna (Puskás Akadémia)": 'orange',
    "Hidegkúti Nándor Stadion (MTK Budapest)": 'blue',
    "Széktói Stadion (Kecskemét)": 'red',
    "Paksi Stadion (Paks)": 'purple',
    "Nyíregyháza Városi Stadion (Nyíregyháza)": 'brown',
    "Nagyerdei Stadion (Debrecen)": 'pink',
    "DVTK Stadion (Diósgyőr)": 'gray',
    "ZTE Stadion (Zalaegerszeg)": 'olive',
    "ETO Park (Győr)": 'cyan',
    "Szusza Ferenc Stadion (Újpest)": 'yellow',
    "Sóstói Stadion (Videoton)": 'teal'
}

HLG = [34, 34, 33, 18, 39, 18, 28, 21, 18, 25, 22, 19]
HKG = [11, 18, 23, 22, 23, 18, 30, 22, 18, 20, 21, 18]

# GeoJSON letöltés
url = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_countries.geojson"

r = requests.get(url)
r.raise_for_status()

with open("world.geojson", "wb") as f:
    f.write(r.content)

world = gpd.read_file("world.geojson")

hungary = world[world['ADMIN'] == "Hungary"]

geo_source = GeoJSONDataSource(geojson=hungary.to_json())

# Térkép
map_figure = figure(
    title="NB1 Stadionok",
    x_axis_label="Hosszúság",
    y_axis_label="Szélesség",
    width=1200,
    height=700,
    toolbar_location=None
)

map_figure.patches(
    xs='xs',
    ys='ys',
    source=geo_source,
    fill_color='lightgray',
    line_color='white',
    alpha=0.7
)

legend_items = []

for i, (stadium, (lat, lon)) in enumerate(stadiums.items()):

    total_goals = HLG[i] + HKG[i]
    home_ratio = HLG[i] / total_goals

    wedge_home = map_figure.annular_wedge(
        x=lon,
        y=lat,
        inner_radius=0,
        outer_radius=total_goals / 500 + 0.05,
        start_angle=0,
        end_angle=2 * 3.14159 * home_ratio,
        color=stadium_colors[stadium],
        alpha=0.8
    )

    map_figure.annular_wedge(
        x=lon,
        y=lat,
        inner_radius=0,
        outer_radius=total_goals / 500 + 0.05,
        start_angle=2 * 3.14159 * home_ratio,
        end_angle=2 * 3.14159,
        color="black",
        alpha=0.8
    )

    legend_items.append(
        LegendItem(label=stadium, renderers=[wedge_home])
    )

legend = Legend(items=legend_items)
map_figure.add_layout(legend, 'right')

# Oszlopdiagram
bar_source = ColumnDataSource(data=dict(
    stadiums=list(stadiums.keys()),
    HLG=HLG,
    HKG=HKG,
    total_goals=[HLG[i] + HKG[i] for i in range(len(HLG))]
))

bar_figure = figure(
    x_range=list(stadiums.keys()),
    title="Hazai és kapott gólok",
    width=1200,
    height=400
)

bar_figure.vbar(
    x='stadiums',
    top='HLG',
    width=0.8,
    color='green',
    source=bar_source
)

bar_figure.vbar(
    x='stadiums',
    top='total_goals',
    bottom='HLG',
    width=0.8,
    color='black',
    source=bar_source
)

hover = HoverTool(
    tooltips=[
        ("Hazai gól", "@HLG"),
        ("Kapott gól", "@HKG")
    ]
)

bar_figure.add_tools(hover)

bar_figure.xaxis.major_label_orientation = 1.2



# A csapatok játékosainak magassága, tömege, góljainak száma, életkora
ferencvaros_players = [
    {"name": "Szalai", "height": 191, "weight": 88, "position": "védő", "goals": 4, "age": 24},
    {"name": "Joseph Lenny", "height": 183, "weight": 78, "position": "támadó", "goals": 4, "age": 24},
    {"name": "Makreckis", "height": 180, "weight": 75, "position": "védő", "goals": 1, "age": 25},
    {"name": "Ben Romdhane", "height": 185, "weight": 78, "position": "középpályás", "goals": 3, "age": 25},
    {"name": "Abu Fani", "height": 170, "weight": 68, "position": "középpályás", "goals": 2, "age": 26},
    {"name": "Gruber", "height": 180, "weight": 74, "position": "támadó", "goals": 1, "age": 20},
    {"name": "Varga", "height": 178, "weight": 74, "position": "középpályás", "goals": 12, "age": 31},
    {"name": "Tóth", "height": 181, "weight": 78, "position": "középpályás", "goals": 2, "age": 19},
    {"name": "Traoré", "height": 177, "weight": 70, "position": "támadó", "goals": 3, "age": 26},
    {"name": "Pešić", "height": 190, "weight": 87, "position": "támadó", "goals": 6, "age": 31},
]



paks_players = [
    {"name": "Böde", "height": 185, "weight": 85, "position": "támadó", "goals": 15, "age": 36},
    {"name": "Könyves", "height": 184, "weight": 80, "position": "támadó", "goals": 3, "age": 33},
    {"name": "Vécsei", "height": 180, "weight": 75, "position": "középpályás", "goals": 1, "age": 31},
    {"name": "Tóth", "height": 198, "weight": 90, "position": "támadó", "goals": 2, "age": 30},
    {"name": "Kinyik", "height": 191, "weight": 82, "position": "védő", "goals": 1, "age": 29},
    {"name": "Ádám", "height": 190, "weight": 83, "position": "támadó", "goals": 1, "age": 30},
    {"name": "Windecker", "height": 185, "weight": 81, "position": "középpályás", "goals": 6, "age": 30},
    {"name": "Ötvös", "height": 177, "weight": 75, "position": "középpályás", "goals": 3, "age": 27},
    {"name": "Oshváth", "height": 177, "weight": 72, "position": "védő", "goals": 1, "age": 29},
    {"name": "Hinora", "height": 180, "weight": 73, "position": "védő", "goals": 2, "age": 27},
]


puskas_players = [
    {"name": "Golla", "height": 186, "weight": 80, "position": "védő", "goals": 2, "age": 31},
    {"name": "Stronati", "height": 190, "weight": 86, "position": "védő", "goals": 1, "age": 29},
    {"name": "Mondovics", "height": 178, "weight": 73, "position": "támadó", "goals": 1, "age": 18},
    {"name": "Puljic", "height": 187, "weight": 72, "position": "támadó", "goals": 1, "age": 32},
    {"name": "Colley", "height": 195, "weight": 86, "position": "védő", "goals": 10, "age": 27},
    {"name": "Nisille", "height": 172, "weight": 69, "position": "középpályás", "goals": 5, "age": 29},
    {"name": "Plšek", "height": 186, "weight": 79, "position": "középpályás", "goals": 7, "age": 26},
    {"name": "Nagy", "height": 188, "weight": 76, "position": "védő", "goals": 12, "age": 32},
    {"name": "Favorov", "height": 185, "weight": 78, "position": "középpályás", "goals": 3, "age": 31},
    {"name": "Levi", "height": 185, "weight": 75, "position": "középpályás", "goals": 11, "age": 29},
]



fehervar_players = [
    {"name": "Gradisar", "height": 187, "weight": 83, "position": "támadó", "goals": 7, "age": 23},
    {"name": "Szabó", "height": 179, "weight": 80, "position": "középpályás", "goals": 5, "age": 24},
    {"name": "Saponijic", "height": 190, "weight": 86, "position": "támadó", "goals": 4, "age": 28},
    {"name": "Stefanelli", "height": 166, "weight": 70, "position": "támadó", "goals": 3, "age": 31},
    {"name": "Katona", "height": 173, "weight": 74, "position": "középpályás", "goals": 4, "age": 25},
    {"name": "Csongvai", "height": 186, "weight": 79, "position": "középpályás", "goals": 1, "age": 25},
    {"name": "Holender", "height": 180, "weight": 73, "position": "támadó", "goals": 1, "age": 31},
    {"name": "Kalmár", "height": 185, "weight": 78, "position": "középpályás", "goals": 1, "age": 31},
    {"name": "Kastrati", "height": 174, "weight": 79, "position": "középpályás", "goals": 1, "age": 26},
    {"name": "Kovács", "height": 180, "weight": 73, "position": "támadó", "goals": 2, "age": 24},
]


debrecen_players = [
    {"name": "Ferenczi", "height": 183, "weight": 78, "position": "védő", "goals": 1, "age": 29},
    {"name": "Hofmann", "height": 183, "weight": 70, "position": "védő", "goals": 1, "age": 32},
    {"name": "Szécsi", "height": 180, "weight": 75, "position": "középpályás", "goals": 2, "age": 28},
    {"name": "Szűcs", "height": 177, "weight": 72, "position": "középpályás", "goals": 3, "age": 20},
    {"name": "Dreskovic", "height": 191, "weight": 86, "position": "védő", "goals": 2, "age": 27},
    {"name": "Dzsudzsák", "height": 179, "weight": 74, "position": "támadó", "goals": 2, "age": 36},
    {"name": "Vajda", "height": 174, "weight": 65, "position": "középpályás", "goals": 2, "age": 21},
    {"name": "Bárány", "height": 179, "weight": 81, "position": "támadó", "goals": 13, "age": 25},
    {"name": "Domingues", "height": 172, "weight": 65, "position": "támadó", "goals": 12, "age": 25},
    {"name": "Szuhodovszki", "height": 182, "weight": 70, "position": "középpályás", "goals": 2, "age": 25},
    ]

kecskemet_players = [
    {"name": "Camaj", "height": 182, "weight": 73, "position": "támadó", "goals": 5, "age": 28},
    {"name": "Pálinkás", "height": 192, "weight": 83, "position": "támadó", "goals": 4, "age": 28},
    {"name": "Nikitscher", "height": 193, "weight": 82, "position": "középpályás", "goals": 2, "age": 26},
    {"name": "Katona", "height": 178, "weight": 72, "position": "középpályás", "goals": 3, "age": 23},
    {"name": "Pászka", "height": 176, "weight": 71, "position": "védő", "goals": 1, "age": 29},
    {"name": "Zeke", "height": 184, "weight": 80, "position": "védő", "goals": 2, "age": 25},
    {"name": "Lukács", "height": 182, "weight": 73, "position": "támadó", "goals": 5, "age": 29},
    {"name": "kovács", "height": 181, "weight": 75, "position": "középpályás", "goals": 1, "age": 23},
    {"name": "Vágó", "height": 189, "weight": 83, "position": "védő", "goals": 1, "age": 33},
    {"name": "Zsótér", "height": 170, "weight": 79, "position": "középpályás", "goals": 2, "age": 29},
]


diosgyor_players = [
    {"name": "Edomwonyi", "height": 186, "weight": 77, "position": "támadó", "goals": 7, "age": 31},
    {"name": "Acolatse", "height": 184, "weight": 76, "position": "védő", "goals": 6, "age": 30},
    {"name": "Rakonjac", "height": 191, "weight": 85, "position": "támadó", "goals": 6, "age": 25},
    {"name": "Gera Dániel", "height": 178, "weight": 74, "position": "középpályás", "goals": 4, "age": 30},
    {"name": "Szatmári", "height": 198, "weight": 86, "position": "védő", "goals": 2, "age": 31},
    {"name": "Kállai", "height": 178, "weight": 72, "position": "védő", "goals": 1, "age": 23},
    {"name": "Szakos", "height": 180, "weight": 74, "position": "támadó", "goals": 1, "age": 22},
    {"name": "Požeg Vancaš", "height": 174, "weight": 66, "position": "középpályás", "goals": 2, "age": 31},
    {"name": "Huszár", "height": 182, "weight": 76, "position": "védő", "goals": 1, "age": 21},
    {"name": "Skribek", "height": 174, "weight": 70, "position": "védő", "goals": 1, "age": 24},
]


mtk_players = [
    {"name": "Bognár", "height": 180, "weight": 76, "position": "középpályás", "goals": 5, "age": 26},
    {"name": "Bobál", "height": 186, "weight": 79, "position": "védő", "goals": 2, "age": 28},
    {"name": "Hey", "height": 181, "weight": 80, "position": "védő", "goals": 2, "age": 27},
    {"name": "Kádár", "height": 184, "weight": 82, "position": "védő", "goals": 1, "age": 33},
    {"name": "Végh", "height": 183, "weight": 75, "position": "középpályás", "goals": 1, "age": 24},
    {"name": "Molnár", "height": 180, "weight": 73, "position": "támadó", "goals": 5, "age": 26},
    {"name": "Jurina", "height": 178, "weight": 70, "position": "támadó", "goals": 13, "age": 27},
    {"name": "Stieber", "height": 175, "weight": 67, "position": "középpályás", "goals": 2, "age": 37},
    {"name": "Horváth Artúr", "height": 183, "weight": 72, "position": "középpályás", "goals": 2, "age": 22},
    {"name": "Németh Krisztián", "height": 180, "weight": 72, "position": "támadó", "goals": 3, "age": 36},
]


zte_players = [
    {"name": "Dénes", "height": 181, "weight": 73, "position": "támadó", "goals": 5, "age": 20},
    {"name": "Jack", "height": 184, "weight": 74, "position": "középpályás", "goals": 2, "age": 27},
    {"name": "Krajcsovics", "height": 180, "weight": 72, "position": "középpályás", "goals": 2, "age": 20},
    {"name": "Németh Dániel", "height": 177, "weight": 70, "position": "támadó", "goals": 2, "age": 21},
    {"name": "Sajbán", "height": 182, "weight": 72, "position": "középpályás", "goals": 2, "age": 29},
    {"name": "Bakti", "height": 180, "weight": 73, "position": "középpályás", "goals": 1, "age": 20},
    {"name": "Csóka", "height": 175, "weight": 71, "position": "védő", "goals": 1, "age": 25},
    {"name": "Kiss Bence", "height": 178, "weight": 72, "position": "támadó", "goals": 1, "age": 25},
    {"name": "Medgyes", "height": 181, "weight": 74, "position": "védő", "goals": 1, "age": 31},
    {"name": "Croizet", "height": 176, "weight": 71, "position": "középpályás", "goals": 7, "age": 32},
]


ujpest_players = [
    {"name": "Beridze", "height": 180, "weight": 71, "position": "támadó", "goals": 2, "age": 25},
    {"name": "Matija Ljujic", "height": 183, "weight": 75, "position": "középpályás", "goals": 9, "age": 32},
    {"name": "Mucsányi", "height": 184, "weight": 74, "position": "támadó", "goals": 3, "age": 23},
    {"name": "Bese", "height": 188, "weight": 82, "position": "védő", "goals": 2, "age": 31},
    {"name": "Horváth Krisztofer György", "height": 182, "weight": 80, "position": "támadó", "goals": 2, "age": 23},
    {"name": "Karamoko", "height": 188, "weight": 83, "position": "támadó", "goals": 2, "age": 28},
    {"name": "Tom Lacoux", "height": 182, "weight": 70, "position": "középpályás", "goals": 2, "age": 23},
    {"name": "Tajti Mátyás", "height": 183, "weight": 73, "position": "középpályás", "goals": 2, "age": 27},
    {"name": "João Aniceto Grandela Nunes", "height": 188, "weight": 78, "position": "védő", "goals": 1, "age": 29},
    {"name": "Dénes Adrián", "height": 181, "weight": 72, "position": "középpályás", "goals": 1, "age": 24},
]



nyiregyhaza_players = [
    {"name": "Beke", "height": 180, "weight": 75, "position": "támadó", "goals": 6, "age": 24},
    {"name": "Kovácsréti", "height": 186, "weight": 74, "position": "támadó", "goals": 6, "age": 24},
    {"name": "Eppel", "height": 190, "weight": 88, "position": "támadó", "goals": 4, "age": 33},
    {"name": "Babic", "height": 188, "weight": 80, "position": "támadó", "goals": 3, "age": 25},
    {"name": "Nagy Dominik", "height": 178, "weight": 72, "position": "támadó", "goals": 3, "age": 22},
    {"name": "Navratil", "height": 180, "weight": 75, "position": "támadó", "goals": 3, "age": 33},
    {"name": "Keresztes", "height": 182, "weight": 73, "position": "középpályás", "goals": 1, "age": 28},
    {"name": "Kovács Milán", "height": 179, "weight": 72, "position": "középpályás", "goals": 1, "age": 23},
    {"name": "Nika Kvekveskiri", "height": 186, "weight": 79, "position": "középpályás", "goals": 1, "age": 33},
    {"name": "Tamás Olivér", "height": 188, "weight": 80, "position": "védő", "goals": 1, "age": 24}
]



gyor_players = [
    {"name": "Bumba", "height": 175, "weight": 70, "position": "középpályás", "goals": 9, "age": 31},
    {"name": "Benbouali", "height": 190, "weight": 85, "position": "támadó", "goals": 7, "age": 25},
    {"name": "Bitri", "height": 192, "weight": 86, "position": "védő", "goals": 5, "age": 29},
    {"name": "Ouro", "height": 188, "weight": 80, "position": "támadó", "goals": 4, "age": 24},
    {"name": "Stefulj", "height": 184, "weight": 78, "position": "középpályás", "goals": 4, "age": 32},
    {"name": "Gavric", "height": 185, "weight": 80, "position": "középpályás", "goals": 2, "age": 27},
    {"name": "Krpić", "height": 183, "weight": 81, "position": "védő", "goals": 2, "age": 30},
    {"name": "Anton", "height": 180, "weight": 77, "position": "középpályás", "goals": 1, "age": 26},
    {"name": "Lukić", "height": 187, "weight": 79, "position": "középpályás", "goals": 1, "age": 31},
    {"name": "Vitális", "height": 182, "weight": 76, "position": "középpályás", "goals": 1, "age": 24}
]



# Checkbox csoport címkékkel
teams = ["Ferencváros","Paks","Puskás Akadémia", "Videoton", "Debrecen", "Kecskemét", "Diósgyőr", "MTK Budapest", "Zalaegerszeg", "Újpest", "Nyíregyháza", "Győri ETO"]
checkbox = CheckboxGroup(labels=teams, active=[])


# Kapusok adatai
ferencvaros_kapus = [{"name": "Dibusz", "height": 186, "weight": 81}]

paks_kapus = [{"name": "Szappanos", "height": 190, "weight": 85}]

puskas_kapus = [{"name": "Pécsi", "height": 187, "weight": 80}]

fehervar_kapus = [{"name": "Dala", "height": 190, "weight": 88}]

debrecen_kapus = [{"name": "Megyeri", "height": 188, "weight": 84}]

kecskemet_kapus = [{"name": "Varga Bence", "height": 192, "weight": 84}]

diosgyor_kapus = [{"name": "Danilović", "height": 191, "weight": 83} ]

mtk_kapus = [{"name": "Demjén", "height": 186, "weight": 75}]

zte_kapus = [{"name": "Gundel-Takécs", "height": 200, "weight": 95}]

ujpest_kapus = [{"name": "Banai", "height": 188, "weight": 82}]

nyiregyhaza_kapus = [{"name": "Tóth", "height": 189, "weight": 84}]

gyor_kapus = [{"name": "Petrás", "height": 192, "weight": 87}]

# Diagram adatok forrása
ferencvaros_heights = [player["height"] for player in ferencvaros_players]
ferencvaros_weights = [player["weight"] for player in ferencvaros_players]
paks_heights = [player["height"] for player in paks_players]
paks_weights = [player["weight"] for player in paks_players]
puskas_heights = [player["height"] for player in puskas_players]
puskas_weights = [player["weight"] for player in puskas_players]
fehervar_heights = [player["height"] for player in fehervar_players]
fehervar_weights = [player["weight"] for player in fehervar_players]
debrecen_heights = [player["height"] for player in debrecen_players]
debrecen_weights = [player["weight"] for player in debrecen_players]
kecskemet_heights = [player["height"] for player in kecskemet_players]
kecskemet_weights = [player["weight"] for player in kecskemet_players]
diosgyor_heights = [player["height"] for player in diosgyor_players]
diosgyor_weights = [player["weight"] for player in diosgyor_players]
mtk_heights = [player["height"] for player in mtk_players]
mtk_weights = [player["weight"] for player in mtk_players]
zte_heights = [player["height"] for player in zte_players]
zte_weights = [player["weight"] for player in zte_players]
ujpest_heights = [player["height"] for player in ujpest_players]
ujpest_weights = [player["weight"] for player in ujpest_players]
nyiregyhaza_heights = [player["height"] for player in nyiregyhaza_players]
nyiregyhaza_weights = [player["weight"] for player in nyiregyhaza_players]
gyor_heights = [player["height"] for player in gyor_players]
gyor_weights = [player["weight"] for player in gyor_players]
ferencvaros_kapus_heights = [player["height"] for player in ferencvaros_kapus]
ferencvaros_kapus_weights = [player["weight"] for player in ferencvaros_kapus]
paks_kapus_heights = [player["height"] for player in paks_kapus]
paks_kapus_weights = [player["weight"] for player in paks_kapus]
puskas_kapus_heights = [player["height"] for player in puskas_kapus]
puskas_kapus_weights = [player["weight"] for player in puskas_kapus]
fehervar_kapus_heights = [player["height"] for player in fehervar_kapus]
fehervar_kapus_weights = [player["weight"] for player in fehervar_kapus]
debrecen_kapus_heights = [player["height"] for player in debrecen_kapus]
debrecen_kapus_weights = [player["weight"] for player in debrecen_kapus]
kecskemet_kapus_heights = [player["height"] for player in kecskemet_kapus]
kecskemet_kapus_weights = [player["weight"] for player in kecskemet_kapus]
diosgyor_kapus_heights = [player["height"] for player in diosgyor_kapus]
diosgyor_kapus_weights = [player["weight"] for player in diosgyor_kapus]
mtk_kapus_heights = [player["height"] for player in mtk_kapus]
mtk_kapus_weights = [player["weight"] for player in mtk_kapus]
zte_kapus_heights = [player["height"] for player in zte_kapus]
zte_kapus_weights = [player["weight"] for player in zte_kapus]
ujpest_kapus_heights = [player["height"] for player in ujpest_kapus]
ujpest_kapus_weights = [player["weight"] for player in ujpest_kapus]
nyiregyhaza_kapus_heights = [player["height"] for player in nyiregyhaza_kapus]
nyiregyhaza_kapus_weights = [player["weight"] for player in nyiregyhaza_kapus]
gyor_kapus_heights = [player["height"] for player in gyor_kapus]
gyor_kapus_weights = [player["weight"] for player in gyor_kapus]


source_ferencvaros = ColumnDataSource(data=dict(x=ferencvaros_heights, y=ferencvaros_weights))
source_paks = ColumnDataSource(data=dict(x=paks_heights, y=paks_weights))
source_puskas = ColumnDataSource(data=dict(x=puskas_heights, y=puskas_weights))
source_videoton = ColumnDataSource(data=dict(x=fehervar_heights, y=fehervar_weights))
source_debrecen = ColumnDataSource(data=dict(x=debrecen_heights, y=debrecen_weights))
source_kecskemet = ColumnDataSource(data=dict(x=kecskemet_heights, y=kecskemet_weights))
source_diosgyor = ColumnDataSource(data=dict(x=diosgyor_heights, y=diosgyor_weights))
source_mtk = ColumnDataSource(data=dict(x=mtk_heights, y=mtk_weights))
source_zte = ColumnDataSource(data=dict(x=zte_heights, y=zte_weights))
source_ujpest = ColumnDataSource(data=dict(x=ujpest_heights, y=ujpest_weights))
source_nyiregyhaza = ColumnDataSource(data=dict(x=nyiregyhaza_heights, y=nyiregyhaza_weights))
source_gyor = ColumnDataSource(data=dict(x=gyor_heights, y=gyor_weights))
source_ferencvaros_kapus = ColumnDataSource(data=dict(x=ferencvaros_kapus_heights, y=ferencvaros_kapus_weights))
source_paks_kapus = ColumnDataSource(data=dict(x=paks_kapus_heights, y=paks_kapus_weights))
source_puskas_kapus = ColumnDataSource(data=dict(x=puskas_kapus_heights, y=puskas_kapus_weights))
source_fehervar_kapus = ColumnDataSource(data=dict(x=fehervar_kapus_heights, y=fehervar_kapus_weights))
source_debrecen_kapus = ColumnDataSource(data=dict(x=debrecen_kapus_heights, y=debrecen_kapus_weights))
source_kecskemet_kapus = ColumnDataSource(data=dict(x=kecskemet_kapus_heights, y=kecskemet_kapus_weights))
source_diosgyor_kapus = ColumnDataSource(data=dict(x=diosgyor_kapus_heights, y=diosgyor_kapus_weights))
source_mtk_kapus = ColumnDataSource(data=dict(x=mtk_kapus_heights, y=mtk_kapus_weights))
source_zte_kapus = ColumnDataSource(data=dict(x=zte_kapus_heights, y=zte_kapus_weights))
source_ujpest_kapus = ColumnDataSource(data=dict(x=ujpest_kapus_heights, y=ujpest_kapus_weights))
source_nyiregyhaza_kapus = ColumnDataSource(data=dict(x=nyiregyhaza_kapus_heights, y=nyiregyhaza_kapus_weights))
source_gyor_kapus = ColumnDataSource(data=dict(x=gyor_kapus_heights, y=gyor_kapus_weights))

# Diagram létrehozása és beállítása
plot = figure(
    title="NB1-es csapatok játékosainak magassága és tömege a 2024/25-ös szezonban",
    x_axis_label="Magasság (cm)",
    y_axis_label="Tömeg (kg)",
    width=800,
    height=500,
    toolbar_location=None,
    background_fill_color="black",
    border_fill_color="black"
)

# Tengelyek és cím színeinek módosítása a fekete háttérhez
plot.title.text_color = "white"
plot.xaxis.axis_label_text_color = "white"
plot.yaxis.axis_label_text_color = "white"
plot.xaxis.major_label_text_color = "white"
plot.yaxis.major_label_text_color = "white"

# Alapértelmezett rejtett scatter plot a csapatoknak

scatter_ferencvaros = plot.circle('x', 'y', source=source_ferencvaros, size=22, color="green", visible=False)

scatter_paks = plot.circle('x', 'y', source=source_paks, size=18, color="purple", visible=False)

scatter_puskas = plot.circle('x', 'y', source=source_puskas, size=18, color="orange", visible=False)

scatter_videoton = plot.circle('x', 'y', source=source_videoton, size=14, color="teal", visible=False)

scatter_debrecen = plot.circle('x', 'y', source=source_debrecen, size=14, color="pink", visible=False)

scatter_kecskemet = plot.circle('x', 'y', source=source_kecskemet, size=10, color="red", visible=False)

scatter_diosgyor = plot.circle('x', 'y', source=source_diosgyor, size=10, color="gray", visible=False)

scatter_mtk = plot.circle('x', 'y', source=source_mtk, size=10, color="blue", visible=False)

scatter_zte = plot.circle('x', 'y', source=source_zte, size=10, color="olive", visible=False)

scatter_ujpest = plot.circle('x', 'y', source=source_ujpest, size=10, color="yellow", visible=False)

scatter_nyiregyhaza = plot.circle('x', 'y', source=source_nyiregyhaza, size=10, color="brown", visible=False)

scatter_gyor = plot.circle('x', 'y', source=source_gyor, size=10, color="cyan", visible=False)

scatter_ferencvaros_kapus = plot.triangle('x', 'y', source=source_ferencvaros_kapus, size=22, color="green", visible=False)

scatter_paks_kapus = plot.triangle('x', 'y', source=source_paks_kapus, size=18, color="purple", visible=False)

scatter_puskas_kapus = plot.triangle('x', 'y', source=source_puskas_kapus, size=18, color="orange", visible=False)

scatter_fehervar_kapus = plot.triangle('x', 'y', source=source_fehervar_kapus, size=14, color="teal", visible=False)

scatter_debrecen_kapus = plot.triangle('x', 'y', source=source_debrecen_kapus, size=14, color="pink", visible=False)

scatter_kecskemet_kapus = plot.triangle('x', 'y', source=source_kecskemet_kapus, size=15, color="red", visible=False)

scatter_diosgyor_kapus = plot.triangle('x', 'y', source=source_diosgyor_kapus, size=15, color="gray", visible=False)

scatter_mtk_kapus = plot.triangle('x', 'y', source=source_mtk_kapus, size=15, color="blue", visible=False)

scatter_zte_kapus = plot.triangle('x', 'y', source=source_zte_kapus, size=15, color="olive", visible=False)

scatter_ujpest_kapus = plot.triangle('x', 'y', source=source_ujpest_kapus, size=15, color="yellow", visible=False)

scatter_nyiregyhaza_kapus = plot.triangle('x', 'y', source=source_nyiregyhaza_kapus, size=15, color="brown", visible=False)

scatter_gyor_kapus = plot.triangle('x', 'y', source=source_gyor_kapus, size=15, color="cyan", visible=False)


# JavaScript callback a checkboxhoz
checkbox.js_on_change("active", CustomJS(args=dict(scatter_ferencvaros=scatter_ferencvaros, scatter_paks=scatter_paks, scatter_puskas=scatter_puskas,
                                                   scatter_videoton=scatter_videoton, scatter_debrecen=scatter_debrecen, scatter_kecskemet=scatter_kecskemet,
                                                   scatter_diosgyor=scatter_diosgyor, scatter_mtk=scatter_mtk, scatter_zte=scatter_zte, scatter_ujpest=scatter_ujpest,
                                                   scatter_nyiregyhaza=scatter_nyiregyhaza, scatter_gyor=scatter_gyor, scatter_ferencvaros_kapus=scatter_ferencvaros_kapus,
                                                   scatter_paks_kapus=scatter_paks_kapus, scatter_puskas_kapus=scatter_puskas_kapus, scatter_fehervar_kapus=scatter_fehervar_kapus,
                                                   scatter_debrecen_kapus=scatter_debrecen_kapus, scatter_kecskemet_kapus=scatter_kecskemet_kapus, scatter_diosgyor_kapus=scatter_diosgyor_kapus,
                                                   scatter_mtk_kapus=scatter_mtk_kapus, scatter_zte_kapus=scatter_zte_kapus, scatter_ujpest_kapus=scatter_ujpest_kapus,
                                                   scatter_nyiregyhaza_kapus=scatter_nyiregyhaza_kapus, scatter_gyor_kapus=scatter_gyor_kapus), code="""
    // Ellenőrizzük, hogy a 'Ferencváros' (0. index) be van-e jelölve
    scatter_ferencvaros.visible = cb_obj.active.includes(0);
    scatter_paks.visible = cb_obj.active.includes(1);
    scatter_puskas.visible = cb_obj.active.includes(2);
    scatter_videoton.visible = cb_obj.active.includes(3);
    scatter_debrecen.visible = cb_obj.active.includes(4);
    scatter_kecskemet.visible = cb_obj.active.includes(5);
    scatter_diosgyor.visible = cb_obj.active.includes(6);
    scatter_mtk.visible = cb_obj.active.includes(7);
    scatter_zte.visible = cb_obj.active.includes(8);
    scatter_ujpest.visible = cb_obj.active.includes(9);
    scatter_nyiregyhaza.visible = cb_obj.active.includes(10);
    scatter_gyor.visible = cb_obj.active.includes(11);
    scatter_ferencvaros_kapus.visible = cb_obj.active.includes(0);
    scatter_paks_kapus.visible = cb_obj.active.includes(1);
    scatter_puskas_kapus.visible = cb_obj.active.includes(2);
    scatter_fehervar_kapus.visible = cb_obj.active.includes(3);
    scatter_debrecen_kapus.visible = cb_obj.active.includes(4);
    scatter_kecskemet_kapus.visible = cb_obj.active.includes(5);
    scatter_diosgyor_kapus.visible = cb_obj.active.includes(6);
    scatter_mtk_kapus.visible = cb_obj.active.includes(7);
    scatter_zte_kapus.visible = cb_obj.active.includes(8);
    scatter_ujpest_kapus.visible = cb_obj.active.includes(9);
    scatter_nyiregyhaza_kapus.visible = cb_obj.active.includes(10);
    scatter_gyor_kapus.visible = cb_obj.active.includes(11);
"""))

ferencvaros_goalses = [player["goals"] for player in ferencvaros_players]
ferencvaros_ages = [player["age"] for player in ferencvaros_players]

paks_goalses = [player["goals"] for player in paks_players]
paks_ages = [player["age"] for player in paks_players]

puskas_goalses = [player["goals"] for player in puskas_players]
puskas_ages = [player["age"] for player in puskas_players]

fehervar_goalses = [player["goals"] for player in fehervar_players]
fehervar_ages = [player["age"] for player in fehervar_players]

debrecen_goalses = [player["goals"] for player in debrecen_players]
debrecen_ages = [player["age"] for player in debrecen_players]

kecskemet_goalses = [player["goals"] for player in kecskemet_players]
kecskemet_ages = [player["age"] for player in kecskemet_players]

diosgyor_goalses = [player["goals"] for player in diosgyor_players]
diosgyor_ages = [player["age"] for player in diosgyor_players]

mtk_goalses = [player["goals"] for player in mtk_players]
mtk_ages = [player["age"] for player in mtk_players]

zte_goalses = [player["goals"] for player in zte_players]
zte_ages = [player["age"] for player in zte_players]

ujpest_goalses = [player["goals"] for player in ujpest_players]
ujpest_ages = [player["age"] for player in ujpest_players]

nyiregyhaza_goalses = [player["goals"] for player in nyiregyhaza_players]
nyiregyhaza_ages = [player["age"] for player in nyiregyhaza_players]

gyor_goalses = [player["goals"] for player in gyor_players]
gyor_ages = [player["age"] for player in gyor_players]


source_ferencvaros = ColumnDataSource(data=dict(x=ferencvaros_goalses, y=ferencvaros_ages))
source_paks = ColumnDataSource(data=dict(x=paks_goalses, y=paks_ages))
source_puskas = ColumnDataSource(data=dict(x=puskas_goalses, y=puskas_ages))
source_videoton = ColumnDataSource(data=dict(x=fehervar_goalses, y=fehervar_ages))
source_debrecen = ColumnDataSource(data=dict(x=debrecen_goalses, y=debrecen_ages))
source_kecskemet = ColumnDataSource(data=dict(x=kecskemet_goalses, y=kecskemet_ages))
source_diosgyor = ColumnDataSource(data=dict(x=diosgyor_goalses, y=diosgyor_ages))
source_mtk = ColumnDataSource(data=dict(x=mtk_goalses, y=mtk_ages))
source_zte = ColumnDataSource(data=dict(x=zte_goalses, y=zte_ages))
source_ujpest = ColumnDataSource(data=dict(x=ujpest_goalses, y=ujpest_ages))
source_nyiregyhaza = ColumnDataSource(data=dict(x=nyiregyhaza_goalses, y=nyiregyhaza_ages))
source_gyor = ColumnDataSource(data=dict(x=gyor_goalses, y=gyor_ages))


plot2 = figure(
    title="NB1-es csapatok játékosainak gólszáma és életkora a 2024/25-ös szezonban",
    x_axis_label="Gólok száma",
    y_axis_label="Életkor (év)",
    width=800,
    height=500,
    toolbar_location=None,
    background_fill_color="black",
    border_fill_color="black"
)

plot2.title.text_color = "white"
plot2.xaxis.axis_label_text_color = "white"
plot2.yaxis.axis_label_text_color = "white"
plot2.xaxis.major_label_text_color = "white"
plot2.yaxis.major_label_text_color = "white"


scatter_ferencvaros = plot2.scatter(
    'x', 'y', source=source_ferencvaros,
    size=22, color="green", marker="circle", visible=False
)

scatter_paks = plot2.scatter(
    'x', 'y', source=source_paks,
    size=19, color="purple", marker="circle", visible=False
)

scatter_puskas = plot2.scatter(
    'x', 'y', source=source_puskas,
    size=16, color="orange", marker="circle", visible=False
)

scatter_videoton = plot2.scatter(
    'x', 'y', source=source_videoton,
    size=16, color="teal", marker="circle", visible=False
)

scatter_debrecen = plot2.scatter(
    'x', 'y', source=source_debrecen,
    size=16, color="pink", marker="circle", visible=False
)

scatter_kecskemet = plot2.scatter(
    'x', 'y', source=source_kecskemet,
    size=13, color="red", marker="circle", visible=False
)

scatter_diosgyor = plot2.scatter(
    'x', 'y', source=source_diosgyor,
    size=13, color="gray", marker="circle", visible=False
)

scatter_mtk = plot2.scatter(
    'x', 'y', source=source_mtk,
    size=13, color="blue", marker="circle", visible=False
)

scatter_zte = plot2.scatter(
    'x', 'y', source=source_zte,
    size=13, color="olive", marker="circle", visible=False
)

scatter_ujpest = plot2.scatter(
    'x', 'y', source=source_ujpest,
    size=13, color="yellow", marker="circle", visible=False
)

scatter_nyiregyhaza = plot2.scatter(
    'x', 'y', source=source_nyiregyhaza,
    size=13, color="brown", marker="circle", visible=False
)

scatter_gyor = plot2.scatter(
    'x', 'y', source=source_gyor,
    size=10, color="cyan", marker="circle", visible=False
)


checkbox2 = CheckboxGroup(
    labels=checkbox.labels,
    active=checkbox.active
)


checkbox2.js_on_change(
    "active",
    CustomJS(
        args=dict(
            scatter_ferencvaros=scatter_ferencvaros,
            scatter_paks=scatter_paks,
            scatter_puskas=scatter_puskas,
            scatter_videoton=scatter_videoton,
            scatter_debrecen=scatter_debrecen,
            scatter_kecskemet=scatter_kecskemet,
            scatter_diosgyor=scatter_diosgyor,
            scatter_mtk=scatter_mtk,
            scatter_zte=scatter_zte,
            scatter_ujpest=scatter_ujpest,
            scatter_nyiregyhaza=scatter_nyiregyhaza,
            scatter_gyor=scatter_gyor
        ),
        code="""
            scatter_ferencvaros.visible = cb_obj.active.includes(0);
            scatter_paks.visible = cb_obj.active.includes(1);
            scatter_puskas.visible = cb_obj.active.includes(2);
            scatter_videoton.visible = cb_obj.active.includes(3);
            scatter_debrecen.visible = cb_obj.active.includes(4);
            scatter_kecskemet.visible = cb_obj.active.includes(5);
            scatter_diosgyor.visible = cb_obj.active.includes(6);
            scatter_mtk.visible = cb_obj.active.includes(7);
            scatter_zte.visible = cb_obj.active.includes(8);
            scatter_ujpest.visible = cb_obj.active.includes(9);
            scatter_nyiregyhaza.visible = cb_obj.active.includes(10);
            scatter_gyor.visible = cb_obj.active.includes(11);
        """
    )
)



tab1 = TabPanel(
    child=column(map_figure, bar_figure),
    title="Térkép"
)

tab2 = TabPanel(
    child=column(checkbox, plot),
    title="Magasság-tömeg"
)

tab3 = TabPanel(
    child=column(checkbox2, plot2),
    title="Gólszám-életkor"
)

tabs = Tabs(tabs=[tab1, tab2, tab3])

html = file_html(tabs, INLINE, "Dashboard")

app = QApplication(sys.argv)

window = QMainWindow()
window.resize(1400, 900)

browser = QWebEngineView()
browser.setHtml(html)

with open("dashboard.html", "w", encoding="utf-8") as f:
    f.write(html)
browser.load(QUrl.fromLocalFile(os.path.abspath("dashboard.html")))

window.setCentralWidget(browser)
window.show()

sys.exit(app.exec())