// Orchestrates selecting property/hotel/quarter, hydrating narrative, and rendering.
// Depends on data.js (demoData), llm.js (hydrateNarrative), and elements.js (render helpers).

function percentChange(current, previous) {
  if (previous === 0 || previous === null || previous === undefined) return null;
  return Math.round(((current - previous) / previous) * 100);
}

function deriveRoiSnapshot(current, previous) {
  if (!current || !previous) return null;
  return {
    total_financial_impact_Q3_usd: current.total_financial_impact_usd,
    total_financial_impact_trend_vs_Q2_pct: percentChange(current.total_financial_impact_usd, previous.total_financial_impact_usd),
    water_cost_avoided_Q3_usd: current.water_cost_avoided_usd,
    water_cost_avoided_trend_vs_Q2_pct: percentChange(current.water_cost_avoided_usd, previous.water_cost_avoided_usd),
    energy_cost_avoided_Q3_usd: current.energy_cost_avoided_usd,
    energy_cost_avoided_trend_vs_Q2_pct: percentChange(current.energy_cost_avoided_usd, previous.energy_cost_avoided_usd),
    downtime_cost_avoided_Q3_usd: current.downtime_cost_avoided_usd,
    downtime_cost_avoided_trend_vs_Q2_pct: percentChange(current.downtime_cost_avoided_usd, previous.downtime_cost_avoided_usd),
    payback_status: current.payback_status,
    payback_achieved_month: current.payback_achieved_month,
    total_investment_to_date_usd: current.total_investment_to_date_usd,
    roi_multiple_to_date: current.roi_multiple_to_date
  };
}

function selectHotelData(data, propertyId, hotelId) {
  return data?.properties?.[propertyId]?.hotels?.[hotelId] || null;
}

function pickPreviousQuarter(hotelData, currentQuarterId) {
  const quarters = Object.keys(hotelData.quarters || {});
  const sorted = quarters.sort().reverse(); // assumes IDs sort lexicographically (e.g., 2025-Q3)
  const currentIndex = sorted.indexOf(currentQuarterId);
  if (currentIndex === -1 || currentIndex === sorted.length - 1) return null;
  return sorted[currentIndex + 1];
}

function renderExecutiveSummary(summaryData) {
  const summary = summaryData && (summaryData["4.1_executive_summary"] || summaryData);
  if (!summary) return;

  const headerEl = document.querySelector(".page-header");
  if (headerEl && (summary.hotel_name || summary.quarter)) {
    headerEl.innerHTML = generateHeader(summary.hotel_name, summary.quarter);
  }

  const openingEl = document.getElementById("opening-statement");
  if (openingEl && summary.opening_statement_primary) {
    openingEl.innerHTML = generateOpeningStatement(summary.opening_statement_primary);
  }

  const declineEl = document.getElementById("decline-ack");
  if (declineEl && summary.opening_statement_decline_acknowledgement) {
    declineEl.innerHTML = generateDeclineAcknowledgement(summary.opening_statement_decline_acknowledgement);
  }

  const takeawaysEl = document.getElementById("top-takeaways");
  if (takeawaysEl && Array.isArray(summary.top_5_takeaways)) {
    takeawaysEl.innerHTML = generateTopTakeaways(summary.top_5_takeaways);
  }

  const roiEl = document.getElementById("roi-snapshot");
  if (roiEl && summary.roi_snapshot) {
    roiEl.innerHTML = generateRoiSnapshot(summary.roi_snapshot);
  }

  const decisionEl = document.getElementById("critical-decision");
  if (decisionEl && summary.critical_decision) {
    decisionEl.innerHTML = generateCriticalDecision(summary.critical_decision);
  }

  const nextStepsEl = document.getElementById("next-steps");
  if (nextStepsEl && Array.isArray(summary.next_steps)) {
    nextStepsEl.innerHTML = generateNextSteps(summary.next_steps);
  }
}

function getInitialSelection(data) {
  const params = new URLSearchParams(window.location.search);
  const firstProperty = Object.keys(data.properties || {})[0];
  const propertyId = params.get("property") || firstProperty;
  const property = data.properties[propertyId] || data.properties[firstProperty];

  const firstHotel = property ? Object.keys(property.hotels || {})[0] : null;
  const hotelId = params.get("hotel") || firstHotel;
  const hotel = property?.hotels?.[hotelId] || property?.hotels?.[firstHotel];

  const quarters = hotel ? Object.keys(hotel.quarters || {}) : [];
  const sortedQuarters = quarters.sort().reverse();
  const defaultQuarter = sortedQuarters[0];
  const quarterId = params.get("quarter") || defaultQuarter;

  return { propertyId, hotelId, quarterId };
}

