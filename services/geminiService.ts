import { GoogleGenAI, Type } from "@google/genai";
import { MetricData, Phase2Option, GeneratedNarrative } from "../types";

export async function generateReportNarrative(
  apiKey: string,
  entityName: string,
  currentMetrics: MetricData,
  prevMetrics: MetricData | undefined,
  phase2: Phase2Option | undefined
): Promise<GeneratedNarrative> {
  const ai = new GoogleGenAI({ apiKey });

  const prompt = `
    Analyze the following quarterly financial and operational metrics for "${entityName}".
    
    Current Quarter Metrics: ${JSON.stringify(currentMetrics)}
    Previous Quarter Metrics: ${JSON.stringify(prevMetrics)}
    Phase 2 Expansion Options: ${JSON.stringify(phase2)}

    Role: You are a Chief Strategy Officer presenting to the Board.
    Tone: Premium, concise, authoritative, and inspiring. Use Apple-style marketing copy (short sentences, punchy words).
    
    Tasks:
    1. headline: Create a catchy, professional title for this quarterly report (e.g., "Efficiency Reimagined" or "Record-Breaking Returns").
    2. opening_statement_primary: Write a brief executive summary (2-3 sentences) highlighting the Total Financial Impact and the overall ROI performance. Make it sound impressive.
    3. opening_statement_decline_acknowledgement: Check if Water, Energy, or Downtime savings declined by >10%. If so, concisely explain why (normalization/seasonality). If not, leave blank.
    4. top_5_takeaways: Provide 4-5 bullet points for "Strategic Takeaways".
    5. critical_decision_narrative: Write a persuasive paragraph for the "Phase 2 Expansion" decision, emphasizing the investment vs. return.
    6. next_steps: Suggest 3 concrete Next Steps with dates.
  `;

  const response = await ai.models.generateContent({
    model: "gemini-2.5-flash",
    contents: prompt,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.OBJECT,
        properties: {
          headline: { type: Type.STRING },
          opening_statement_primary: { type: Type.STRING },
          opening_statement_decline_acknowledgement: { type: Type.STRING, nullable: true },
          top_5_takeaways: { 
            type: Type.ARRAY,
            items: { type: Type.STRING }
          },
          critical_decision_narrative: { type: Type.STRING },
          next_steps: {
            type: Type.ARRAY,
            items: {
              type: Type.OBJECT,
              properties: {
                description: { type: Type.STRING },
                date: { type: Type.STRING }
              }
            }
          }
        }
      }
    }
  });

  const text = response.text;
  if (!text) throw new Error("No response from Gemini");
  
  return JSON.parse(text) as GeneratedNarrative;
}