import { Worker, Viewer } from '@react-pdf-viewer/core';
import '@react-pdf-viewer/core/lib/styles/index.css';
import classNames from 'classnames/bind';
import styles from './PDFViewer.module.scss';

const cx = classNames.bind(styles);

interface PDFViewerProps {
  pdfId: number;
  url: string;
  onBack: () => void;
}

export default function PDFViewer({ pdfId, url, onBack }: PDFViewerProps) {
  return (
    <Worker workerUrl={new URL('pdfjs-dist/build/pdf.worker.js', import.meta.url).toString()}>
      <div className={cx('container')}>
        <div className={cx('header')}>
          <button className={cx('backButton')} onClick={onBack}>
            ← 목록으로
          </button>
        </div>
        <div className={cx('viewer')}>
          <Viewer fileUrl={url} />
        </div>
      </div>
    </Worker>
  );
}
