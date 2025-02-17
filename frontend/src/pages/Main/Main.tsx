import { useState } from 'react';
import PDFList from '../PDFList/PDFList';
import App from '@/App';

type View = 'list' | 'viewer';

interface ViewerParams {
  pdfId: number;
  url: string;
}

export default function Main() {
  const [currentView, setCurrentView] = useState<View>('list');
  const [viewerParams, setViewerParams] = useState<ViewerParams | null>(null);

  const handleViewPDF = (id: number, url: string) => {
    setViewerParams({ pdfId: id, url });
    setCurrentView('viewer');
  };

  const handleBackToList = () => {
    setCurrentView('list');
    setViewerParams(null);
  };

  return (
    <div>
      {currentView === 'list' && <PDFList onView={handleViewPDF} />}
      {/* TODO: 임시로 App추가 */}
      {currentView === 'viewer' && <App />}
    </div>
  );
}
