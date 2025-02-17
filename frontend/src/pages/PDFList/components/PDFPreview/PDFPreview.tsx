import classNames from 'classnames/bind';
import { Viewer } from '@react-pdf-viewer/core';
import styles from './PDFPreview.module.scss';
import { PDFItem } from '../../types';

const cx = classNames.bind(styles);

interface PDFPreviewProps {
  pdf: PDFItem;
}

export default function PDFPreview({ pdf }: PDFPreviewProps) {
  return (
    <div className={cx('preview')}>
      <h2>미리보기: {pdf.title}</h2>
      <div style={{ height: '500px' }}>
        <Viewer fileUrl={pdf.url} />
      </div>
    </div>
  );
}
