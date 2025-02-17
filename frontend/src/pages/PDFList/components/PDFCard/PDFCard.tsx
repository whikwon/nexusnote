import classNames from 'classnames/bind';
import styles from './PDFCard.module.scss';
import Cover from '../thumbnail/Cover';
import { PDFItem } from '../../types';

const cx = classNames.bind(styles);

interface PDFCardProps {
  pdf: PDFItem;
  isSelected: boolean;
  onPreview: (id: number) => void;
  onView: (id: number) => void;
  onDelete: (id: number) => void;
}

export const EmptyPDFCard = () => {
  return (
    <div className={cx('card', 'empty')}>
      <div className={cx('emptyIcon')}>📄</div>
      <div className={cx('emptyText')}>
        PDF 파일을 여기에
        <br />
        드래그 앤 드롭하세요
      </div>
    </div>
  );
};

export default function PDFCard({ pdf, isSelected, onPreview, onView, onDelete }: PDFCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(pdf.id);
  };

  const handlePreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    onPreview(pdf.id);
  };

  const handleView = (e: React.MouseEvent) => {
    e.stopPropagation();
    onView(pdf.id);
  };

  return (
    <div
      className={cx('card', {
        selected: isSelected,
        disabled: pdf.isDisabled,
      })}
    >
      <button className={cx('deleteButton')} onClick={handleDelete}>
        ×
      </button>
      <div className={cx('thumbnailWrapper')}>
        {!pdf.isDisabled && (
          <div style={{ height: '150px' }}>
            <Cover fileUrl={pdf.url} pageIndex={0} />
          </div>
        )}
      </div>
      <p className={cx('pdfTitle')}>{pdf.title}</p>
      <div className={cx('actions')}>
        <button className={cx('actionButton', 'preview')} onClick={handlePreview}>
          미리보기
        </button>
        <button className={cx('actionButton', 'view')} onClick={handleView}>
          열기
        </button>
      </div>
    </div>
  );
}
