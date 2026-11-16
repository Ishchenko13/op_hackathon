const flightForm = document.querySelector("[data-airports-url]");

if (flightForm) {
  for (const field of flightForm.querySelectorAll("[data-airport-field]")) {
    setupAirportField(field, flightForm.dataset.airportsUrl);
  }

  const departure = flightForm.elements.departure_date;
  const returnDate = flightForm.elements.return_date;
  const today = returnDate.min;
  function updateReturnMinimum() {
    returnDate.min = departure.value > today ? departure.value : today;
  }
  departure.addEventListener("change", updateReturnMinimum);
  updateReturnMinimum();
}

function setupAirportField(field, endpoint) {
  const input = field.querySelector("[role='combobox']");
  const code = field.querySelector("[data-airport-code]");
  const list = field.querySelector("[role='listbox']");
  const status = field.querySelector("[role='status']");
  let results = [];
  let active = -1;
  let timeout;
  let pending;

  function closeSuggestions() {
    clearTimeout(timeout);
    pending?.abort();
    results = [];
    active = -1;
    list.replaceChildren();
    list.hidden = true;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
    status.textContent = "";
  }

  function setValidity() {
    input.setCustomValidity(
      input.value && !code.value ? "Choose an airport from the suggestions." : ""
    );
  }

  function selectAirport(result) {
    input.value = result.display_name || `${result.city} — ${result.airport} (${result.iata})`;
    code.value = result.iata;
    closeSuggestions();
    setValidity();
    status.textContent = `Selected ${input.value}.`;
  }

  function showSuggestions(airports) {
    results = airports;
    airports.forEach((airport, index) => {
      const option = document.createElement("li");
      option.id = `${list.id}-${index}`;
      option.setAttribute("role", "option");
      option.setAttribute("aria-selected", "false");
      option.textContent = `${airport.city} · ${airport.airport} (${airport.iata})`;
      option.addEventListener("mousedown", (event) => event.preventDefault());
      option.addEventListener("click", () => selectAirport(airport));
      list.append(option);
    });
    list.hidden = airports.length === 0;
    input.setAttribute("aria-expanded", String(!list.hidden));
    status.textContent = airports.length
      ? `${airports.length} airport suggestions available.`
      : "No matching airports.";
  }

  input.addEventListener("input", () => {
    code.value = "";
    setValidity();
    closeSuggestions();
    const query = input.value.trim();
    if (query.length < 2) return;

    timeout = setTimeout(async () => {
      const controller = new AbortController();
      pending = controller;
      const url = new URL(endpoint, window.location.href);
      url.searchParams.set("q", query);
      status.textContent = "Searching airports…";
      try {
        const response = await fetch(url, { signal: controller.signal });
        const data = await response.json();
        if (controller.signal.aborted) return;
        if (!response.ok || data.error) {
          status.textContent = data.error || "Airport suggestions are temporarily unavailable.";
          return;
        }
        showSuggestions(data.airports);
      } catch (error) {
        if (!controller.signal.aborted) {
          status.textContent = "Airport suggestions are temporarily unavailable.";
        }
      }
    }, 180);
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      closeSuggestions();
      return;
    }
    if (!results.length) return;
    if (event.key === "Enter" && active >= 0) {
      event.preventDefault();
      selectAirport(results[active]);
      return;
    }
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;

    event.preventDefault();
    if (event.key === "ArrowDown") {
      active = (active + 1) % results.length;
    } else {
      active = active <= 0 ? results.length - 1 : active - 1;
    }
    for (const [index, option] of Array.from(list.children).entries()) {
      option.setAttribute("aria-selected", String(index === active));
    }
    const option = list.children[active];
    input.setAttribute("aria-activedescendant", option.id);
    option.scrollIntoView({ block: "nearest" });
  });

  field.addEventListener("focusout", (event) => {
    if (!field.contains(event.relatedTarget)) closeSuggestions();
  });

  setValidity();
}
