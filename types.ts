
export interface MetricData {
  total_financial_impact_usd: number;
  water_cost_avoided_usd: number;
  energy_cost_avoided_usd: number;
  downtime_cost_avoided_usd: number;
  total_investment_to_date_usd: number;
  roi_multiple_to_date: number;
  payback_status: string;
  payback_achieved_month: string | null;
  alert_ack_within_4h_pct: number;
  high_priority_resolution_lt_6h_pct: number;
}

export interface Phase2Option {
  decision_deadline: string;
  incremental_capex_usd: number;
  expected_additional_annual_savings_usd_range: {
    low: number;
    high: number;
  };
  expected_portfolio_level_roi_multiple_after_phase2: number;
}

export interface GeneratedNarrative {
  headline: string;
  opening_statement_primary: string;
  opening_statement_decline_acknowledgement?: string;
  top_5_takeaways: string[];
  critical_decision_narrative: string;
  next_steps: { description: string; date?: string }[];
}

export interface QuarterData {
  label: string;
  metrics: MetricData;
}

export interface HotelData {
  hotel_name: string;
  current_quarter: string;
  quarters: Record<string, QuarterData>;
  phase2_option: Phase2Option;
  narrative: GeneratedNarrative; // Pre-simulated insight
}

export interface PropertyData {
  name: string;
  hotels: Record<string, HotelData>;
  portfolio_narrative: GeneratedNarrative; // Pre-simulated insight for the overview
}

export interface RootData {
  properties: Record<string, PropertyData>;
}