function populateSelect(selectEl, options, selectedId) {
  selectEl.innerHTML = "";
  options.forEach(({ id, label }) => {
    const opt = document.createElement("option");
    opt.value = id;
    opt.textContent = label;
    if (id === selectedId) opt.selected = true;
    selectEl.appendChild(opt);
  });
}

function buildControls(data, selection, onChange) {
  const controlsEl = document.getElementById("selection-controls");
  if (!controlsEl) return;

  const propertySelect = controlsEl.querySelector("#property-select");
  const hotelSelect = controlsEl.querySelector("#hotel-select");
  const quarterSelect = controlsEl.querySelector("#quarter-select");

  const propertyOptions = Object.entries(data.properties || {}).map(([id, val]) => ({
    id,
    label: val.name || id
  }));

  populateSelect(propertySelect, propertyOptions, selection.propertyId);

  function sortedQuarterIds(hotel) {
    return Object.keys(hotel.quarters || {}).sort().reverse(); // latest first
  }

  function refreshHotelsAndQuarters(selectedPropertyId, selectedHotelId, selectedQuarterId) {
    const selectedProperty = data.properties[selectedPropertyId];
    const hotelOptions = Object.entries(selectedProperty.hotels || {}).map(([id, val]) => ({
      id,
      label: val.hotel_name || id
    }));
    populateSelect(hotelSelect, hotelOptions, selectedHotelId);

    const selectedHotel = selectedProperty.hotels[selectedHotelId] || selectedProperty.hotels[hotelOptions[0].id];
    const quarterOrder = sortedQuarterIds(selectedHotel);
    const quarterOptions = quarterOrder.map((id) => ({ id, label: selectedHotel.quarters[id].label || id }));
    const quarterToSelect = selectedQuarterId || quarterOrder[0];
    populateSelect(quarterSelect, quarterOptions, quarterToSelect);
  }

  refreshHotelsAndQuarters(selection.propertyId, selection.hotelId, selection.quarterId);

  propertySelect.addEventListener("change", () => {
    const newProperty = propertySelect.value;
    const firstHotel = Object.keys(data.properties[newProperty].hotels || {})[0];
    const firstQuarter = sortedQuarterIds(data.properties[newProperty].hotels[firstHotel])[0];
    refreshHotelsAndQuarters(newProperty, firstHotel, firstQuarter);
    onChange({ propertyId: newProperty, hotelId: hotelSelect.value, quarterId: quarterSelect.value });
  });

  hotelSelect.addEventListener("change", () => {
    const newHotel = hotelSelect.value;
    const quarterKeys = sortedQuarterIds(data.properties[propertySelect.value].hotels[newHotel]);
    const sorted = quarterKeys;
    populateSelect(
      quarterSelect,
      sorted.map((id) => ({ id, label: data.properties[propertySelect.value].hotels[newHotel].quarters[id].label || id })),
      sorted[0]
    );
    onChange({ propertyId: propertySelect.value, hotelId: newHotel, quarterId: quarterSelect.value });
  });

  quarterSelect.addEventListener("change", () => {
    onChange({ propertyId: propertySelect.value, hotelId: hotelSelect.value, quarterId: quarterSelect.value });
  });
}

async function loadAndRender(selection) {
  const { propertyId, hotelId, quarterId } = selection;
  const hotelData = selectHotelData(demoData, propertyId, hotelId);
  if (!hotelData) return;

  const previousQuarterId = pickPreviousQuarter(hotelData, quarterId);
  if (!previousQuarterId) return;

  const currentMetrics = hotelData.quarters[quarterId].metrics;
  const previousMetrics = hotelData.quarters[previousQuarterId].metrics;
  const roiSnapshot = deriveRoiSnapshot(currentMetrics, previousMetrics);

  const narrative = await hydrateNarrative(hotelData, roiSnapshot, quarterId, previousQuarterId);

  const summaryData = {
    ...narrative,
    roi_snapshot: roiSnapshot,
    hotel_name: hotelData.hotel_name,
    quarter: hotelData.quarters[quarterId].label
  };

  renderExecutiveSummary(summaryData);
}

document.addEventListener("DOMContentLoaded", async () => {
  const selection = getInitialSelection(demoData);
  buildControls(demoData, selection, (newSelection) => {
    loadAndRender(newSelection);
    const params = new URLSearchParams(window.location.search);
    params.set("property", newSelection.propertyId);
    params.set("hotel", newSelection.hotelId);
    params.set("quarter", newSelection.quarterId);
    const newUrl = `${window.location.pathname}?${params.toString()}`;
    window.history.replaceState({}, "", newUrl);
  });

  await loadAndRender(selection);
});
