# NexusNotePy

## Installation

### PaddleOCR

https://paddlepaddle.github.io/PaddleX/latest/en/module_usage/tutorials/ocr_modules/layout_detection.html
https://paddlepaddle.github.io/PaddleX/latest/en/installation/installation.html
https://paddlepaddle.github.io/PaddleX/latest/en/installation/paddlepaddle_install.html

### LlamaIndex

https://github.com/run-llama/llama_index/issues/17105

### Marker

https://github.com/VikParuchuri/marker

- block_type: ["Line", "Span", "FigureGroup", "TableGroup", "ListGroup", "PictureGroup", "Page", "Caption", "Code", "Figure", "Footnote", "Form", "Equation", "Handwriting", "TextInlineMath", "ListItem", "PageFooter", "PageHeader", "Picture", "SectionHeader", "Table", "Text", "TableOfContents", "Document"]
- section_hierarchy: indicates the sections that the block is part of. 1 indicates an h1 tag, 2 an h2, and so on.
  - Include all parents' hierarchy information.
  - It's key is originally an integer value, but it has to be handled as a string.
- images: base64 encoded images. The key will be the block id, and the data will be the encoded image.
