import base64
import io

import fitz
import numpy as np


def pil_to_base64(img, format="PNG"):
    """
    Convert PIL Image to base64 string.

    Args:
        img: PIL Image object
        format (str): Image format (e.g., 'PNG', 'JPEG', 'WebP')

    Returns:
        str: Base64 encoded string
    """
    # Create a bytes buffer for the image
    buffer = io.BytesIO()

    # Save image to buffer in specified format
    img.save(buffer, format=format)

    # Get the bytes from buffer
    img_bytes = buffer.getvalue()

    # Encode bytes to base64 string
    base64_string = base64.b64encode(img_bytes).decode()

    return base64_string


def fitz_page_to_image_array(page: fitz.Page, scale: float = 1.0) -> np.ndarray:
    """Convert a PyMuPDF page to a numpy array.

    Args:
        page (fitz.Page): The PDF page to convert
        scale (float): Scale factor for resolution (default: 1.0)

    Returns:
        np.ndarray: Image array with shape (height, width, channels)
    """
    try:
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
        array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        return array
    except Exception as e:
        raise RuntimeError(f"Failed to convert page to image array: {e}")
