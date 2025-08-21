document.addEventListener("DOMContentLoaded", function () {
  const searchForm = document.getElementById("searchForm");
  const loadingState = document.getElementById("loadingState");
  const results = document.getElementById("results");
  const errorState = document.getElementById("errorState");
  const errorMessage = document.getElementById("errorMessage");

  // To keep track of chart instances and destroy them before redrawing
  let sourceChartInstance = null;
  let timelineChartInstance = null;

  searchForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const query = document.getElementById("searchQuery").value;

    // Show loading state and hide previous results/errors
    loadingState.classList.remove("hidden");
    results.classList.add("hidden");
    errorState.classList.add("hidden");
    results.innerHTML = ""; // Clear previous results

    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query, max_articles: 10 }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Failed to fetch results");
      }

      // Hide loading, show results
      loadingState.classList.add("hidden");
      results.classList.remove("hidden");

      displayResults(query, data);
    } catch (error) {
      console.error("Error:", error);
      loadingState.classList.add("hidden");
      errorState.classList.remove("hidden");
      errorMessage.textContent = error.message;
    }
  });

  function displayResults(query, data) {
    // Inject the main results HTML structure
    results.innerHTML = `
        <div class="results-header">
            <h2>Results for "${query}"</h2>
            <div class="results-meta">
                <span>${data.articles_processed} articles analyzed</span>
                <span>Confidence: ${Math.round(
                  data.analysis_confidence * 100
                )}%</span>
            </div>
        </div>
        <div class="card">
            <h3><i class="fas fa-file-alt"></i> Summary</h3>
            <p>${data.summary}</p>
        </div>
        <div class="card">
            <h3><i class="fas fa-lightbulb"></i> Key Insights</h3>
            <div class="insights-list">
                ${data.key_insights
                  .map((insight) => `<div>${insight}</div>`)
                  .join("")}
            </div>
        </div>
        <div class="charts-container">
            <div class="chart-card">
                <h3>Source Breakdown</h3>
                <canvas id="sourceBreakdownChart"></canvas>
            </div>
            <div class="chart-card">
                <h3>Publication Timeline</h3>
                <canvas id="publicationTimelineChart"></canvas>
            </div>
        </div>
    `;

    // Render the charts using the visualization data
    renderCharts(data.visualization_data);
  }

  function renderCharts(visData) {
    // Destroy previous charts if they exist to prevent conflicts
    if (sourceChartInstance) {
      sourceChartInstance.destroy();
    }
    if (timelineChartInstance) {
      timelineChartInstance.destroy();
    }

    // 1. Source Breakdown Chart (Bar Graph)
    const sourceCtx = document
      .getElementById("sourceBreakdownChart")
      .getContext("2d");
    const sourceData = visData.source_breakdown;
    sourceChartInstance = new Chart(sourceCtx, {
      type: "bar",
      data: {
        labels: Object.keys(sourceData),
        datasets: [
          {
            label: "% of Articles",
            data: Object.values(sourceData),
            backgroundColor: "rgba(54, 162, 235, 0.6)",
            borderColor: "rgba(54, 162, 235, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        indexAxis: "y", // Horizontal bar chart
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (context) {
                return `${context.dataset.label}: ${context.raw.toFixed(1)}%`;
              },
            },
          },
        },
        scales: {
          x: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Percentage (%)",
            },
          },
        },
      },
    });

    // 2. Publication Timeline (Line Graph)
    const timelineCtx = document
      .getElementById("publicationTimelineChart")
      .getContext("2d");
    const timelineData = visData.timeline;

    // Convert timeline data to a format Chart.js understands
    const timelinePoints = timelineData.map((event) => ({
      x: new Date(event.timestamp),
      y: 1, // We can just plot occurrences. For a better view, we'd need to aggregate.
    }));

    // Aggregate counts per day for a cleaner graph
    const countsPerDay = timelineData.reduce((acc, event) => {
      const day = event.timestamp.split("T")[0]; // Get YYYY-MM-DD
      acc[day] = (acc[day] || 0) + 1;
      return acc;
    }, {});

    const sortedDays = Object.keys(countsPerDay).sort();

    timelineChartInstance = new Chart(timelineCtx, {
      type: "line",
      data: {
        labels: sortedDays,
        datasets: [
          {
            label: "Number of Articles Published",
            data: sortedDays.map((day) => countsPerDay[day]),
            fill: false,
            borderColor: "rgb(75, 192, 192)",
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        scales: {
          x: {
            type: "time",
            time: {
              unit: "day",
              tooltipFormat: "MMM dd, yyyy",
            },
            title: {
              display: true,
              text: "Date",
            },
          },
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Number of Articles",
            },
            ticks: {
              stepSize: 1, // Ensure y-axis has integer steps
            },
          },
        },
        plugins: {
          legend: { display: false },
        },
      },
    });
  }
});
