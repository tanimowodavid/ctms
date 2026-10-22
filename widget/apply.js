(() => {
  const parameters = new URLSearchParams(window.location.search);
  const apiBase = (parameters.get("apiBase") || "").replace(/\/$/, "");
  const embedToken = parameters.get("embedToken") || "";
  const form = document.querySelector("#application-form");
  const cohortName = document.querySelector("#cohort-name");
  const trackSelect = document.querySelector("#track");
  const submitButton = document.querySelector("#submit-button");
  const message = document.querySelector("#message");

  function showMessage(text, kind = "error") {
    message.textContent = text;
    message.dataset.kind = kind;
  }

  async function loadOptions() {
    if (!apiBase || !embedToken) {
      cohortName.textContent = "Application form unavailable";
      showMessage("The widget is missing its API address or cohort token.");
      return;
    }

    try {
      const response = await fetch(
        `${apiBase}/cohorts/${encodeURIComponent(embedToken)}/application-tracks`
      );
      if (response.status === 404) throw new Error("This application link is not valid.");
      if (!response.ok) throw new Error("Could not load the application form.");
      const options = await response.json();
      cohortName.textContent = options.cohortName;

      if (!options.acceptingApplications) {
        showMessage("Applications for this cohort are closed.");
        return;
      }
      if (!options.tracks.length) {
        showMessage("There are no tracks available for this cohort.");
        return;
      }

      for (const track of options.tracks) {
        const option = document.createElement("option");
        option.value = track.id;
        option.textContent = track.name;
        trackSelect.append(option);
      }
      form.hidden = false;
    } catch (error) {
      cohortName.textContent = "Application form unavailable";
      showMessage(error instanceof TypeError
        ? "Could not connect to the application service. Please try again later."
        : error.message);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    submitButton.disabled = true;
    submitButton.textContent = "Submitting…";
    showMessage("Submitting your application…", "info");

    const payload = {
      fullName: document.querySelector("#full-name").value.trim(),
      email: document.querySelector("#email").value.trim(),
      trackId: trackSelect.value,
    };

    try {
      const response = await fetch(
        `${apiBase}/cohorts/${encodeURIComponent(embedToken)}/apply`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
      const result = await response.json().catch(() => ({}));
      if (response.status === 409) {
        const detail = (result.detail || "").toLowerCase();
        if (detail.includes("closed")) {
          showMessage("Applications for this cohort are closed.");
        } else {
          showMessage("An application with this email has already been submitted.");
        }
        return;
      }
      if (response.status === 400 || response.status === 422) {
        showMessage(result.detail || "Check your details and try again.");
        return;
      }
      if (!response.ok) throw new Error("Could not submit your application. Please try again.");

      form.reset();
      showMessage("Your application was submitted successfully.", "success");
      form.hidden = true;
    } catch (error) {
      showMessage(error instanceof TypeError
        ? "Could not connect to the application service. Please try again."
        : error.message);
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Submit application";
    }
  });

  loadOptions();
})();
