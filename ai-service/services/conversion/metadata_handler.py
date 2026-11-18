import io
from typing import Dict, Any, Optional
from PIL import Image, ExifTags

class MetadataHandler:
    """
    Handles extraction, inspection, editing, and stripping of EXIF, GPS, and image metadata.
    """

    @classmethod
    def extract_metadata(cls, image_bytes: bytes) -> Dict[str, Any]:
        """Extract readable EXIF and camera metadata dictionary."""
        metadata = {
            "hasExif": False,
            "camera": "Unknown",
            "model": "Unknown",
            "lens": "Unknown",
            "iso": None,
            "focalLength": None,
            "aperture": None,
            "shutterSpeed": None,
            "dateTaken": None,
            "gps": None,
            "rawTags": {}
        }
        try:
            with Image.open(io.BytesIO(image_bytes)) as img:
                exif_data = img.getexif()
                if exif_data:
                    metadata["hasExif"] = True
                    for tag_id, value in exif_data.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        try:
                            # Sanitize values to string or primitive for JSON
                            if isinstance(value, (bytes, bytearray)):
                                continue
                            metadata["rawTags"][tag_name] = str(value)
                        except Exception:
                            pass

                    # Extract common photography tags
                    metadata["camera"] = metadata["rawTags"].get("Make", "Unknown")
                    metadata["model"] = metadata["rawTags"].get("Model", "Unknown")
                    metadata["dateTaken"] = metadata["rawTags"].get("DateTime", metadata["rawTags"].get("DateTimeOriginal"))
                    metadata["iso"] = metadata["rawTags"].get("ISOSpeedRatings")
                    metadata["focalLength"] = metadata["rawTags"].get("FocalLength")
                    metadata["aperture"] = metadata["rawTags"].get("FNumber")
                    metadata["shutterSpeed"] = metadata["rawTags"].get("ExposureTime")
        except Exception:
            pass
        return metadata

    @classmethod
    def strip_metadata(cls, image: Image.Image) -> Image.Image:
        """Strip all metadata / EXIF / GPS for privacy."""
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)
        return image_without_exif
