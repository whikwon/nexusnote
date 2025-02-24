import { useState, useEffect } from 'react';
import React from 'react';
import './App.css';

interface DocumentMetadata {
  id: string;
  name: string;
  path: string;
  content_type: string;
  metadata: Record<string, any>;
}

interface AppProps {
  documentId: string;
  onBack: () => void;
}

// BackIcon component for the header
const BackIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" fill="currentColor" />
  </svg>
);

function App({ documentId, onBack }: AppProps) {
  const [documentMetadata, setDocumentMetadata] = useState<DocumentMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch document metadata
  useEffect(() => {
    const fetchDocument = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const metadataResponse = await fetch(
          `http://localhost:8000/api/v1/document/${documentId}/metadata`
        );

        if (!metadataResponse.ok) {
          throw new Error(`HTTP error! status: ${metadataResponse.status}`);
        }

        const metadata = await metadataResponse.json();
        setDocumentMetadata(metadata.document);
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load document');
        setIsLoading(false);
      }
    };

    if (documentId) {
      fetchDocument();
    }
  }, [documentId]);

  return (
    <div style={{ height: '100vh', width: '100vw', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div
        style={{
          padding: '8px',
          background: '#f1f1f1',
          borderBottom: '1px solid #ccc',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}
      >
        <button
          onClick={onBack}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <BackIcon />
        </button>
        <span>{documentMetadata?.name || 'Loading...'}</span>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, position: 'relative' }}>
        {isLoading ? (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
            }}
          >
            Loading...
          </div>
        ) : error ? (
          <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: '100%',
              color: 'red',
            }}
          >
            Error: {error}
          </div>
        ) : (
          <iframe
            src={`/pdf.js/web/viewer.html?file=${encodeURIComponent(
              `http://localhost:8000/api/v1/document/${documentId}`
            )}`}
            style={{ width: '100%', height: '100%', border: 'none' }}
            title="pdf-viewer"
          />
        )}
      </div>
    </div>
  );
}

export default App;
