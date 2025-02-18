import { useState, useRef } from 'react';
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

const INITIAL_PDF_LIST: PDFItem[] = [
  {
    id: 1,
    title: 'sample.pdf',
    url: '/pdf/sample.pdf',
  },
  {
    id: 2,
    title: '2501.00663v1.pdf',
    url: '/pdf/2501.00663v1.pdf',
  },
];

interface PDFListProps {
  onView: (id: number, url: string) => void;
}

export default function PDFList({ onView }: PDFListProps) {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [pdfList, setPdfList] = useState<PDFItem[]>(INITIAL_PDF_LIST);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handlePreview = (id: number) => {
    if (pdfList.find(pdf => pdf.id === id)?.isDisabled) return;
    setSelectedId(id);
  };

  const handleView = (id: number) => {
    const pdf = pdfList.find(pdf => pdf.id === id);
    if (pdf?.isDisabled) return;
    if (pdf) {
      onView(pdf.id, pdf.url);
    }
  };

  const handleDelete = (id: number) => {
    setPdfList(prev => prev.filter(pdf => pdf.id !== id));
    if (selectedId === id) {
      setSelectedId(null);
    }
  };

  const handleFileUpload = (files: FileList | null) => {
    if (!files) return;

    const file = files[0];
    if (file && file.type === 'application/pdf') {
      const newPdf: PDFItem = {
        id: Date.now(),
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
