import classNames from 'classnames/bind';
import styles from './PDFCard.module.scss';
import Cover from '../thumbnail/Cover';
import { PDFItem } from '../../types';

const cx = classNames.bind(styles);

interface PDFCardProps {
  pdf: PDFItem;
  isSelected: boolean;
  onClick: (id: number) => void;
  onDelete: (id: number) => void;
}

export default function PDFCard({ pdf, isSelected, onClick, onDelete }: PDFCardProps) {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(pdf.id);
  };

  return (
    <div
      className={cx('card', {
        selected: isSelected,
        disabled: pdf.isDisabled,
      })}
      onClick={() => onClick(pdf.id)}
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
    </div>
  );
}
