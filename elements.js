function formatCurrency(value) {
  if (value === undefined || value === null || isNaN(value)) return "—";
  return `$${Number(value).toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

function formatPercent(value) {
  if (value === undefined || value === null || isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value}%`;
}

function formatDate(value) {
  if (!value) return "—";
  return value;
}

function formatRange(rangeObj, formatter) {
  if (!rangeObj || rangeObj.low === undefined || rangeObj.high === undefined) {
    return "—";
  }
  return `${formatter(rangeObj.low)} to ${formatter(rangeObj.high)}`;
}

function generateHeader(hotelName, quarter) {
  return `
    <div>
      <h1>Executive Summary 4.1</h1>
      <p class="pill">${quarter || "Quarter"}</p>
      <p class="section-subtitle">${hotelName || "Property"}</p>
    </div>
  `;
}

function generateOpeningStatement(primaryText) {
  return `
    <div class="card">
      <h2 class="section-title">Opening Statement</h2>
      <p class="body-text">${primaryText || ""}</p>
    </div>
  `;
}

function generateDeclineAcknowledgement(text) {
  return `
    <div class="card">
      <h2 class="section-title">Acknowledgement of Decline</h2>
      <p class="body-text">${text || ""}</p>
    </div>
  `;
}

function generateTopTakeaways(listOfStrings) {
  const items = Array.isArray(listOfStrings)
    ? listOfStrings.map((item) => `<li>${item}</li>`).join("")
    : "";
  return `
    <div class="card">
      <h2 class="section-title">Top Takeaways</h2>
      <ul class="list">${items}</ul>
    </div>
  `;
}

function generateRoiSnapshot(roiObject) {
  if (!roiObject) {
    return "";
  }

  const paybackBadge =
    roiObject.payback_status === "achieved"
      ? `<span class="badge-success">Payback achieved</span> <span class="muted">(${formatDate(roiObject.payback_achieved_month)})</span>`
      : `<span class="badge-alert">Payback in progress</span>`;

  return `
    <div class="card">
      <h2 class="section-title">ROI Snapshot</h2>
      <div class="metric-grid">
        <div class="metric">
          <p class="label">Total financial impact Q3</p>
          <p class="value">${formatCurrency(roiObject.total_financial_impact_Q3_usd)}</p>
          <p class="delta">vs Q2: ${formatPercent(roiObject.total_financial_impact_trend_vs_Q2_pct)}</p>
        </div>
        <div class="metric">
          <p class="label">Water cost avoided Q3</p>
          <p class="value">${formatCurrency(roiObject.water_cost_avoided_Q3_usd)}</p>
          <p class="delta">vs Q2: ${formatPercent(roiObject.water_cost_avoided_trend_vs_Q2_pct)}</p>
        </div>
        <div class="metric">
          <p class="label">Energy cost avoided Q3</p>
          <p class="value">${formatCurrency(roiObject.energy_cost_avoided_Q3_usd)}</p>
          <p class="delta">vs Q2: ${formatPercent(roiObject.energy_cost_avoided_trend_vs_Q2_pct)}</p>
        </div>
        <div class="metric">
          <p class="label">Downtime cost avoided Q3</p>
          <p class="value">${formatCurrency(roiObject.downtime_cost_avoided_Q3_usd)}</p>
          <p class="delta">vs Q2: ${formatPercent(roiObject.downtime_cost_avoided_trend_vs_Q2_pct)}</p>
        </div>
        <div class="metric">
          <p class="label">Total investment to date</p>
          <p class="value">${formatCurrency(roiObject.total_investment_to_date_usd)}</p>
          <p class="delta">ROI multiple to date: ${roiObject.roi_multiple_to_date ?? "—"}x</p>
        </div>
        <div class="metric">
          <p class="label">Payback</p>
          <p class="value">${paybackBadge}</p>
          <p class="delta">Month: ${formatDate(roiObject.payback_achieved_month)}</p>
        </div>
      </div>
    </div>
  `;
}

function generateCriticalDecision(decisionObject) {
  if (!decisionObject) {
    return "";
  }

  const savingsRange = decisionObject.expected_additional_annual_savings_usd_range
    ? formatRange(decisionObject.expected_additional_annual_savings_usd_range, formatCurrency)
    : "—";

  return `
    <div class="card">
      <h2 class="section-title">Critical Decision</h2>
      <p class="body-text emphasis">${decisionObject.description || ""}</p>
      <div class="metric-grid" style="margin-top: 14px;">
        <div class="metric">
          <p class="label">Decision deadline</p>
          <p class="value">${formatDate(decisionObject.deadline)}</p>
        </div>
        <div class="metric">
          <p class="label">Incremental CAPEX</p>
          <p class="value">${formatCurrency(decisionObject.incremental_capex_usd)}</p>
        </div>
        <div class="metric">
          <p class="label">Expected annual savings</p>
          <p class="value">${savingsRange}</p>
        </div>
        <div class="metric">
          <p class="label">Portfolio-level ROI after Phase 2</p>
          <p class="value">${decisionObject.expected_portfolio_level_roi_multiple_after_phase2 ?? "—"}x</p>
        </div>
      </div>
    </div>
  `;
}

function generateNextSteps(stepsArray) {
  const steps = Array.isArray(stepsArray)
    ? stepsArray
        .map((step) => {
          const date = step.target_date ? `<span class="date">${formatDate(step.target_date)}</span>` : "";
          const period = step.target_period ? `<span class="period">${step.target_period}</span>` : "";
          const timing = date || period;
          return `
            <div class="next-step">
              ${timing || '<span class="date muted">Upcoming</span>'}
              <p class="description">${step.description || ""}</p>
            </div>
          `;
        })
        .join("")
    : "";

  return `
    <div class="card">
      <h2 class="section-title">Next Steps</h2>
      <div class="stack">
        ${steps}
      </div>
    </div>
  `;
}
