(() => {
  const script = document.currentScript;
  if (!script) return;

  const widgetUrl = script.dataset.widgetUrl || new URL("apply.html", script.src).href;
  const apiBase = script.dataset.apiBase;
  const embedToken = script.dataset.embedToken;
  const container = script.dataset.container
    ? document.querySelector(script.dataset.container)
    : script.parentElement;

  if (!container || !apiBase || !embedToken) {
    console.error("CTMS widget needs data-api-base and data-embed-token attributes.");
    return;
  }

  const frameUrl = new URL(widgetUrl, document.baseURI);
  frameUrl.searchParams.set("apiBase", apiBase.replace(/\/$/, ""));
  frameUrl.searchParams.set("embedToken", embedToken);

  const frame = document.createElement("iframe");
  frame.src = frameUrl.href;
  frame.title = "Cohort application form";
  frame.loading = "lazy";
  frame.style.width = "100%";
  frame.style.height = script.dataset.height || "540px";
  frame.style.border = "0";
  frame.style.borderRadius = "12px";
  frame.setAttribute("loading", "lazy");
  container.append(frame);
})();
