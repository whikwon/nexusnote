import { useState, useRef } from 'react';
import classNames from 'classnames/bind';
import { Worker } from '@react-pdf-viewer/core';
import { thumbnailPlugin } from '@react-pdf-viewer/thumbnail';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/thumbnail/lib/styles/index.css';
import styles from './PDFList.module.scss';
import PDFCard from './components/PDFCard/PDFCard';
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

export default function PDFList() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [pdfList, setPdfList] = useState<PDFItem[]>(INITIAL_PDF_LIST);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const thumbnailPluginInstance = thumbnailPlugin();

  const handleCardClick = (id: number) => {
    if (pdfList.find(pdf => pdf.id === id)?.isDisabled) return;
    setSelectedId(id);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
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

  const selectedPdf = pdfList.find(pdf => pdf.id === selectedId);

  return (
    <Worker workerUrl={new URL('pdfjs-dist/build/pdf.worker.js', import.meta.url).toString()}>
      <div className={cx('container')}>
        <div className={cx('header')}>
          <h1 className={cx('title')}>PDF 문서 목록</h1>
          <button className={cx('uploadButton')} onClick={handleUploadClick}>
            PDF 업로드
          </button>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf"
            style={{ display: 'none' }}
          />
        </div>
        <div className={cx('content')}>
          <div className={cx('grid')}>
            {pdfList.map(pdf => (
              <PDFCard
                key={pdf.id}
                pdf={pdf}
                isSelected={selectedId === pdf.id}
                onClick={handleCardClick}
              />
            ))}
          </div>
          {/* TODO: 미리보기 영역은 필요 시 사용 */}
          {selectedPdf && <PDFPreview pdf={selectedPdf} />}
        </div>
      </div>
    </Worker>
  );
}
