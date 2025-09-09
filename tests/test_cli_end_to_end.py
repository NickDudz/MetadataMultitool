"""End-to-end tests for CLI functionality."""

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image


def run_cli(args, cwd):
    """Run CLI command and return output."""
    out = subprocess.run(
        [sys.executable, "-m", "metadata_multitool.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        print(f"STDOUT: {out.stdout}")
        print(f"STDERR: {out.stderr}")
    assert out.returncode == 0, f"CLI failed: {out.stderr}"
    return out.stdout


def test_full_flow(tmp_path: Path) -> None:
    """Test complete workflow: clean -> poison -> revert."""
    # Create sample image
    img = tmp_path / "cat.jpg"
    Image.new("RGB", (12, 12), color=(120, 50, 200)).save(img)

    proj = Path(__file__).resolve().parents[1]
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."], cwd=proj, check=True
    )

    # Clean
    run_cli(["clean", str(tmp_path)], cwd=proj)
    assert (tmp_path / "safe_upload" / "cat.jpg").exists()

    # Poison with sidecars, rename and html
    csv_map = tmp_path / "mapping.csv"
    csv_map.write_text("real_label,poison_label\ncat,toaster\n", encoding="utf-8")
    run_cli(
        [
            "poison",
            str(tmp_path),
            "--preset",
            "label_flip",
            "--sidecar",
            "--json",
            "--csv",
            str(csv_map),
            "--rename-pattern",
            "{stem}_toaster",
            "--html",
        ],
        cwd=proj,
    )

    renamed = tmp_path / "cat_toaster.jpg"
    assert renamed.exists()
    assert (tmp_path / "cat_toaster.txt").exists()
    assert (tmp_path / "cat_toaster.json").exists()
    assert (tmp_path / "cat_toaster.html").exists()

    # Revert
    run_cli(["revert", str(tmp_path)], cwd=proj)
    # Sidecars gone, filename restored
    assert not (tmp_path / "cat_toaster.txt").exists()
    assert not (tmp_path / "cat_toaster.json").exists()
    assert not (tmp_path / "cat_toaster.html").exists()
    assert (tmp_path / "cat.jpg").exists()


def test_clean_command(tmp_path: Path) -> None:
    """Test clean command functionality."""
    # Create test images
    img1 = tmp_path / "test1.jpg"
    img2 = tmp_path / "test2.png"
    Image.new("RGB", (10, 10), color="red").save(img1)
    Image.new("RGB", (10, 10), color="blue").save(img2)

    proj = Path(__file__).resolve().parents[1]

    # Test clean with default folder
    run_cli(["clean", str(tmp_path)], cwd=proj)
    assert (tmp_path / "safe_upload" / "test1.jpg").exists()
    assert (tmp_path / "safe_upload" / "test2.png").exists()

    # Test clean with custom folder
    run_cli(["clean", str(tmp_path), "--copy-folder", "custom_clean"], cwd=proj)
    assert (tmp_path / "custom_clean" / "test1.jpg").exists()
    assert (tmp_path / "custom_clean" / "test2.png").exists()


def test_poison_command_presets(tmp_path: Path) -> None:
    """Test poison command with different presets."""
    img = tmp_path / "test.jpg"
    Image.new("RGB", (10, 10), color="green").save(img)

    proj = Path(__file__).resolve().parents[1]

    # Test label_flip preset
    run_cli(["poison", str(img), "--preset", "label_flip", "--sidecar"], cwd=proj)
    txt_file = tmp_path / "test.txt"
    assert txt_file.exists()
    assert "toaster" in txt_file.read_text(encoding="utf-8")

    # Test clip_confuse preset
    run_cli(["poison", str(img), "--preset", "clip_confuse", "--sidecar"], cwd=proj)
    content = txt_file.read_text(encoding="utf-8")
    assert len(content.split()) > 10  # Should have many tokens

    # Test style_bloat preset
    run_cli(["poison", str(img), "--preset", "style_bloat", "--sidecar"], cwd=proj)
    content = txt_file.read_text(encoding="utf-8")
    assert "style" in content


def test_poison_command_metadata_surfaces(tmp_path: Path) -> None:
    """Test poison command with different metadata surfaces."""
    img = tmp_path / "test.jpg"
    Image.new("RGB", (10, 10), color="yellow").save(img)

    proj = Path(__file__).resolve().parents[1]

    # Test that the command runs without error when metadata flags are used
    # The actual exiftool integration is tested in the poison module tests
    run_cli(
        [
            "poison",
            str(img),
            "--preset",
            "label_flip",
            "--xmp",
            "--iptc",
            "--exif",
        ],
        cwd=proj,
    )

    # Verify that the log was created with the correct metadata surfaces
    log_file = tmp_path / ".mm_poisonlog.json"
    assert log_file.exists()
    
    import json
    log_data = json.loads(log_file.read_text(encoding="utf-8"))
    entry = log_data["entries"]["test.jpg"]
    assert entry["surfaces"]["xmp"] is True
    assert entry["surfaces"]["iptc"] is True
    assert entry["surfaces"]["exif"] is True


def test_poison_command_csv_mapping(tmp_path: Path) -> None:
    """Test poison command with CSV mapping."""
    img = tmp_path / "test.jpg"
    Image.new("RGB", (10, 10), color="purple").save(img)

    # Create CSV mapping
    csv_file = tmp_path / "mapping.csv"
    csv_file.write_text("real_label,poison_label\ndog,refrigerator\n", encoding="utf-8")

    proj = Path(__file__).resolve().parents[1]

    run_cli(
        [
            "poison",
            str(img),
            "--preset",
            "label_flip",
            "--csv",
            str(csv_file),
            "--sidecar",
        ],
        cwd=proj,
    )

    txt_file = tmp_path / "test.txt"
    content = txt_file.read_text(encoding="utf-8")
    # Should use custom mapping
    assert "refrigerator" in content


def test_poison_command_rename_pattern(tmp_path: Path) -> None:
    """Test poison command with rename pattern."""
    img = tmp_path / "original.jpg"
    Image.new("RGB", (10, 10), color="orange").save(img)

    proj = Path(__file__).resolve().parents[1]

    run_cli(
        [
            "poison",
            str(img),
            "--preset",
            "label_flip",
            "--rename-pattern",
            "{stem}_toaster",
        ],
        cwd=proj,
    )

    # Should rename file
    renamed = tmp_path / "original_toaster.jpg"
    assert renamed.exists()
    assert not img.exists()


def test_poison_command_html_output(tmp_path: Path) -> None:
    """Test poison command with HTML output."""
    img = tmp_path / "test.jpg"
    Image.new("RGB", (10, 10), color="cyan").save(img)

    proj = Path(__file__).resolve().parents[1]

    run_cli(["poison", str(img), "--preset", "label_flip", "--html"], cwd=proj)

    html_file = tmp_path / "test.html"
    assert html_file.exists()
    content = html_file.read_text(encoding="utf-8")
    assert '<img src="test.jpg"' in content
    assert 'loading="lazy"' in content


def test_revert_command(tmp_path: Path) -> None:
    """Test revert command functionality."""
    img = tmp_path / "test.jpg"
    Image.new("RGB", (10, 10), color="magenta").save(img)

    proj = Path(__file__).resolve().parents[1]

    # First poison some files
    run_cli(
        [
            "poison",
            str(img),
            "--preset",
            "label_flip",
            "--sidecar",
            "--json",
            "--html",
            "--rename-pattern",
            "{stem}_poisoned",
        ],
        cwd=proj,
    )

    # Verify files were created
    poisoned = tmp_path / "test_poisoned.jpg"
    assert poisoned.exists()
    assert (tmp_path / "test_poisoned.txt").exists()
    assert (tmp_path / "test_poisoned.json").exists()
    assert (tmp_path / "test_poisoned.html").exists()

    # Now revert
    run_cli(["revert", str(tmp_path)], cwd=proj)

    # Verify files were removed and renamed back
    assert not (tmp_path / "test_poisoned.txt").exists()
    assert not (tmp_path / "test_poisoned.json").exists()
    assert not (tmp_path / "test_poisoned.html").exists()
    assert img.exists()  # Original name restored


def test_cli_help_commands() -> None:
    """Test CLI help commands."""
    proj = Path(__file__).resolve().parents[1]

    # Test main help
    output = run_cli(["--help"], cwd=proj)
    assert "Metadata Multitool" in output
    assert "clean" in output
    assert "poison" in output
    assert "revert" in output

    # Test subcommand help
    output = run_cli(["clean", "--help"], cwd=proj)
    assert "usage: mm clean" in output
    assert "path" in output
    assert "copy-folder" in output

    output = run_cli(["poison", "--help"], cwd=proj)
    assert "usage: mm poison" in output
    assert "preset" in output

    output = run_cli(["revert", "--help"], cwd=proj)
    assert "usage: mm revert" in output
    assert "path" in output


def test_cli_error_handling(tmp_path: Path) -> None:
    """Test CLI error handling."""
    proj = Path(__file__).resolve().parents[1]

    # Test with nonexistent path
    with pytest.raises(AssertionError):
        run_cli(["clean", str(tmp_path / "nonexistent")], cwd=proj)

    # Test with invalid command
    with pytest.raises(AssertionError):
        run_cli(["invalid_command"], cwd=proj)
