# Local dashboard

Double-click **Start Dashboard.cmd**, then open http://127.0.0.1:8504.
Keep its window open while using the dashboard. MySQL must be running on this computer on port 3306, with the imported `olist` database.

Local credentials are read from `.env.local` (excluded from Git). The launcher forces the host to `127.0.0.1` so cloud settings cannot redirect this local session. The dashboard uses the read-only account. Stop it with Ctrl+C in its window.

## Rename navigation labels

Edit the visible text of the four navigation links in `marketplace/index.html` (inside `<nav aria-label="Workspace">`). Keep `href` and `data-view` unchanged.

Edit the matching first string in the `views` object at the top of `marketplace/app.js` to change the page heading and browser title too. Example: change `overview: ["Overview", ...]` to `overview: ["Summary", ...]`.

Refresh the browser after saving. These edits affect the local website; publishing is a separate step.

## SQL and charts

The SQL panel shows parameterized query definitions and bound filter values for the displayed result, including cached results. Theme changes, selecting a chart point and zooming happen in the browser and do not execute SQL. Exports reuse the report query.

Monthly orders on Overview and reports R01 and R05 support data-range zoom: drag across months, double-click a point, or choose From/Through months and click Zoom to range. The chart axes rescale to the selected values. Reset zoom (or Escape while focused in the chart) restores all months. Shift+Enter on a focused point zooms around it. A single click still shows exact values. Other reports keep their existing interactions without zoom controls.
