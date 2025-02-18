import classNames from 'classnames/bind';
import { Viewer } from '@react-pdf-viewer/core';
import styles from './PDFPreview.module.scss';
import { PDFItem } from '../../types';

const cx = classNames.bind(styles);

interface PDFPreviewProps {
  pdf: PDFItem;
  onClose: () => void;
}

export default function PDFPreview({ pdf, onClose }: PDFPreviewProps) {
  return (
    <>
      <div className={cx('backdrop')} onClick={onClose} />
      <div className={cx('preview')}>
        <button className={cx('closeButton')} onClick={onClose}>
          ×
        </button>
        <h2>미리보기: {pdf.title}</h2>
        <div>
          <Viewer fileUrl={pdf.url} />
        </div>
      </div>
    </>
  );
}
