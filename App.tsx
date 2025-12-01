
import React from 'react';
import { SIMULATED_DATA } from './constants';
import { Layout } from './components/Layout';
import { MetricCard } from './components/MetricCard';
import { GeneratedNarrative, MetricData, Phase2Option, PropertyData, RootData } from './types';
import generatedReport from './services/report_output.json';

// Helper to sum metrics for portfolio view
const aggregateMetrics = (property: PropertyData, quarter: string): MetricData => {
  const totals: any = {
    total_financial_impact_usd: 0,
    water_cost_avoided_usd: 0,
    energy_cost_avoided_usd: 0,
    downtime_cost_avoided_usd: 0,
    total_investment_to_date_usd: 0,
    roi_multiple_to_date: 0, 
    alert_ack_within_4h_pct: 0, 
    high_priority_resolution_lt_6h_pct: 0, 
    payback_status: "in_progress",
    payback_achieved_month: null
  };

  const hotels = Object.values(property.hotels);
  let count = 0;
  let roiSum = 0;

  hotels.forEach(h => {
    const qData = h.quarters[quarter];
    if (qData) {
      count++;
      const m = qData.metrics;
      totals.total_financial_impact_usd += m.total_financial_impact_usd;
      totals.water_cost_avoided_usd += m.water_cost_avoided_usd;
      totals.energy_cost_avoided_usd += m.energy_cost_avoided_usd;
      totals.downtime_cost_avoided_usd += m.downtime_cost_avoided_usd;
      totals.total_investment_to_date_usd += m.total_investment_to_date_usd;
      roiSum += m.roi_multiple_to_date;
      totals.alert_ack_within_4h_pct += m.alert_ack_within_4h_pct;
      totals.high_priority_resolution_lt_6h_pct += m.high_priority_resolution_lt_6h_pct;
    }
  });

  if (count > 0) {
    totals.roi_multiple_to_date = Number((roiSum / count).toFixed(2));
    totals.alert_ack_within_4h_pct = Math.round(totals.alert_ack_within_4h_pct / count);
    totals.high_priority_resolution_lt_6h_pct = Math.round(totals.high_priority_resolution_lt_6h_pct / count);
    totals.payback_status = totals.roi_multiple_to_date >= 1 ? "achieved" : "in_progress";
  }

  return totals as MetricData;
};

