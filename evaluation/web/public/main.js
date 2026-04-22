const form = document.querySelector("#rating-form");
const output = document.querySelector("#saved-rating");

form?.addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(form);
  const rating = data.get("rating");
  window.localStorage.setItem("luvoire.phase58.rating", String(rating));
  if (output) {
    output.textContent = `Saved rating: ${rating}`;
  }
});

const prior = window.localStorage.getItem("luvoire.phase58.rating");
if (prior && output) {
  output.textContent = `Saved rating: ${prior}`;
}
