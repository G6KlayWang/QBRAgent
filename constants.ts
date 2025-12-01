
import { RootData } from './types';

export const SIMULATED_DATA: RootData = {
  "properties": {
    "hilton_regional_portfolio": {
      "name": "Hilton Regional Portfolio",
      "portfolio_narrative": {
        "headline": "Efficiency at Scale",
        "opening_statement_primary": "The Regional Portfolio delivered a combined $94,000 in financial impact this quarter, driven by a 15% improvement in water efficiency across all properties. We have achieved a weighted ROI of 1.1x, signaling a transition from investment recovery to pure value generation.",
        "top_5_takeaways": [
          "Total portfolio financial impact grew by 2% quarter-over-quarter.",
          "Water optimization remains the primary driver, contributing 48% of total savings.",
          "Alert responsiveness improved to 86%, directly correlating with reduced downtime costs.",
          "Hilton Riverside has fully achieved payback, setting the benchmark for the region.",
          "Phase 2 expansion opportunities identified for both properties to capture outdoor water savings."
        ],
        "critical_decision_narrative": "Approving the Phase 2 expansion across the portfolio by Q1 2026 will unlock an estimated $165k-$210k in additional annual savings. The combined portfolio ROI is projected to exceed 3.5x within 18 months of implementation.",
        "next_steps": [
          { "description": "Finalize Phase 2 budget approval for Riverside and Seaview.", "date": "Jan 2026" },
          { "description": "Standardize 'Magic Moment' alert protocols across engineering teams.", "date": "Feb 2026" },
          { "description": "Conduct Q4 pre-season preventive maintenance audit.", "date": "Nov 2025" }
        ]
      },
      "hotels": {
        "hilton_riverside": {
          "hotel_name": "Hilton Riverside",
          "current_quarter": "2025-Q3",
          "narrative": {
            "headline": "Riverside: Peak Performance",
            "opening_statement_primary": "Hilton Riverside achieved a milestone 1.17x ROI this quarter, with $53,000 in total cost avoidance. The property has successfully moved into the 'Payback Achieved' status, validating the initial smart infrastructure investment.",
            "top_5_takeaways": [
              "Achieved full project payback in July 2025.",
              "Energy cost avoidance rose 29% due to optimized chiller staging.",
              "Downtime costs reduced by $1,000 QoQ thanks to early leak detection.",
              "Engineering team sustained an 88% alert acknowledgement rate.",
              "Water savings slightly normalized due to seasonal cooling tower variance."
            ],
            "critical_decision_narrative": "With the core system stabilized, expanding to pool and irrigation monitoring (Phase 2) is the logical next step. This $120k investment is low-risk and expected to yield $95k+ annually.",
            "next_steps": [
              { "description": "Approve Phase 2 capital for pool/irrigation scope.", "date": "Jan 31, 2026" },
              { "description": "Review basement connectivity for improved sensor uptime.", "date": "Dec 2025" },
              { "description": "Celebrate 'Payback Achieved' milestone with ops team.", "date": "Oct 2025" }
            ]
          },
          "quarters": {
            "2025-Q3": {
              "label": "Q3 2025",
              "metrics": {
                "total_financial_impact_usd": 53000,
                "water_cost_avoided_usd": 26000,
                "energy_cost_avoided_usd": 18000,
                "downtime_cost_avoided_usd": 9000,
                "total_investment_to_date_usd": 180000,
                "roi_multiple_to_date": 1.17,
                "payback_status": "achieved",
                "payback_achieved_month": "2025-07",
                "alert_ack_within_4h_pct": 88,
                "high_priority_resolution_lt_6h_pct": 82
              }
            },
            "2025-Q2": {
              "label": "Q2 2025",
              "metrics": {
                "total_financial_impact_usd": 52000,
                "water_cost_avoided_usd": 30000,
                "energy_cost_avoided_usd": 14000,
                "downtime_cost_avoided_usd": 8000,
                "total_investment_to_date_usd": 165000,
                "roi_multiple_to_date": 1.05,
                "payback_status": "in_progress",
                "payback_achieved_month": null,
                "alert_ack_within_4h_pct": 85,
                "high_priority_resolution_lt_6h_pct": 74
              }
            }
          },
          "phase2_option": {
            "decision_deadline": "2026-01-31",
            "incremental_capex_usd": 120000,
            "expected_additional_annual_savings_usd_range": { "low": 95000, "high": 120000 },
            "expected_portfolio_level_roi_multiple_after_phase2": 3.8
          }
        },
        "hilton_seaview": {
          "hotel_name": "Hilton Seaview",
          "current_quarter": "2025-Q3",
          "narrative": {
            "headline": "Seaview: Momentum Building",
            "opening_statement_primary": "Hilton Seaview continues its upward trajectory with $41,000 in savings and a near-payback ROI of 0.98x. Operational engagement has improved significantly, with alert resolution times dropping by 15%.",
            "top_5_takeaways": [
              "ROI reached 0.98x; payback expected in Q4 2025.",
              "Energy savings increased by 18% QoQ due to boiler optimization.",
              "Alert acknowledgment rate jumped from 70% to 81%.",
              "Identified $19k in water savings despite high occupancy.",
              "Phase 2 offers a quicker payback period than Riverside."
            ],
            "critical_decision_narrative": "Seaview's Phase 2 focuses on kitchen hot water loops. A smaller $90k capex injection is projected to return $70k-$90k annually, making it a high-velocity capital deployment.",
            "next_steps": [
              { "description": "Train night staff on new leak protocol.", "date": "Nov 15, 2025" },
              { "description": "Finalize Phase 2 design with engineering.", "date": "Feb 2026" },
              { "description": "Audit guest room low-flow fixtures.", "date": "Dec 2025" }
            ]
          },
          "quarters": {
            "2025-Q3": {
              "label": "Q3 2025",
              "metrics": {
                "total_financial_impact_usd": 41000,
                "water_cost_avoided_usd": 19000,
                "energy_cost_avoided_usd": 15000,
                "downtime_cost_avoided_usd": 7000,
                "total_investment_to_date_usd": 150000,
                "roi_multiple_to_date": 0.98,
                "payback_status": "in_progress",
                "payback_achieved_month": null,
                "alert_ack_within_4h_pct": 81,
                "high_priority_resolution_lt_6h_pct": 76
              }
            },
            "2025-Q2": {
              "label": "Q2 2025",
              "metrics": {
                "total_financial_impact_usd": 40500,
                "water_cost_avoided_usd": 20000,
                "energy_cost_avoided_usd": 12700,
                "downtime_cost_avoided_usd": 6400,
                "total_investment_to_date_usd": 138000,
                "roi_multiple_to_date": 0.93,
                "payback_status": "in_progress",
                "payback_achieved_month": null,
                "alert_ack_within_4h_pct": 70,
                "high_priority_resolution_lt_6h_pct": 65
              }
            }
          },
          "phase2_option": {
            "decision_deadline": "2026-02-15",
            "incremental_capex_usd": 90000,
            "expected_additional_annual_savings_usd_range": { "low": 70000, "high": 90000 },
            "expected_portfolio_level_roi_multiple_after_phase2": 3.4
          }
        }
      }
    }
  }
};