// Component for a Single Page (Overview or Building)
const ReportPage: React.FC<{
  title: string;
  subtitle: string;
  metrics: MetricData;
  prevMetrics?: MetricData;
  narrative: GeneratedNarrative;
  phase2?: Phase2Option;
  isOverview?: boolean;
}> = ({ title, subtitle, metrics, prevMetrics, narrative, phase2, isOverview }) => {
  return (
    <div className="report-page w-full min-h-[1100px] p-12 lg:p-16 flex flex-col bg-white relative overflow-hidden break-after-page print:break-after-page">
       {/* Page Header */}
       <div className="mb-12 border-b border-gray-100 pb-8 flex justify-between items-end">
          <div>
            <span className="text-blue-600 font-bold tracking-wider uppercase text-xs mb-2 block">{subtitle}</span>
            <h1 className="text-4xl font-bold tracking-tight text-[#1D1D1F]">{title}</h1>
          </div>
          <div className="text-right hidden print:block">
             <p className="text-sm text-gray-400">Q3 2025 Report</p>
          </div>
       </div>

       {/* Narrative Headline */}
       <div className="mb-10">
          <h2 className="text-3xl font-semibold text-[#1D1D1F] mb-4 tracking-tight leading-tight">{narrative.headline}</h2>
          <p className="text-lg text-gray-600 leading-relaxed font-normal max-w-4xl">
            {narrative.opening_statement_primary}
          </p>
       </div>

       {/* Metrics Grid */}
       <div className="grid grid-cols-3 gap-6 mb-12">
          <MetricCard 
            label="Total Impact" 
            value={metrics.total_financial_impact_usd} 
            prevValue={prevMetrics?.total_financial_impact_usd}
            isCurrency
            highlight
          />
          <MetricCard 
            label="Total Investment" 
            value={metrics.total_investment_to_date_usd} 
            prevValue={prevMetrics?.total_investment_to_date_usd}
            isCurrency
          />
          <MetricCard 
            label="ROI Multiple" 
            value={metrics.roi_multiple_to_date} 
            prevValue={prevMetrics?.roi_multiple_to_date}
            suffix="x"
          />
          <MetricCard 
            label="Water Savings" 
            value={metrics.water_cost_avoided_usd} 
            prevValue={prevMetrics?.water_cost_avoided_usd}
            isCurrency
          />
          <MetricCard 
            label="Energy Savings" 
            value={metrics.energy_cost_avoided_usd} 
            prevValue={prevMetrics?.energy_cost_avoided_usd}
            isCurrency
          />
          <MetricCard 
            label="Downtime Savings" 
            value={metrics.downtime_cost_avoided_usd} 
            prevValue={prevMetrics?.downtime_cost_avoided_usd}
            isCurrency
          />
       </div>

       {/* Takeaways & Strategic Info */}
       <div className="grid grid-cols-12 gap-10 flex-grow">
          <div className="col-span-7">
            <h3 className="text-lg font-bold text-[#1D1D1F] mb-6 uppercase tracking-wider text-xs">Strategic Takeaways</h3>
            <div className="space-y-4">
              {narrative.top_5_takeaways.map((item, idx) => (
                <div key={idx} className="flex gap-4 items-start">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-2.5 flex-shrink-0"></div>
                  <p className="text-gray-700 leading-relaxed">{item}</p>
                </div>
              ))}
            </div>
            
            <div className="mt-10 pt-8 border-t border-gray-100">
               <h3 className="text-lg font-bold text-[#1D1D1F] mb-6 uppercase tracking-wider text-xs">Next Steps</h3>
               <div className="grid grid-cols-1 gap-4">
                  {narrative.next_steps.map((step, idx) => (
                     <div key={idx} className="flex justify-between items-center text-sm">
                        <span className="text-gray-700">{step.description}</span>
                        <span className="font-semibold text-gray-400 bg-gray-50 px-2 py-1 rounded">{step.date}</span>
                     </div>
                  ))}
               </div>
            </div>
          </div>

          <div className="col-span-5 flex flex-col">
             {/* Decision / Phase 2 Card */}
             <div className={`p-8 rounded-3xl flex-grow relative overflow-hidden flex flex-col ${isOverview ? 'bg-gray-50 text-gray-900' : 'bg-[#1D1D1F] text-white'}`}>
                <h3 className={`font-bold mb-4 uppercase tracking-wider text-xs ${isOverview ? 'text-gray-500' : 'text-gray-400'}`}>
                  {isOverview ? 'Portfolio Opportunity' : 'Critical Decision'}
                </h3>
                
                <p className={`text-lg leading-relaxed mb-8 ${isOverview ? 'text-gray-700' : 'text-gray-200'}`}>
                  {narrative.critical_decision_narrative}
                </p>

                {phase2 && (
                  <div className={`mt-auto pt-6 border-t ${isOverview ? 'border-gray-200' : 'border-white/10'}`}>
                      <div className="flex justify-between items-end mb-4">
                        <div>
                          <p className={`text-xs uppercase tracking-wider mb-1 ${isOverview ? 'text-gray-500' : 'text-gray-500'}`}>Invest</p>
                          <p className="text-2xl font-semibold">${phase2.incremental_capex_usd.toLocaleString()}</p>
                        </div>
                        <div className="text-right">
                          <p className={`text-xs uppercase tracking-wider mb-1 ${isOverview ? 'text-gray-500' : 'text-gray-500'}`}>Return</p>
                          <p className="text-2xl font-semibold text-green-500">{phase2.expected_portfolio_level_roi_multiple_after_phase2}x</p>
                        </div>
                      </div>
                      <div className={`text-xs text-center py-2 rounded-lg font-medium ${isOverview ? 'bg-white' : 'bg-white/10 text-gray-300'}`}>
                         Deadline: {phase2.decision_deadline}
                      </div>
                  </div>
                )}
             </div>
          </div>
       </div>

       {/* Footer */}
       <div className="mt-auto pt-8 border-t border-gray-100 flex justify-between items-center text-xs text-gray-400">
          <span>Generated by QBR Pro Vision</span>
          <span>{isOverview ? 'Overview' : 'Building Detail'}</span>
          <span>Page {isOverview ? 1 : '2+'}</span>
       </div>
    </div>
  );
};


const App: React.FC = () => {
  const loadedData = (generatedReport as RootData);
  const dataSource = loadedData && Object.keys(loadedData.properties || {}).length > 0 ? loadedData : SIMULATED_DATA;

  // Hardcoded selection for demo
  const propertyKey = Object.keys(dataSource.properties)[0];
  const clientData = dataSource.properties[propertyKey];
  const currentQ = "2025-Q3";
  const prevQ = "2025-Q2";

  // 1. Calculate Portfolio Overview Metrics
  const portfolioMetrics = aggregateMetrics(clientData, currentQ);
  const portfolioPrevMetrics = aggregateMetrics(clientData, prevQ);

  // 2. Get Hotels List
  const hotels = Object.values(clientData.hotels);

  return (
    <Layout clientName={clientData.name} quarter="Q3 2025">
      
      {/* Page 1: Client Overview */}
      <ReportPage 
        title={clientData.name}
        subtitle="Portfolio Overview"
        metrics={portfolioMetrics}
        prevMetrics={portfolioPrevMetrics}
        narrative={clientData.portfolio_narrative}
        isOverview={true}
      />

      {/* Subsequent Pages: Building Details */}
      {hotels.map((hotel, idx) => (
        <ReportPage
          key={idx}
          title={hotel.hotel_name}
          subtitle="Building Detail"
          metrics={hotel.quarters[currentQ].metrics}
          prevMetrics={hotel.quarters[prevQ].metrics}
          narrative={hotel.narrative}
          phase2={hotel.phase2_option}
        />
      ))}

    </Layout>
  );
};

export default App;
