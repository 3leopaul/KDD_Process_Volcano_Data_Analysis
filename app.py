from dash import Dash, html, dcc, Input, Output
from src.data_loader import load_data
import src.components.impact_analysis as impact

# Charger les données une seule fois
df = load_data()

# Initialisation de l'app
app = Dash(__name__)

# --- Préparation des filtres ---
year_min = int(df["Year"].min()) if not df.empty else 0
year_max = int(df["Year"].max()) if not df.empty else 2024
country_options = [{"label": c, "value": c} for c in sorted(df["Country"].dropna().unique())] if not df.empty else []

app.layout = html.Div(
    children=[
        html.H1("Volcano Impact Dashboard – Person 5 (Impact Analyst)", style={'textAlign': 'center'}),
        html.P("Exploring human and economic impact of significant volcanic eruptions.", style={'textAlign': 'center'}),

        # ---------- Filtres globaux ----------
        html.Div(
            children=[
                html.Div(
                    children=[
                        html.Label("Year range"),
                        dcc.RangeSlider(
                            id="year-slider",
                            min=year_min,
                            max=year_max,
                            value=[year_min, year_max],
                            step=10,  # Pas de 10 ans pour alléger
                            marks={str(y): str(y) for y in range(year_min, year_max + 1, 500)},
                            tooltip={"placement": "bottom", "always_visible": True},
                        ),
                    ],
                    style={"flex": "2", "marginRight": "30px"},
                ),
                html.Div(
                    children=[
                        html.Label("Country"),
                        dcc.Dropdown(
                            id="country-dropdown",
                            options=country_options,
                            placeholder="All countries",
                            value=None,
                            clearable=True,
                        ),
                    ],
                    style={"flex": "1"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "marginBottom": "30px", "padding": "20px", "backgroundColor": "#f9f9f9", "borderRadius": "10px"},
        ),

        # ---------- Onglets ----------
        dcc.Tabs(
            id="tabs",
            value="tab-overview",
            children=[
                # Tab 1 : Overview
                dcc.Tab(
                    label="Overview – Fatalities",
                    value="tab-overview",
                    children=[
                        html.Div(
                            children=[
                                dcc.Graph(id="top10-deadliest-eruptions"),
                                dcc.Graph(id="top10-deadliest-volcanoes"),
                                dcc.Graph(id="top10-deadliest-countries"),
                                dcc.Graph(id="deaths-over-time"),
                            ],
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "padding": "20px"},
                        )
                    ],
                ),

                # Tab 2 : Regions & Volcanoes
                dcc.Tab(
                    label="Regions & Volcanoes",
                    value="tab-regions",
                    children=[
                        html.Div(
                            children=[
                                dcc.Graph(id="top10-deadliest-regions"),
                                dcc.Graph(id="region-volcano-sunburst"),
                                dcc.Graph(id="volcano-treemap"),
                                dcc.Graph(id="volcano-donut"),
                            ],
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "padding": "20px"},
                        )
                    ],
                ),

                # Tab 3 : Injuries & Ratios
                dcc.Tab(
                    label="Injuries & Ratios",
                    value="tab-injuries",
                    children=[
                        html.Div(
                            children=[
                                dcc.Graph(id="deaths-vs-injuries-scatter"),
                                dcc.Graph(id="deaths-vs-injuries-bubble"),
                                dcc.Graph(id="injury-ratio-bar"),
                                dcc.Graph(id="injury-ratio-scatter"),
                            ],
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "padding": "20px"},
                        )
                    ],
                ),

                # Tab 4 : Distributions & Risk
                dcc.Tab(
                    label="Distributions & Risk",
                    value="tab-distributions",
                    children=[
                        html.Div(
                            children=[
                                dcc.Graph(id="death-boxplot"),
                                dcc.Graph(id="death-stripplot"), # Mapped to boxplot_by_type
                                dcc.Graph(id="pareto-chart"),
                                dcc.Graph(id="loglog-plot"),
                                dcc.Graph(id="correlation-heatmap"),
                            ],
                            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "20px", "padding": "20px"},
                        )
                    ],
                ),
            ],
        ),
    ],
    style={"width": "95%", "margin": "0 auto", "fontFamily": "Arial, sans-serif"},
)


# ---------- Callback ----------

@app.callback(
    [
        Output("top10-deadliest-eruptions", "figure"),
        Output("top10-deadliest-volcanoes", "figure"),
        Output("top10-deadliest-countries", "figure"),
        Output("deaths-over-time", "figure"),
        Output("top10-deadliest-regions", "figure"),
        Output("region-volcano-sunburst", "figure"),
        Output("volcano-treemap", "figure"),
        Output("volcano-donut", "figure"),
        Output("deaths-vs-injuries-scatter", "figure"),
        Output("deaths-vs-injuries-bubble", "figure"),
        Output("injury-ratio-bar", "figure"),
        Output("injury-ratio-scatter", "figure"),
        Output("death-boxplot", "figure"),
        Output("death-stripplot", "figure"),
        Output("pareto-chart", "figure"),
        Output("loglog-plot", "figure"),
        Output("correlation-heatmap", "figure"),
    ],
    [
        Input("country-dropdown", "value"),
        Input("year-slider", "value"),
    ],
)
def update_all_figures(selected_country, year_range):
    # 1. Filtrage des données
    dff = df.copy()

    if year_range is not None:
        start, end = year_range
        dff = dff[(dff["Year"] >= start) & (dff["Year"] <= end)]

    if selected_country:
        dff = dff[dff["Country"] == selected_country]

    # Sécurité : Si le filtre renvoie vide, on évite les erreurs (ou on renvoie des graphs vides)
    # Ici, je choisis de renvoyer le df complet si vide pour montrer quelque chose, 
    # mais tu peux changer ça.
    if dff.empty and (selected_country or year_range):
        # Optionnel : garder le df vide pour montrer "Aucune donnée"
        # dff = df # Décommente si tu préfères un fallback
        pass 

    # 2. Génération des figures via le module 'impact'
    
    # Tab 1
    fig1 = impact.render_top10_deadliest_eruptions(dff)
    fig2 = impact.render_top10_deadliest_volcanoes(dff)
    fig3 = impact.render_top10_deadliest_countries(dff)
    fig4 = impact.render_deaths_over_time(dff)

    # Tab 2
    fig5 = impact.render_top10_deadliest_regions(dff)
    fig6 = impact.render_region_volcano_sunburst(dff)
    fig7 = impact.render_deadliest_volcanoes_treemap(dff)
    fig8 = impact.render_deadliest_volcanoes_donut(dff)

    # Tab 3
    fig9 = impact.render_deaths_vs_injuries_scatter(dff)
    fig10 = impact.render_deaths_vs_injuries_bubble(dff)
    fig11 = impact.render_top10_injury_ratio(dff)
    fig12 = impact.render_injury_ratio_scatter(dff)

    # Tab 4
    fig13 = impact.render_death_boxplot(dff)
    fig14 = impact.render_death_boxplot_by_type(dff) # Correspond à ton ID 'stripplot'
    fig15 = impact.render_pareto_chart(dff)
    fig16 = impact.render_loglog_heavytail(dff)
    fig17 = impact.render_correlation_heatmap(dff)

    return (
        fig1, fig2, fig3, fig4,
        fig5, fig6, fig7, fig8,
        fig9, fig10, fig11, fig12,
        fig13, fig14, fig15, fig16, fig17
    )

if __name__ == "__main__":
    app.run(debug=True)