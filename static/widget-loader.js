(function () {
  const widgets = document.querySelectorAll("#anksura-widget");

  widgets.forEach((widget) => {
    // Read the business identifier
    const siteHash = widget.dataset.siteHash;

    if (!siteHash) {
      console.error("Booking widget: Missing site hash.");
      return;
    }

    // Create the iframe
    const iframe = document.createElement("iframe");

    iframe.src = `http://127.0.0.1:8000/widget/${siteHash}?v=2`;
    iframe.width = "100%";
    iframe.height = "700";
    iframe.style.border = "none";
    iframe.style.borderRadius = "12px";

    // Insert iframe into the container
    widget.appendChild(iframe);
  });
})();
