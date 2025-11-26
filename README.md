# 0. Project Context & Data Overview

## Project Goal

We are building a Visualization Prototype for the course Programming for Data Science. The objective is to apply the Knowledge Discovery in Databases (KDD) process to a real-world dataset.

**Deliverable**: An interactive Dash web application (not just a static notebook).

**Core Requirement**: The dashboard must display 4 distinct indicators (metrics) derived from the data.

**Key Constraint**: The solution must be modular (encapsulated functions) and collaborative.

## The Data: Significant Volcanic Eruptions

We are working with the NCEI Volcano Events Dataset (`volcano-events.tsv`). This dataset tracks significant volcanic eruptions throughout history that meet specific criteria (e.g., caused fatalities, moderate damage, or had a VEI of 6+).

### Key Columns & Definitions:

*   **Temporal**: `Year` (Critical), `Mo` (Month), `Dy` (Day). Note: Years can be negative (BC).
*   **Geospatial**: `Latitude`, `Longitude` (for mapping), `Country`, `Location` (Region), `Elevation` (m).
*   **Volcanic Metrics**:
    *   `Name`: Name of the volcano.
    *   `Type`: Morphology (e.g., Stratovolcano, Caldera, Shield volcano).
    *   `VEI`: Volcanic Explosivity Index (0-8 scale). Crucial for intensity analysis.
    *   `Agent`: The specific cause of damage (e.g., T=Tsunami, P=Pyroclastic flow).
*   **Impact Metrics** (The "Y" variables for our charts):
    *   `Deaths` / `Total Deaths`: Confirmed fatalities.
    *   `Injuries` / `Total Injuries`: Non-fatal casualties.
    *   `Damage ($Mil)` / `Total Damage ($Mil)`: Economic cost in Millions USD.
    *   `Houses Destroyed`: Physical infrastructure damage.

**Note**: Many impact columns contain NaN (missing values), implying 0 or unknown. We must decide how to handle these in `src/data_loader.py`.

# 1. Roles & Responsibilities

# Volcano Insights Dashboard: Development Plan

This document outlines the development plan for the Volcano Insights Dashboard. Each role is assigned to a specific part of the Next.js/React application, allowing for parallel work streams.

---

## Person 1: Data Lead & Architect

**Focus:** Data Integrity and Project Structure


**Key Tasks:**
- Verify and maintain the `volcano-events.tsv` dataset.
- Ensure data consistency. Handle NaNs and standardize column names in `load_clean_data()`.
- Return a clean pandas DataFrame for use by other components.

---

## Person 2: UI Lead (The Dashboarder)

**Focus:** Main Layout and Interactivity


**Key Tasks:**
- Develop the main dashboard layout in `src/layout.py` using `dash.html` and `dash.dcc`.
- Implement the master state management for filters (Year Range, Country) within `app.py` using Dash Callbacks.
- Create the UI for the filters, including the year range slider and country dropdown.
- Pass the filtered data down to the individual chart components via callbacks.
- Integrate the components created by Persons 3-6 into the main dashboard grid.

---

## Person 3: Spatial Analyst (The Geographer)

**Focus:** Geographic Data Visualization


**Key Tasks:**
- Implement the `render_map` function using `px.scatter_geo` to plot volcanoes by latitude and longitude.
- Use the `VEI` data to control the size of the points on the scatter plot.
- Configure the tooltip to display relevant information like volcano name, country, type, and VEI.
- Ensure the chart is responsive and fits well within the dashboard layout.
- **Insight Question to Answer:** Where are the 'Ring of Fire' hot spots?

---

## Person 4: Temporal Analyst (The Historian)

**Focus:** Time-Series Analysis


**Key Tasks:**
- Create the `render_time_series` function.
- Process the filtered data to aggregate the number of eruptions by century or year.
- Use `px.histogram` or `px.line` to display the frequency of eruptions over time.
- Format the X-axis labels to be readable.
- Design a tooltip that shows the exact count when hovered.
- **Insight Question to Answer:** Are we recording more eruptions now than in the past?

---

## Person 5: Impact Analyst (The Statistician)

**Focus:** Human and Economic Impact Analysis


**Key Tasks:**
- Develop the `render_impact_chart` function.
- Filter and sort the data to find the top 10 deadliest events based on `Deaths`.
- Implement a horizontal `px.bar` chart to display these events, with the length of the bar representing the number of deaths.
- Label the Y-axis with the volcano name and year.
- Create a detailed tooltip that shows exact deaths and the country of the event.
- **Insight Question to Answer:** Which specific eruptions have been the most devastating?

---

## Person 6: Correlation Analyst (The Scientist)

**Focus:** Statistical Correlation Analysis


**Key Tasks:**
- Build the `render_correlation_plot` function.
- Implement a `px.scatter` plot to graph VEI against impact metrics.
- Use a logarithmic scale for the Y-axis to handle the wide range of values in deaths and damages.
- Add logic to switch the Y-axis metric between 'Deaths' and 'Damage_Millions' (controlled by callbacks).
- Ensure rows with zero or null impact are excluded from the plot to prevent log-scale errors.
- **Insight Question to Answer:** Do bigger explosions always mean more destruction, or does context matter more?

---


# 2. Shared Code Conventions

*   **Variable Names**: Use `snake_case` (e.g., `volcano_df`, `death_count`).
*   **DataFrame**: Everyone expects a DataFrame named `df` with these standard columns (renamed by Person 1):
    *   `Year`, `Name`, `Country`, `Type`, `VEI`, `Deaths`, `Damage_Millions`, `Latitude`, `Longitude`
*   **Testing**: Every component file must have a `if __name__ == "__main__":` block that generates a test plot using a sample dataframe.

# 3. Git Workflow

1.  Person 1 pushes the "Skeleton" (folder structure).
2.  Everyone clones the repo.
3.  Everyone creates a branch (e.g., `feature/map-view`).
4.  Everyone pushes their specific file to `src/components/` or `src/`.
5.  Person 1 merges the branches into `main`.
