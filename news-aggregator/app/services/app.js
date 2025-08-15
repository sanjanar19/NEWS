document.addEventListener("DOMContentLoaded", function () {
  const searchForm = document.getElementById("searchForm");
  const loadingState = document.getElementById("loadingState");
  const results = document.getElementById("results");
  const errorState = document.getElementById("errorState");
  const errorMessage = document.getElementById("errorMessage");
  const healthModal = document.getElementById("healthModal");
  const healthCheckBtn = document.getElementById("healthCheckBtn");
  const closeModal = healthModal.querySelector(".close");

  searchForm.addEventListener("submit", async function (event) {
    event.preventDefault();
    const query = document.getElementById("searchQuery").value;

    // Show loading state
    loadingState.classList.remove("hidden");
    results.classList.add("hidden");
    errorState.classList.add("hidden");

    try {
      const response = await fetch("http://127.0.0.1:8000/api/v1/search", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          max_articles: 5,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Failed to fetch results");
      }

      // Hide loading, show results
      loadingState.classList.add("hidden");
      results.classList.remove("hidden");

      // Display results
      results.innerHTML = `
                <div class="results-header">
                    <h2>Results for "${query}"</h2>
                    <div class="results-meta">
                        <span>${
                          data.articles_processed
                        } articles analyzed</span>
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
            `;
    } catch (error) {
      console.error("Error:", error);
      loadingState.classList.add("hidden");
      errorState.classList.remove("hidden");
      errorMessage.textContent = error.message;
    }
  });

  healthCheckBtn.addEventListener("click", async function () {
    try {
      const response = await fetch("/health");
      const data = await response.json();
      displayHealthCheck(data);
    } catch (error) {
      showError(error.message);
    }
  });

  closeModal.addEventListener("click", function () {
    healthModal.classList.add("hidden");
  });

  function displayResults(data) {
    document.getElementById("summaryText").innerText = data.summary;
    document.getElementById(
      "processingTime"
    ).innerText = `Processing Time: ${data.processing_time_ms} ms`;
    document.getElementById(
      "articlesProcessed"
    ).innerText = `Articles Processed: ${data.articles_processed}`;

    const insightsList = document.getElementById("insightsList");
    insightsList.innerHTML = "";
    data.key_insights.forEach((insight) => {
      const insightItem = document.createElement("div");
      insightItem.innerText = `${insight.point} (Confidence: ${insight.confidence})`;
      insightsList.appendChild(insightItem);
    });

    // Update charts and sources here...

    resultsSection.classList.remove("hidden");
  }

  function showError(message) {
    document.getElementById("errorMessage").innerText = message;
    errorState.classList.remove("hidden");
  }

  function displayHealthCheck(data) {
    const healthContent = document.getElementById("healthContent");
    healthContent.innerHTML = `<p>Status: ${data.status}</p><p>Version: ${data.version}</p>`;
    healthModal.classList.remove("hidden");
  }
});
