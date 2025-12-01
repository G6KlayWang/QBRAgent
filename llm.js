function percentChange(current, previous) {
  if (previous === 0 || previous === null || previous === undefined) return null;
  return Math.round(((current - previous) / previous) * 100);
}

function buildLLMPrompt(hotelData, roiSnapshot, currentQuarterId, previousQuarterId) {
  const current = hotelData.quarters[currentQuarterId].metrics;
  const prev = hotelData.quarters[previousQuarterId].metrics;
  const currentLabel = hotelData.quarters[currentQuarterId].label;
  const prevLabel = hotelData.quarters[previousQuarterId].label;
  const totalDelta = percentChange(current.total_financial_impact_usd, prev.total_financial_impact_usd);
  const waterDelta = percentChange(current.water_cost_avoided_usd, prev.water_cost_avoided_usd);
  const energyDelta = percentChange(current.energy_cost_avoided_usd, prev.energy_cost_avoided_usd);
  const downtimeDelta = percentChange(current.downtime_cost_avoided_usd, prev.downtime_cost_avoided_usd);
  const declines = [waterDelta, energyDelta, downtimeDelta].some((v) => v !== null && v <= -10);

  return `
You are an analyst writing a concise executive summary for a QBR.
Return JSON with keys:
- opening_statement_primary (2-3 sentences, business tone)
- opening_statement_decline_acknowledgement (must exist if any key metric declined >10% vs prior quarter; explain why)
- top_5_takeaways (array of 5 bullets answering "so what?")
- roi_snapshot (reuse provided numbers; no need to restate)
- critical_decision (one clear ask with deadline; include incremental_capex_usd and expected_additional_annual_savings_usd_range if relevant)
- next_steps (array of { description, target_date? or target_period? })
Tone: business/financial (CFO/owner) with operational clarity; avoid raw telemetry.

Context:
- Hotel: ${hotelData.hotel_name}
- Current quarter: ${currentLabel}
- Prior quarter: ${prevLabel}
- Financial impact: current ${formatCurrency(current.total_financial_impact_usd)}, prior ${formatCurrency(prev.total_financial_impact_usd)}
- Water avoided: current ${formatCurrency(current.water_cost_avoided_usd)}, prior ${formatCurrency(prev.water_cost_avoided_usd)}
- Energy avoided: current ${formatCurrency(current.energy_cost_avoided_usd)}, prior ${formatCurrency(prev.energy_cost_avoided_usd)}
- Downtime avoided: current ${formatCurrency(current.downtime_cost_avoided_usd)}, prior ${formatCurrency(prev.downtime_cost_avoided_usd)}
- ROI multiple to date: current ${current.roi_multiple_to_date}x, prior ${prev.roi_multiple_to_date}x
- Payback status: ${current.payback_status}; Month (if achieved): ${current.payback_achieved_month ?? "n/a"}
- Alert response: current ack <4h ${current.alert_ack_within_4h_pct}%, prior ${prev.alert_ack_within_4h_pct}% ; high priority <6h current ${current.high_priority_resolution_lt_6h_pct}%, prior ${prev.high_priority_resolution_lt_6h_pct}%
- Phase 2 option: capex ${formatCurrency(hotelData.phase2_option.incremental_capex_usd)}, expected annual savings range ${formatRange(hotelData.phase2_option.expected_additional_annual_savings_usd_range, formatCurrency)}, portfolio ROI after phase 2 ${hotelData.phase2_option.expected_portfolio_level_roi_multiple_after_phase2}x
${declines ? "- Note: at least one metric declined >10% QoQ; you MUST acknowledge and explain it." : ""}

HTML template sections on the page (your JSON will populate these):
- .page-header -> header with title, quarter, hotel
- #opening-statement -> opening_statement_primary
- #decline-ack -> opening_statement_decline_acknowledgement
- #top-takeaways -> top_5_takeaways list
- #roi-snapshot -> roi_snapshot numbers (already provided)
- #critical-decision -> critical_decision
- #next-steps -> next_steps

Only return JSON; do not include prose outside the JSON.
`;
}

async function callOpenAIChat(prompt, llmConfig) {
  if (!llmConfig?.enabled) return null;

  const basePayload = {
    model: llmConfig.model || "gpt-4o-mini",
    temperature: llmConfig.temperature ?? 0.4,
    messages: [
      {
        role: "system",
        content: "You write concise QBR narratives. Respond ONLY with JSON matching the requested shape."
      },
      { role: "user", content: prompt }
    ]
  };

  if (llmConfig.proxyEndpoint) {
    console.info("Calling LLM proxy", llmConfig.proxyEndpoint);
    const res = await fetch(llmConfig.proxyEndpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, model: basePayload.model, temperature: basePayload.temperature })
    });
    if (!res.ok) {
      throw new Error(`LLM proxy failed: ${res.status} ${res.statusText}`);
    }
    const json = await res.json();
    return json?.content || null;
  }

  const headers = { "Content-Type": "application/json" };
  if (llmConfig.apiKey) {
    headers.Authorization = `Bearer ${llmConfig.apiKey}`;
  }

  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers,
    body: JSON.stringify(basePayload)
  });
  if (!res.ok) {
    throw new Error(`LLM call failed: ${res.status} ${res.statusText}`);
  }
  const json = await res.json();
  const content = json?.choices?.[0]?.message?.content;
  return content || null;
}

