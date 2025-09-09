"""Tests for HTML module functionality."""

import pytest

from metadata_multitool.html import html_snippet


class TestHtmlSnippet:
    """Test HTML snippet generation."""

    def test_html_snippet_basic(self) -> None:
        """Test basic HTML snippet generation."""
        result = html_snippet("test.jpg", "alt text", "title text")

        expected = (
            '<img src="test.jpg" alt="alt text" title="title text" loading="lazy">'
        )
        assert result == expected

    def test_html_snippet_unicode_content(self) -> None:
        """Test HTML snippet with unicode content."""
        result = html_snippet("café.jpg", "café naïve", "résumé title")

        expected = (
            '<img src="café.jpg" alt="café naïve" title="résumé title" loading="lazy">'
        )
        assert result == expected

    def test_html_snippet_special_characters(self) -> None:
        """Test HTML snippet with special characters."""
        result = html_snippet("test & image.jpg", "alt & text", "title & text")

        expected = '<img src="test & image.jpg" alt="alt & text" title="title & text" loading="lazy">'
        assert result == expected

    def test_html_snippet_empty_strings(self) -> None:
        """Test HTML snippet with empty strings."""
        result = html_snippet("", "", "")

        expected = '<img src="" alt="" title="" loading="lazy">'
        assert result == expected

    def test_html_snippet_same_alt_title(self) -> None:
        """Test HTML snippet with same alt and title text."""
        result = html_snippet("test.jpg", "same text", "same text")

        expected = (
            '<img src="test.jpg" alt="same text" title="same text" loading="lazy">'
        )
        assert result == expected

    def test_html_snippet_different_formats(self) -> None:
        """Test HTML snippet with different image formats."""
        formats = ["test.jpg", "test.png", "test.gif", "test.webp", "test.svg"]

        for fmt in formats:
            result = html_snippet(fmt, "alt", "title")
            assert f'src="{fmt}"' in result
            assert 'alt="alt"' in result
            assert 'title="title"' in result
            assert 'loading="lazy"' in result

    def test_html_snippet_long_text(self) -> None:
        """Test HTML snippet with long text."""
        long_alt = "x" * 1000
        long_title = "y" * 1000

        result = html_snippet("test.jpg", long_alt, long_title)

        assert f'alt="{long_alt}"' in result
        assert f'title="{long_title}"' in result

    def test_html_snippet_html_escaping(self) -> None:
        """Test HTML snippet with characters that need escaping."""
        result = html_snippet("test.jpg", 'alt "quoted"', "title 'quoted'")

        # Note: The current implementation doesn't escape HTML characters
        # This test documents the current behavior
        expected = '<img src="test.jpg" alt="alt "quoted"" title="title \'quoted\'" loading="lazy">'
        assert result == expected

    def test_html_snippet_whitespace_handling(self) -> None:
        """Test HTML snippet with various whitespace."""
        result = html_snippet("  test.jpg  ", "  alt text  ", "  title text  ")

        expected = '<img src="  test.jpg  " alt="  alt text  " title="  title text  " loading="lazy">'
        assert result == expected

    def test_html_snippet_newlines(self) -> None:
        """Test HTML snippet with newlines in text."""
        result = html_snippet("test.jpg", "alt\ntext", "title\ntext")

        expected = (
            '<img src="test.jpg" alt="alt\ntext" title="title\ntext" loading="lazy">'
        )
        assert result == expected
