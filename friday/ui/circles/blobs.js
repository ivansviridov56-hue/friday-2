// Style "blobs": soft glowing spots, drawn by CSS (see .blob in styles.css).
(function () {
  window.fridayCircles.register("blobs", {
    mount(box) {
      box.innerHTML =
        '<div class="blobs-anchor">' +
        '<div class="blob a"></div><div class="blob b"></div><div class="blob c"></div>' +
        "</div>";
    },
  });
})();