function safeParseJSON(jsonString) {
  try {
    return JSON.parse(jsonString);
  } catch (err) {
    console.warn("Failed to parse LLM JSON, falling back to generated summary.", err);
    return null;
  }
}

function buildFallbackNarrative(hotelData, roiSnapshot, currentQuarterId, previousQuarterId) {
  const current = hotelData.quarters[currentQuarterId].metrics;
  const prev = hotelData.quarters[previousQuarterId].metrics;
  const currentLabel = hotelData.quarters[currentQuarterId].label;
  const prevLabel = hotelData.quarters[previousQuarterId].label;
  const totalDelta = percentChange(current.total_financial_impact_usd, prev.total_financial_impact_usd);
  const waterDelta = percentChange(current.water_cost_avoided_usd, prev.water_cost_avoided_usd);
  const energyDelta = percentChange(current.energy_cost_avoided_usd, prev.energy_cost_avoided_usd);
  const downtimeDelta = percentChange(current.downtime_cost_avoided_usd, prev.downtime_cost_avoided_usd);
  const mustAcknowledge = [waterDelta, energyDelta, downtimeDelta].some((v) => v !== null && v <= -10);

  return {
    opening_statement_primary: `${hotelData.hotel_name} delivered ${formatCurrency(current.total_financial_impact_usd)} in ${currentLabel} financial impact, ${totalDelta ?? 0}% versus ${prevLabel}, with ROI to date at ${current.roi_multiple_to_date}x.`,
    opening_statement_decline_acknowledgement: mustAcknowledge
      ? `Key metric declines acknowledged: water ${waterDelta ?? 0}% vs ${prevLabel}, energy ${energyDelta ?? 0}%, downtime ${downtimeDelta ?? 0}%. Drivers: normalizing operations and fewer anomalies.`
      : `Performance variations within normal range; no >10% declines vs ${prevLabel} in core metrics.`,
    top_5_takeaways: [
      `Total impact ${formatCurrency(current.total_financial_impact_usd)} (${totalDelta ?? 0}% vs ${prevLabel}).`,
      `Water cost avoided ${formatCurrency(current.water_cost_avoided_usd)} (${waterDelta ?? 0}% vs ${prevLabel}).`,
      `Energy cost avoided ${formatCurrency(current.energy_cost_avoided_usd)} (${energyDelta ?? 0}% vs ${prevLabel}).`,
      `Alert responsiveness: ${current.alert_ack_within_4h_pct}% ack <4h (${prev.alert_ack_within_4h_pct}% prior); high-priority resolution <6h ${current.high_priority_resolution_lt_6h_pct}% (${prev.high_priority_resolution_lt_6h_pct}% prior).`,
      `ROI multiple to date ${current.roi_multiple_to_date}x; payback status ${current.payback_status}.`
    ],
    critical_decision: {
      description: `Approve Phase 2 to capture ${formatRange(
        hotelData.phase2_option.expected_additional_annual_savings_usd_range,
        formatCurrency
      )} annual savings and move toward ${hotelData.phase2_option.expected_portfolio_level_roi_multiple_after_phase2}x projected portfolio ROI.`,
      deadline: hotelData.phase2_option.decision_deadline,
      incremental_capex_usd: hotelData.phase2_option.incremental_capex_usd,
      expected_additional_annual_savings_usd_range: hotelData.phase2_option.expected_additional_annual_savings_usd_range,
      expected_portfolio_level_roi_multiple_after_phase2: hotelData.phase2_option.expected_portfolio_level_roi_multiple_after_phase2
    },
    next_steps: [
      {
        description: "Approve Phase 2 to unlock incremental annual savings.",
        target_date: hotelData.phase2_option.decision_deadline
      },
      {
        description: "Maintain alert responsiveness above 85% to protect savings consistency.",
        target_period: `Next quarter after ${currentLabel}`
      },
      {
        description: "Validate baseline after upcoming Phase 2 installations and recalibrate ROI multiple.",
        target_period: `${currentLabel} + 1`
      }
    ]
  };
}

async function hydrateNarrative(hotelData, roiSnapshot, currentQuarterId, previousQuarterId) {
  const prompt = buildLLMPrompt(hotelData, roiSnapshot, currentQuarterId, previousQuarterId);
  try {
    const llmContent = await callOpenAIChat(prompt, hotelData.llm_config);
    const parsed = llmContent ? safeParseJSON(llmContent) : null;
    if (parsed) {
      return parsed;
    }
  } catch (err) {
    console.warn("LLM generation failed, using fallback", err);
  }

  return buildFallbackNarrative(hotelData, roiSnapshot, currentQuarterId, previousQuarterId);
}
