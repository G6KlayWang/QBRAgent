// Demo data separated by property -> hotel -> quarters. Only quantitative facts live here.
// Extend or replace this structure with real data sources or fetch logic.
const demoData = {
  properties: {
    hilton_regional_portfolio: {
      name: "Hilton Regional Portfolio",
      hotels: {
        hilton_riverside: {
          hotel_name: "Hilton Riverside",
          quarters: {
            "2025-Q3": {
              label: "Q3 2025",
              metrics: {
                total_financial_impact_usd: 53000,
                water_cost_avoided_usd: 26000,
                energy_cost_avoided_usd: 18000,
                downtime_cost_avoided_usd: 9000,
                total_investment_to_date_usd: 180000,
                roi_multiple_to_date: 1.17,
                payback_status: "achieved",
                payback_achieved_month: "2025-07",
                alert_ack_within_4h_pct: 88,
                high_priority_resolution_lt_6h_pct: 82
              }
            },
            "2025-Q2": {
              label: "Q2 2025",
              metrics: {
                total_financial_impact_usd: 52000,
                water_cost_avoided_usd: 30000,
                energy_cost_avoided_usd: 14000,
                downtime_cost_avoided_usd: 8000,
                total_investment_to_date_usd: 165000,
                roi_multiple_to_date: 1.05,
                payback_status: "in_progress",
                payback_achieved_month: null,
                alert_ack_within_4h_pct: 85,
                high_priority_resolution_lt_6h_pct: 74
              }
            }
          },
          phase2_option: {
            decision_deadline: "2026-01-31",
            incremental_capex_usd: 120000,
            expected_additional_annual_savings_usd_range: { low: 95000, high: 120000 },
            expected_portfolio_level_roi_multiple_after_phase2: 3.8
          },
          llm_config: {
            enabled: false,
            model: "gpt-4o-mini",
            temperature: 0.4,
            proxyEndpoint: "/api/qbr-narrative"
          }
        },
        hilton_seaview: {
          hotel_name: "Hilton Seaview",
          quarters: {
            "2025-Q3": {
              label: "Q3 2025",
              metrics: {
                total_financial_impact_usd: 41000,
                water_cost_avoided_usd: 19000,
                energy_cost_avoided_usd: 15000,
                downtime_cost_avoided_usd: 7000,
                total_investment_to_date_usd: 150000,
                roi_multiple_to_date: 0.98,
                payback_status: "in_progress",
                payback_achieved_month: null,
                alert_ack_within_4h_pct: 81,
                high_priority_resolution_lt_6h_pct: 76
              }
            },
            "2025-Q2": {
              label: "Q2 2025",
              metrics: {
                total_financial_impact_usd: 40500,
                water_cost_avoided_usd: 20000,
                energy_cost_avoided_usd: 12700,
                downtime_cost_avoided_usd: 6400,
                total_investment_to_date_usd: 138000,
                roi_multiple_to_date: 0.93,
                payback_status: "in_progress",
                payback_achieved_month: null,
                alert_ack_within_4h_pct: 70,
                high_priority_resolution_lt_6h_pct: 65
              }
            }
          },
          phase2_option: {
            decision_deadline: "2026-02-15",
            incremental_capex_usd: 90000,
            expected_additional_annual_savings_usd_range: { low: 70000, high: 90000 },
            expected_portfolio_level_roi_multiple_after_phase2: 3.4
          },
          llm_config: {
            enabled: false,
            model: "gpt-4o-mini",
            temperature: 0.4,
            proxyEndpoint: "/api/qbr-narrative"
          }
        },
        hilton_midtown: {
          hotel_name: "Hilton Midtown",
          quarters: {
            "2025-Q3": {
              label: "Q3 2025",
              metrics: {
                total_financial_impact_usd: 48500,
                water_cost_avoided_usd: 22000,
                energy_cost_avoided_usd: 17000,
                downtime_cost_avoided_usd: 9500,
                total_investment_to_date_usd: 210000,
                roi_multiple_to_date: 1.22,
                payback_status: "achieved",
                payback_achieved_month: "2025-06",
                alert_ack_within_4h_pct: 90,
                high_priority_resolution_lt_6h_pct: 84
              }
            },
            "2025-Q2": {
              label: "Q2 2025",
              metrics: {
                total_financial_impact_usd: 47000,
                water_cost_avoided_usd: 23500,
                energy_cost_avoided_usd: 15000,
                downtime_cost_avoided_usd: 8500,
                total_investment_to_date_usd: 195000,
                roi_multiple_to_date: 1.12,
                payback_status: "in_progress",
                payback_achieved_month: null,
                alert_ack_within_4h_pct: 86,
                high_priority_resolution_lt_6h_pct: 78
              }
            }
          },
          phase2_option: {
            decision_deadline: "2026-03-15",
            incremental_capex_usd: 110000,
            expected_additional_annual_savings_usd_range: { low: 80000, high: 100000 },
            expected_portfolio_level_roi_multiple_after_phase2: 3.6
          },
          llm_config: {
            enabled: false,
            model: "gpt-4o-mini",
            temperature: 0.4,
            proxyEndpoint: "/api/qbr-narrative"
          }
        },
        hilton_airport: {
          hotel_name: "Hilton Airport",
          quarters: {
            "2025-Q3": {
              label: "Q3 2025",
              metrics: {
                total_financial_impact_usd: 36000,
                water_cost_avoided_usd: 14000,
                energy_cost_avoided_usd: 13000,
                downtime_cost_avoided_usd: 9000,
                total_investment_to_date_usd: 130000,
                roi_multiple_to_date: 0.9,
                payback_status: "in_progress",
                payback_achieved_month: null,
                alert_ack_within_4h_pct: 75,
                high_priority_resolution_lt_6h_pct: 70
              }
            },
            "2025-Q2": {
              label: "Q2 2025",
              metrics: {
                total_financial_impact_usd: 34500,
                water_cost_avoided_usd: 15000,
                energy_cost_avoided_usd: 11500,
                downtime_cost_avoided_usd: 8000,
                total_investment_to_date_usd: 118000,
                roi_multiple_to_date: 0.84,
                payback_status: "in_progress",
                payback_achieved_month: null,
                alert_ack_within_4h_pct: 70,
                high_priority_resolution_lt_6h_pct: 64
              }
            }
          },
          phase2_option: {
            decision_deadline: "2026-02-28",
            incremental_capex_usd: 80000,
            expected_additional_annual_savings_usd_range: { low: 55000, high: 75000 },
            expected_portfolio_level_roi_multiple_after_phase2: 3.1
          },
          llm_config: {
            enabled: false,
            model: "gpt-4o-mini",
            temperature: 0.35,
            proxyEndpoint: "/api/qbr-narrative"
          }
        },
        hilton_suburban: {
          hotel_name: "Hilton Suburban",
          quarters: {
            "2025-Q3": {
              label: "Q3 2025",
              metrics: {
                total_financial_impact_usd: 29500,
                water_cost_avoided_usd: 12000,
                energy_cost_avoided_usd: 10000,
                downtime_cost_avoided_usd: 7500,
                total_investment_to_date_usd: 100000,
                roi_multiple_to_date: 0.87,
                payback_status: "in_progress",
                payback_achieved_month: null,
                alert_ack_within_4h_pct: 72,
                high_priority_resolution_lt_6h_pct: 68
              }
            },
            "2025-Q2": {
              label: "Q2 2025",
              metrics: {
                total_financial_impact_usd: 28000,
                water_cost_avoided_usd: 11000,
                energy_cost_avoided_usd: 9500,
                downtime_cost_avoided_usd: 7500,
                total_investment_to_date_usd: 90000,
                roi_multiple_to_date: 0.79,
                payback_status: "in_progress",
                payback_achieved_month: null,
                alert_ack_within_4h_pct: 68,
                high_priority_resolution_lt_6h_pct: 60
              }
            }
          },
          phase2_option: {
            decision_deadline: "2026-04-10",
            incremental_capex_usd: 65000,
            expected_additional_annual_savings_usd_range: { low: 42000, high: 52000 },
            expected_portfolio_level_roi_multiple_after_phase2: 2.9
          },
          llm_config: {
            enabled: false,
            model: "gpt-4o-mini",
            temperature: 0.35,
            proxyEndpoint: "/api/qbr-narrative"
          }
        }
      }
    }
  }
};
