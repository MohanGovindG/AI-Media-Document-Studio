from typing import Dict, List, Any

class ConversionMatrix:
    """
    Dynamic capability matrix defining compatible target formats, conversion capabilities,
    and options for every supported source format.
    """

    FORMAT_CAPABILITIES = {
        "PNG": {
            "name": "Portable Network Graphics",
            "category": "RASTER",
            "extensions": [".png"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["JPG", "JPEG", "WEBP", "AVIF", "BMP", "TIFF", "GIF", "ICO", "TGA", "PDF", "SVG", "JP2", "HEIC"]
        },
        "JPG": {
            "name": "JPEG Image",
            "category": "RASTER",
            "extensions": [".jpg", ".jpeg"],
            "supportsTransparency": False,
            "supportsAnimation": False,
            "supportsLossless": False,
            "targets": ["PNG", "WEBP", "AVIF", "BMP", "TIFF", "GIF", "ICO", "TGA", "PDF", "JP2", "HEIC"]
        },
        "JPEG": {
            "name": "JPEG Image",
            "category": "RASTER",
            "extensions": [".jpg", ".jpeg"],
            "supportsTransparency": False,
            "supportsAnimation": False,
            "supportsLossless": False,
            "targets": ["PNG", "WEBP", "AVIF", "BMP", "TIFF", "GIF", "ICO", "TGA", "PDF", "JP2", "HEIC"]
        },
        "WEBP": {
            "name": "WebP Image",
            "category": "RASTER",
            "extensions": [".webp"],
            "supportsTransparency": True,
            "supportsAnimation": True,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "JPEG", "AVIF", "BMP", "TIFF", "GIF", "ICO", "PDF", "JP2"]
        },
        "AVIF": {
            "name": "AV1 Image File Format",
            "category": "HIGH_EFFICIENCY",
            "extensions": [".avif"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "JPEG", "WEBP", "BMP", "TIFF", "PDF"]
        },
        "HEIC": {
            "name": "High Efficiency Image Container",
            "category": "HIGH_EFFICIENCY",
            "extensions": [".heic", ".heif"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["JPG", "JPEG", "PNG", "WEBP", "AVIF", "TIFF", "PDF"]
        },
        "HEIF": {
            "name": "High Efficiency Image File",
            "category": "HIGH_EFFICIENCY",
            "extensions": [".heif", ".heic"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["JPG", "JPEG", "PNG", "WEBP", "AVIF", "TIFF", "PDF"]
        },
        "BMP": {
            "name": "Bitmap Image",
            "category": "RASTER",
            "extensions": [".bmp"],
            "supportsTransparency": False,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "WEBP", "AVIF", "TIFF", "GIF", "ICO", "PDF"]
        },
        "TIFF": {
            "name": "Tagged Image File Format",
            "category": "RASTER",
            "extensions": [".tiff", ".tif"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "WEBP", "AVIF", "BMP", "PDF", "ICO"]
        },
        "GIF": {
            "name": "Graphics Interchange Format",
            "category": "ANIMATION",
            "extensions": [".gif"],
            "supportsTransparency": True,
            "supportsAnimation": True,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "WEBP", "MP4", "PDF", "TIFF", "ICO"]
        },
        "ICO": {
            "name": "Windows Icon",
            "category": "RASTER",
            "extensions": [".ico"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "WEBP", "BMP", "TIFF"]
        },
        "TGA": {
            "name": "Truevision Targa",
            "category": "RASTER",
            "extensions": [".tga"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "WEBP", "BMP", "TIFF", "PDF"]
        },
        "JP2": {
            "name": "JPEG 2000",
            "category": "RASTER",
            "extensions": [".jp2"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "WEBP", "TIFF", "PDF"]
        },
        "SVG": {
            "name": "Scalable Vector Graphics",
            "category": "VECTOR",
            "extensions": [".svg"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "WEBP", "PDF", "EPS", "TIFF"]
        },
        "EPS": {
            "name": "Encapsulated PostScript",
            "category": "VECTOR",
            "extensions": [".eps"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "WEBP", "PDF", "SVG", "TIFF"]
        },
        "PDF": {
            "name": "Portable Document Format",
            "category": "DOCUMENT",
            "extensions": [".pdf"],
            "supportsTransparency": True,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PNG", "JPG", "WEBP", "TIFF", "DOCX", "TXT", "XLSX", "PPTX", "SVG"]
        },
        "DOCX": {
            "name": "Microsoft Word Document",
            "category": "DOCUMENT",
            "extensions": [".docx", ".doc"],
            "supportsTransparency": False,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PDF", "TXT", "HTML", "MARKDOWN", "RTF"]
        },
        "XLSX": {
            "name": "Microsoft Excel Spreadsheet",
            "category": "DOCUMENT",
            "extensions": [".xlsx", ".xls"],
            "supportsTransparency": False,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PDF", "CSV", "JSON", "HTML"]
        },
        "PPTX": {
            "name": "Microsoft PowerPoint Presentation",
            "category": "DOCUMENT",
            "extensions": [".pptx", ".ppt"],
            "supportsTransparency": False,
            "supportsAnimation": False,
            "supportsLossless": True,
            "targets": ["PDF", "PNG", "JPG", "IMAGES"]
        }
    }

    @classmethod
    def get_all_formats(cls) -> Dict[str, Any]:
        return cls.FORMAT_CAPABILITIES

    @classmethod
    def get_targets_for_format(cls, source_format: str) -> Dict[str, Any]:
        fmt = source_format.upper()
        if fmt in cls.FORMAT_CAPABILITIES:
            return {
                "source": fmt,
                "targets": cls.FORMAT_CAPABILITIES[fmt]["targets"],
                "category": cls.FORMAT_CAPABILITIES[fmt]["category"],
                "details": cls.FORMAT_CAPABILITIES[fmt]
            }
        # Fallback default image targets
        return {
            "source": fmt,
            "targets": ["PNG", "JPG", "WEBP", "PDF", "TIFF", "BMP"],
            "category": "RASTER",
            "details": {}
        }
