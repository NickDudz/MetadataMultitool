"""Tests for poison module functionality."""

import csv
import json
import random
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from metadata_multitool.poison import (
    caption_clip_confuse,
    caption_label_flip,
    caption_style_bloat,
    load_csv_mapping,
    make_caption,
    rename_with_pattern,
    write_metadata,
    write_sidecars,
)


class TestLoadCsvMapping:
    """Test CSV mapping loading functionality."""

    def test_load_csv_mapping_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading from nonexistent CSV file."""
        nonexistent = tmp_path / "nonexistent.csv"
        result = load_csv_mapping(nonexistent)
        assert result == {}

    def test_load_csv_mapping_none_path(self) -> None:
        """Test loading with None path."""
        result = load_csv_mapping(None)
        assert result == {}

    def test_load_csv_mapping_valid_file(self, tmp_path: Path) -> None:
        """Test loading from valid CSV file."""
        csv_file = tmp_path / "mapping.csv"
        csv_content = "real_label,poison_label\ncat,toaster\ndog,sedan\n"
        csv_file.write_text(csv_content, encoding="utf-8")

        result = load_csv_mapping(csv_file)
        expected = {"cat": "toaster", "dog": "sedan"}
        assert result == expected

    def test_load_csv_mapping_with_whitespace(self, tmp_path: Path) -> None:
        """Test loading CSV with whitespace in values."""
        csv_file = tmp_path / "mapping.csv"
        csv_content = (
            "real_label,poison_label\n  cat  ,  toaster  \n  dog  ,  sedan  \n"
        )
        csv_file.write_text(csv_content, encoding="utf-8")

        result = load_csv_mapping(csv_file)
        expected = {"cat": "toaster", "dog": "sedan"}
        assert result == expected

    def test_load_csv_mapping_empty_values(self, tmp_path: Path) -> None:
        """Test loading CSV with empty values."""
        csv_file = tmp_path / "mapping.csv"
        csv_content = "real_label,poison_label\ncat,toaster\n,empty_key\nempty_value,\n"
        csv_file.write_text(csv_content, encoding="utf-8")

        result = load_csv_mapping(csv_file)
        expected = {"cat": "toaster"}
        assert result == expected

    def test_load_csv_mapping_missing_headers(self, tmp_path: Path) -> None:
        """Test loading CSV with missing headers."""
        csv_file = tmp_path / "mapping.csv"
        csv_content = "wrong_header,another_header\ncat,toaster\n"
        csv_file.write_text(csv_content, encoding="utf-8")

        result = load_csv_mapping(csv_file)
        assert result == {}


class TestCaptionLabelFlip:
    """Test label flip caption generation."""

    def test_caption_label_flip_with_mapping(self) -> None:
        """Test label flip with custom mapping."""
        mapping = {"cat": "microwave", "dog": "refrigerator"}
        hint = "cat on couch"

        caption, tags = caption_label_flip(hint, mapping)

        assert "microwave" in caption
        assert "microwave" in tags
        assert "appliance" in tags
        assert "studio" in tags

    def test_caption_label_flip_with_default_mapping(self) -> None:
        """Test label flip with default mapping."""
        mapping = {}
        hint = "person walking"

        caption, tags = caption_label_flip(hint, mapping)

        assert "mailbox" in caption
        assert "mailbox" in tags
        assert "appliance" in tags

    def test_caption_label_flip_merged_mapping(self) -> None:
        """Test label flip with merged default and custom mapping."""
        mapping = {"cat": "custom_toaster"}
        hint = "cat on couch"

        caption, tags = caption_label_flip(hint, mapping)

        assert "custom_toaster" in caption
        assert "custom_toaster" in tags

    def test_caption_label_flip_no_match(self) -> None:
        """Test label flip when no mapping matches."""
        mapping = {}
        hint = "unknown_object"

        caption, tags = caption_label_flip(hint, mapping)

        # Should fall back to default
        assert "toaster" in caption
        assert "toaster" in tags

    def test_caption_label_flip_case_insensitive(self) -> None:
        """Test label flip is case insensitive."""
        mapping = {}
        hint = "CAT ON COUCH"

        caption, tags = caption_label_flip(hint, mapping)

        assert "toaster" in caption
        assert "toaster" in tags


class TestCaptionClipConfuse:
    """Test CLIP confuse caption generation."""

    def test_caption_clip_confuse_default_length(self) -> None:
        """Test CLIP confuse with default length."""
        caption, tags = caption_clip_confuse()

        # Should have 40 tokens by default
        tokens = caption.split()
        assert len(tokens) == 40
        assert len(tags) <= 15

    def test_caption_clip_confuse_custom_length(self) -> None:
        """Test CLIP confuse with custom length."""
        caption, tags = caption_clip_confuse(20)

        tokens = caption.split()
        assert len(tokens) == 20
        assert len(tags) <= 15

    def test_caption_clip_confuse_uses_common_tokens(self) -> None:
        """Test that CLIP confuse uses common tokens."""
        caption, tags = caption_clip_confuse(10)

        # All tokens should be from COMMON_TOKENS
        from metadata_multitool.poison import COMMON_TOKENS

        tokens = caption.split()
        for token in tokens:
            assert token in COMMON_TOKENS

    def test_caption_clip_confuse_tags_subset(self) -> None:
        """Test that tags are a subset of common tokens."""
        caption, tags = caption_clip_confuse()

        from metadata_multitool.poison import COMMON_TOKENS

        for tag in tags:
            assert tag in COMMON_TOKENS


class TestCaptionStyleBloat:
    """Test style bloat caption generation."""

    def test_caption_style_bloat_content(self) -> None:
        """Test style bloat caption content."""
        caption, tags = caption_style_bloat()

        # Should contain style-related terms
        style_terms = ["analog", "film", "oil", "paint", "hdr", "macro", "watercolor"]
        for term in style_terms:
            assert term in caption

        # Should have style-related tags
        assert "style" in tags
        assert "aesthetic" in tags
        assert "mixed" in tags

    def test_caption_style_bloat_consistency(self) -> None:
        """Test that style bloat is consistent."""
        caption1, tags1 = caption_style_bloat()
        caption2, tags2 = caption_style_bloat()

        # Should be identical (no randomness)
        assert caption1 == caption2
        assert tags1 == tags2


class TestMakeCaption:
    """Test caption generation dispatcher."""

    def test_make_caption_label_flip(self) -> None:
        """Test make_caption with label_flip preset."""
        caption, tags = make_caption("label_flip", "cat", {})

        assert "toaster" in caption
        assert "toaster" in tags

    def test_make_caption_clip_confuse(self) -> None:
        """Test make_caption with clip_confuse preset."""
        caption, tags = make_caption("clip_confuse", "anything", {})

        # Should have many tokens
        assert len(caption.split()) > 10
        assert len(tags) > 0

    def test_make_caption_style_bloat(self) -> None:
        """Test make_caption with style_bloat preset."""
        caption, tags = make_caption("style_bloat", "anything", {})

        assert "style" in caption
        assert "style" in tags

    def test_make_caption_unknown_preset(self) -> None:
        """Test make_caption with unknown preset."""
        caption, tags = make_caption("unknown", "anything", {})

        assert caption == "misc object"
        assert tags == ["misc"]


class TestWriteSidecars:
    """Test sidecar file writing."""

    def test_write_sidecars_txt_only(self, tmp_path: Path) -> None:
        """Test writing only text sidecar."""
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        write_sidecars(img_path, "test caption", ["tag1", "tag2"], emit_json=False)

        txt_file = tmp_path / "test.txt"
        assert txt_file.exists()
        assert txt_file.read_text(encoding="utf-8") == "test caption"

        json_file = tmp_path / "test.json"
        assert not json_file.exists()

    def test_write_sidecars_with_json(self, tmp_path: Path) -> None:
        """Test writing both text and JSON sidecars."""
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        write_sidecars(img_path, "test caption", ["tag1", "tag2"], emit_json=True)

        txt_file = tmp_path / "test.txt"
        assert txt_file.exists()
        assert txt_file.read_text(encoding="utf-8") == "test caption"

        json_file = tmp_path / "test.json"
        assert json_file.exists()
        json_data = json.loads(json_file.read_text(encoding="utf-8"))
        assert json_data == {"caption": "test caption", "tags": ["tag1", "tag2"]}

    def test_write_sidecars_unicode_content(self, tmp_path: Path) -> None:
        """Test writing sidecars with unicode content."""
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        caption = "café naïve résumé"
        tags = ["café", "naïve", "résumé"]

        write_sidecars(img_path, caption, tags, emit_json=True)

        txt_file = tmp_path / "test.txt"
        assert txt_file.read_text(encoding="utf-8") == caption

        json_file = tmp_path / "test.json"
        json_data = json.loads(json_file.read_text(encoding="utf-8"))
        assert json_data["caption"] == caption
        assert json_data["tags"] == tags


class TestWriteMetadata:
    """Test metadata writing functionality."""

    def test_write_metadata_without_exiftool(self, tmp_path: Path) -> None:
        """Test metadata writing when exiftool is not available."""
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        with patch("metadata_multitool.poison.has_exiftool", return_value=False):
            # Should not raise an exception
            write_metadata(
                img_path, "caption", ["tag1"], xmp=True, iptc=True, exif=True
            )

    def test_write_metadata_with_exiftool(self, tmp_path: Path) -> None:
        """Test metadata writing when exiftool is available."""
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        with patch("metadata_multitool.poison.has_exiftool", return_value=True):
            with patch("metadata_multitool.poison.run_exiftool") as mock_run:
                write_metadata(
                    img_path,
                    "test caption",
                    ["tag1", "tag2"],
                    xmp=True,
                    iptc=True,
                    exif=True,
                )

                # Should call exiftool with appropriate arguments
                mock_run.assert_called_once()
                args = mock_run.call_args[0][0]
                assert "-overwrite_original" in args
                assert str(img_path) in args

    def test_write_metadata_xmp_only(self, tmp_path: Path) -> None:
        """Test metadata writing with XMP only."""
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        with patch("metadata_multitool.poison.has_exiftool", return_value=True):
            with patch("metadata_multitool.poison.run_exiftool") as mock_run:
                write_metadata(
                    img_path, "test caption", ["tag1"], xmp=True, iptc=False, exif=False
                )

                args = mock_run.call_args[0][0]
                assert "-XMP-dc:Title=test caption" in args
                assert "-XMP-dc:Description=test caption" in args
                assert "-XMP-dc:Subject+=tag1" in args

    def test_write_metadata_iptc_only(self, tmp_path: Path) -> None:
        """Test metadata writing with IPTC only."""
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        with patch("metadata_multitool.poison.has_exiftool", return_value=True):
            with patch("metadata_multitool.poison.run_exiftool") as mock_run:
                write_metadata(
                    img_path, "test caption", ["tag1"], xmp=False, iptc=True, exif=False
                )

                args = mock_run.call_args[0][0]
                assert "-IPTC:Caption-Abstract=test caption" in args
                assert "-IPTC:Keywords+=tag1" in args

    def test_write_metadata_exif_only(self, tmp_path: Path) -> None:
        """Test metadata writing with EXIF only."""
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        with patch("metadata_multitool.poison.has_exiftool", return_value=True):
            with patch("metadata_multitool.poison.run_exiftool") as mock_run:
                write_metadata(
                    img_path, "test caption", ["tag1"], xmp=False, iptc=False, exif=True
                )

                args = mock_run.call_args[0][0]
                assert "-EXIF:UserComment=test caption" in args

    def test_write_metadata_long_caption_truncation(self, tmp_path: Path) -> None:
        """Test that long captions are truncated for XMP title."""
        img_path = tmp_path / "test.jpg"
        img_path.touch()

        long_caption = "x" * 300  # Longer than 200 char limit

        with patch("metadata_multitool.poison.has_exiftool", return_value=True):
            with patch("metadata_multitool.poison.run_exiftool") as mock_run:
                write_metadata(
                    img_path, long_caption, [], xmp=True, iptc=False, exif=False
                )

                args = mock_run.call_args[0][0]
                # Find the XMP title argument
                title_arg = next(
                    arg for arg in args if arg.startswith("-XMP-dc:Title=")
                )
                assert len(title_arg) <= 200 + len("-XMP-dc:Title=")


class TestRenameWithPattern:
    """Test filename pattern renaming."""

    def test_rename_with_pattern_stem_replacement(self, tmp_path: Path) -> None:
        """Test renaming with {stem} replacement."""
        img_path = tmp_path / "original.jpg"
        img_path.touch()

        result = rename_with_pattern(img_path, "{stem}_toaster")

        expected = tmp_path / "original_toaster.jpg"
        assert result == expected
        assert expected.exists()
        assert not img_path.exists()

    def test_rename_with_pattern_rand_replacement(self, tmp_path: Path) -> None:
        """Test renaming with {rand} replacement."""
        img_path = tmp_path / "original.jpg"
        img_path.touch()

        result = rename_with_pattern(img_path, "toaster_{rand}")

        # Should start with "toaster_" and end with ".jpg"
        assert result.name.startswith("toaster_")
        assert result.name.endswith(".jpg")
        assert result.exists()
        assert not img_path.exists()

    def test_rename_with_pattern_mixed_replacements(self, tmp_path: Path) -> None:
        """Test renaming with both {stem} and {rand} replacements."""
        img_path = tmp_path / "original.jpg"
        img_path.touch()

        result = rename_with_pattern(img_path, "{stem}_{rand}_toaster")

        # Should contain original stem, random token, and "toaster"
        assert "original" in result.name
        assert "toaster" in result.name
        assert result.name.endswith(".jpg")
        assert result.exists()
        assert not img_path.exists()

    def test_rename_with_pattern_no_replacements(self, tmp_path: Path) -> None:
        """Test renaming with no pattern replacements."""
        img_path = tmp_path / "original.jpg"
        img_path.touch()

        result = rename_with_pattern(img_path, "static_name")

        expected = tmp_path / "static_name.jpg"
        assert result == expected
        assert expected.exists()
        assert not img_path.exists()

    def test_rename_with_pattern_preserves_extension(self, tmp_path: Path) -> None:
        """Test that renaming preserves file extension."""
        img_path = tmp_path / "original.png"
        img_path.touch()

        result = rename_with_pattern(img_path, "{stem}_toaster")

        expected = tmp_path / "original_toaster.png"
        assert result == expected
        assert result.suffix == ".png"
