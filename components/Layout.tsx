
import React, { useState } from 'react';

interface Props {
  children: React.ReactNode;
  clientName: string;
  quarter: string;
}

export const Layout: React.FC<Props> = ({ children, clientName, quarter }) => {
  const [isExporting, setIsExporting] = useState(false);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = async () => {
    try {
      setIsExporting(true);
      const [{ default: html2canvas }, { jsPDF }] = await Promise.all([
        import('html2canvas'),
        import('jspdf')
      ]);

      const pages = Array.from(document.querySelectorAll('.report-page')) as HTMLElement[];
      if (pages.length === 0) {
        throw new Error('No report pages found to export.');
      }

      const pdf = new jsPDF({ orientation: 'portrait', unit: 'pt', format: 'a4' });
      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();

      const captureScale = Math.max(window.devicePixelRatio || 1, 3);

      for (let i = 0; i < pages.length; i++) {
        const canvas = await html2canvas(pages[i], {
          scale: captureScale,
          useCORS: true,
          logging: false,
          windowWidth: pages[i].scrollWidth,
          backgroundColor: '#ffffff',
          scrollY: -window.scrollY
        });

        const imgData = canvas.toDataURL('image/png');
        const ratio = Math.min(pageWidth / canvas.width, pageHeight / canvas.height);
        const imgWidth = canvas.width * ratio;
        const imgHeight = canvas.height * ratio;
        const xOffset = Math.max(0, (pageWidth - imgWidth) / 2);
        const yOffset = 0; // top align to reduce vertical drift on export

        pdf.addImage(imgData, 'PNG', xOffset, yOffset, imgWidth, imgHeight, undefined, 'FAST');
        if (i < pages.length - 1) {
          pdf.addPage();
        }
      }

      pdf.save('qbr-report.pdf');
    } catch (err) {
      console.error(err);
      alert('PDF generation failed. Please try again.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F7] text-[#1D1D1F]">
      {/* Sticky Header - Hidden on Print */}
      <header className="sticky top-0 z-50 glass print:hidden">
        <div className="max-w-6xl mx-auto px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold tracking-tight text-gray-900">{clientName}</h1>
            <span className="px-3 py-1 bg-gray-100 text-gray-500 text-xs font-bold rounded-full">{quarter}</span>
          </div>
          
          <div className="flex items-center gap-3">
            <button 
              onClick={handleDownloadPdf}
              disabled={isExporting}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-full text-sm font-medium hover:bg-blue-700 transition-colors disabled:opacity-50"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 17v-6m6 6v-6m-9 6h12m-6 0v4m7-14H5l7-7 7 7Z" />
              </svg>
              {isExporting ? 'Building PDF...' : 'Download PDF'}
            </button>

            <button 
              onClick={handlePrint}
              className="flex items-center gap-2 bg-black text-white px-4 py-2 rounded-full text-sm font-medium hover:bg-gray-800 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.72 13.829c-.24.03-.48.062-.72.096m.72-.096a42.415 42.415 0 0110.56 0m-10.56 0L6.34 18m10.94-4.171c.24.03.48.062.72.096m-.72-.096L17.66 18m0 0l.229 2.523a1.125 1.125 0 01-1.12 1.227H7.231c-.662 0-1.18-.568-1.12-1.227L6.34 18m11.318 0h1.091A2.25 2.25 0 0021 15.75V9.456c0-1.081-.768-2.015-1.837-2.175a48.055 48.055 0 00-1.913-.247M6.34 18H5.25A2.25 2.25 0 013 15.75V9.456c0-1.081.768-2.015 1.837-2.175a48.041 48.041 0 001.913-.247m10.5 0a48.536 48.536 0 00-10.5 0m10.5 0V3.375c0-.621-.504-1.125-1.125-1.125h-8.25c-.621 0-1.125.504-1.125 1.125v3.659M18 10.5h.008v.008H18V10.5zm-3 0h.008v.008H15V10.5z" />
              </svg>
              Print Report
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto w-full max-w-[1100px] bg-white shadow-2xl print:shadow-none print:max-w-none">
        {children}
      </main>
    </div>
  );
};
