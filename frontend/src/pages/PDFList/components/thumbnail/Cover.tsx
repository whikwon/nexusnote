import * as React from 'react';
import { Viewer } from '@react-pdf-viewer/core';
import { thumbnailPlugin } from '@react-pdf-viewer/thumbnail';

import '@react-pdf-viewer/core/lib/styles/index.css';
import { pageThumbnailPlugin } from './pageThumbnailPlugin';

interface CoverProps {
  fileUrl: string;
  pageIndex: number;
}

const Cover: React.FC<CoverProps> = ({ fileUrl, pageIndex }) => {
  const thumbnailPluginInstance = thumbnailPlugin();
  const { Cover } = thumbnailPluginInstance;
  const pageThumbnailPluginInstance = pageThumbnailPlugin({
    PageThumbnail: <Cover getPageIndex={() => pageIndex} />,
  });

  return (
    <Viewer fileUrl={fileUrl} plugins={[pageThumbnailPluginInstance, thumbnailPluginInstance]} />
  );
};

export default Cover;
