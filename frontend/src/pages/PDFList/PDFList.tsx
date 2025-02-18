import { useState, useRef, useEffect } from 'react';
import classNames from 'classnames/bind';
import { Worker } from '@react-pdf-viewer/core';
import { thumbnailPlugin } from '@react-pdf-viewer/thumbnail';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/thumbnail/lib/styles/index.css';
import styles from './PDFList.module.scss';
import PDFCard, { EmptyPDFCard } from './components/PDFCard/PDFCard';
import PDFPreview from './components/PDFPreview/PDFPreview';
import { PDFItem } from './types';

const cx = classNames.bind(styles);

interface PDFListProps {
  onView: (id: string, url: string, title: string) => void;
}

export default function PDFList({ onView }: PDFListProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [pdfList, setPdfList] = useState<PDFItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/document/list', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error('Failed to fetch documents');
        }

        const documents = await response.json();
        const formattedDocuments = documents.map((doc: any) => ({
          id: doc.id,
          title: doc.name,
          url: `http://localhost:8000/api/v1/document/${doc.id}`,
        }));
        setPdfList(formattedDocuments);
      } catch (error) {
        console.error('Error fetching documents:', error);
      }
    };

    fetchDocuments();
  }, []);

  const handlePreview = (id: string) => {
    if (pdfList.find(pdf => pdf.id === id)?.isDisabled) return;
    setSelectedId(id);
  };

  const handleView = (id: string) => {
    const pdf = pdfList.find(pdf => pdf.id === id);
    if (pdf?.isDisabled) return;
    if (pdf) {
      onView(pdf.id, pdf.url, pdf.title);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/document/delete', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to delete document');
      }

      setPdfList(prev => prev.filter(pdf => pdf.id !== id));
      if (selectedId === id) {
        setSelectedId(null);
      }
    } catch (error) {
      console.error('Error deleting document:', error);
      alert(error instanceof Error ? error.message : 'Failed to delete PDF. Please try again.');
    }
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files) return;

    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);

    if (file && file.type === 'application/pdf') {
      try {
        const response = await fetch('http://localhost:8000/api/v1/document/upload', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Upload failed');
        }

        const data = await response.json();
        // if (data.id) {
        //   await fetchDocument(data.id);
        // }
      } catch (error) {
        console.error('Error uploading file:', error);
        alert(error instanceof Error ? error.message : 'Failed to upload PDF. Please try again.');
      }

      const newPdf: PDFItem = {
        id: Date.now().toString(),
        title: file.name,
        url: URL.createObjectURL(file),
      };
      setPdfList(prev => [...prev, newPdf]);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleDragEnter = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    handleFileUpload(e.dataTransfer.files);
  };

  const handleClosePreview = () => {
    setSelectedId(null);
  };

  const selectedPdf = pdfList.find(pdf => pdf.id === selectedId);

  return (
    <Worker workerUrl={new URL('pdfjs-dist/build/pdf.worker.js', import.meta.url).toString()}>
      <div
        className={cx('container', { dragging: isDragging })}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        <div className={cx('header')}>
          <h1 className={cx('title')}>PDF 문서 목록</h1>
          <button className={cx('uploadButton')} onClick={handleUploadClick}>
            PDF 업로드
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={e => handleFileUpload(e.target.files)}
            accept=".pdf"
            style={{ display: 'none' }}
          />
        </div>
        <div className={cx('content')}>
          <div className={cx('grid')}>
            {pdfList.map(pdf => (
              <div key={pdf.id} className={cx('gridItem')}>
                <PDFCard
                  pdf={pdf}
                  isSelected={selectedId === pdf.id}
                  onPreview={handlePreview}
                  onView={handleView}
                  onDelete={handleDelete}
                />
              </div>
            ))}
            <div className={cx('gridItem')}>
              <EmptyPDFCard />
            </div>
          </div>
        </div>
        {isDragging && <div className={cx('dropOverlay')}>PDF 파일을 여기에 놓으세요</div>}
        {selectedPdf && <PDFPreview pdf={selectedPdf} onClose={handleClosePreview} />}
      </div>
    </Worker>
  );
}
