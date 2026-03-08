const token = localStorage.getItem("token");

async function loadRatings() {
  try {
    const url = token
      ? `${API_URL}/ratings/folder/${folderId}?token=${token}`
      : `${API_URL}/ratings/folder/${folderId}`;
    const res = await fetch(url);
    if (!res.ok) return;

    const data = await res.json();
    overallRating = { average: data.average || 0, count: data.count || 0 };
    userRating = data.userRating || 0;

    updateRatingDisplay();
  } catch (e) {
    console.error("Error loading ratings:", e);
  }
}

// Click to rate
document.getElementById("userStars").addEventListener("click", async (e) => {
  if (e.target.classList.contains("star")) {
    if (!token) {
      alert("Потрібно увійти в систему, щоб поставити оцінку");
      return;
    }
    const rating = parseInt(e.target.dataset.rating);
    try {
      const res = await fetch(`${API_URL}/ratings?token=${token}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_id: folderId, rating }),
      });
      if (!res.ok) throw new Error("Failed to submit rating");

      const data = await res.json();
      overallRating = { average: data.average, count: data.count };
      userRating = rating;
      updateRatingDisplay();
    } catch (e) {
      console.error("Error submitting rating:", e);
      alert("Помилка відправки оцінки");
    }
  }
});
