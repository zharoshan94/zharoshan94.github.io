const FORECAST_API_URL = "https://api.open-meteo.com/v1/forecast?latitude=27.7172&longitude=85.3240&current=temperature_2m&hourly=temperature_2m,precipitation&models=ecmwf_ifs025&forecast_days=7&timezone=Asia%2FKathmandu";
const FORECAST_PLOTLY_URL = "https://cdn.jsdelivr.net/npm/plotly.js@3.6.0/dist/plotly.min.js";

const forecastRoot = document.querySelector("[data-forecast-root]");
if (forecastRoot) {
  const forecastStatus = forecastRoot.querySelector("[data-forecast-status]");
  const forecastChart = forecastRoot.querySelector("[data-forecast-chart]");

  function formatForecastTime(value) {
    return new Date(value).toLocaleString("en-GB", {
      weekday: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  }

  function renderForecast(forecast) {
    Plotly.newPlot(forecastChart, [
      {
        x: forecast.hourly.time,
        y: forecast.hourly.temperature_2m,
        name: "2-metre temperature",
        type: "scatter",
        mode: "lines",
        line: { color: "#d45b45", width: 2.5 },
        hovertemplate: "%{y:.1f} °C<extra>2-metre temperature</extra>"
      },
      {
        x: forecast.hourly.time,
        y: forecast.hourly.precipitation,
        name: "Precipitation rate",
        type: "bar",
        yaxis: "y2",
        marker: { color: "#2f7f9f", opacity: 0.62 },
        hovertemplate: "%{y:.2f} mm/h<extra>Precipitation rate</extra>"
      }
    ], {
      margin: { t: 24, r: 58, b: 72, l: 58 },
      paper_bgcolor: "#ffffff",
      plot_bgcolor: "#f7fbfc",
      hovermode: "x unified",
      legend: { orientation: "h", y: 1.12, x: 0 },
      xaxis: { title: "Local time", tickformat: "%a %d %b<br>%H:%M", gridcolor: "#d9e7eb" },
      yaxis: { title: "Temperature (°C)", gridcolor: "#d9e7eb" },
      yaxis2: { title: "Precipitation (mm/h)", overlaying: "y", side: "right", rangemode: "tozero", gridcolor: "transparent" }
    }, {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["lasso2d", "select2d"]
    });

    forecastStatus.textContent = "Updated " + formatForecastTime(forecast.current.time) + " · ECMWF IFS 0.25°";
  }

  const plotlyScript = document.createElement("script");
  plotlyScript.src = FORECAST_PLOTLY_URL;
  plotlyScript.onload = function() {
    fetch(FORECAST_API_URL)
      .then(function(response) {
        if (!response.ok) {
          throw new Error("Forecast request failed");
        }
        return response.json();
      })
      .then(renderForecast)
      .catch(function() {
        forecastStatus.textContent = "The forecast is temporarily unavailable. Please try again later.";
      });
  };
  plotlyScript.onerror = function() {
    forecastStatus.textContent = "The chart library could not be loaded.";
  };
  document.head.appendChild(plotlyScript);
}