from PIL import Image


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
