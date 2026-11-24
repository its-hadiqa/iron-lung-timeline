
// image displaying popup
const viewer = document.getElementById("viewer");
const viewerTitle = document.getElementById("viewer-title");
const viewerImg = document.getElementById("viewer-img");

// listener for click anywhere
// if it's a link, display popup
document.addEventListener("click", (e) => {
  const link = e.target.closest("a.capture");
  if (!link) return;
  e.preventDefault();
  viewerTitle.textContent = link.dataset.title;
  viewerImg.src = link.href;
  viewerImg.alt = link.dataset.title;
  viewer.showModal();
});

// a click outside the popup will also close it
viewer.addEventListener("click", (e) => { if (e.target === viewer) viewer.close(); });