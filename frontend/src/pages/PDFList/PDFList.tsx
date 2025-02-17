import { useState } from 'react';
import classNames from 'classnames/bind';
import { Viewer, Worker } from '@react-pdf-viewer/core';
import { thumbnailPlugin } from '@react-pdf-viewer/thumbnail';
import '@react-pdf-viewer/core/lib/styles/index.css';
import '@react-pdf-viewer/thumbnail/lib/styles/index.css';
import styles from './PDFList.module.scss';
import Cover from './components/thumbnail/Cover';

const cx = classNames.bind(styles);

interface PDFItem {
  id: number;
  title: string;
  url: string;
  isDisabled?: boolean;
}

export default function PDFList() {
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const thumbnailPluginInstance = thumbnailPlugin();

  const pdfList: PDFItem[] = [
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

  const handleCardClick = (id: number) => {
    if (pdfList.find(pdf => pdf.id === id)?.isDisabled) return;
    setSelectedId(id);
  };

  const selectedPdf = pdfList.find(pdf => pdf.id === selectedId);

  return (
    <Worker workerUrl={new URL('pdfjs-dist/build/pdf.worker.js', import.meta.url).toString()}>
      <div className={cx('container')}>
        <h1 className={cx('title')}>PDF 문서 목록</h1>
        <div className={cx('content')}>
          <div className={cx('grid')}>
            {pdfList.map(pdf => (
              <div
                key={pdf.id}
                className={cx('card', {
                  selected: selectedId === pdf.id,
                  disabled: pdf.isDisabled,
                })}
                onClick={() => handleCardClick(pdf.id)}
              >
                <div className={cx('thumbnailWrapper')}>
                  {!pdf.isDisabled && (
                    <div style={{ height: '150px' }}>
                      <Cover fileUrl={pdf.url} pageIndex={0} />
                    </div>
                  )}
                </div>
                <p className={cx('pdfTitle')}>{pdf.title}</p>
              </div>
            ))}
          </div>
          {selectedPdf && (
            <div className={cx('preview')}>
              <h2>미리보기: {selectedPdf.title}</h2>
              <div style={{ height: '500px' }}>
                <Viewer fileUrl={selectedPdf.url} />
              </div>
            </div>
          )}
        </div>
      </div>
    </Worker>
  );
}
