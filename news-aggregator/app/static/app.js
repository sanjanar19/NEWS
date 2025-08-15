document.addEventListener("DOMContentLoaded", function () {
  const searchForm = document.getElementById("searchForm");
  const loading = document.getElementById("loading");
  const results = document.getElementById("results");
  const error = document.getElementById("error");

  searchForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const query = document.getElementById("searchQuery").value;

    // Show loading, hide other sections
    loading.classList.remove("hidden");
    results.innerHTML = "";
    error.classList.add("hidden");

    try {
      const response = await fetch("/api/v1/search", {
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

      // Display results
      results.innerHTML = `
                <h2>Results for "${query}"</h2>
                <div class="summary">
                    <h3>Summary</h3>
                    <p>${data.summary}</p>
                </div>
                <div class="insights">
                    <h3>Key Insights</h3>
                    <ul>
                        ${data.key_insights
                          .map((insight) => `<li>${insight}</li>`)
                          .join("")}
                    </ul>
                </div>
            `;
    } catch (err) {
      error.classList.remove("hidden");
      error.textContent = err.message;
    } finally {
      loading.classList.add("hidden");
    }
  });
});
