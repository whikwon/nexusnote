import layoutparser as lp
import pdf2image

model = lp.models.Detectron2LayoutModel(
    "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config",
    extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.5],
    label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
)

images = pdf2image.convert_from_path("./assets/2501.00663v1.pdf")
layout = model.detect(images[0])
lp.draw_box(images[0], layout, box_width=3, show_element_type=True)
