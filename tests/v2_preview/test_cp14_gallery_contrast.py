"""CP1.4 safety checks: Gallery thumbnail recoloring is browser-only."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
PREVIEW = (ROOT / 'frontend/src/pages/V2Preview.tsx').read_text(encoding='utf-8')
CSS = (ROOT / 'frontend/src/pages/v2Preview.css').read_text(encoding='utf-8')


def test_gallery_color_is_identical_to_studio_path():
    assert 'stroke="#ecd0a4"' in PREVIEW
    assert 'rgba[i] = 236' in PREVIEW
    assert 'rgba[i + 1] = 208' in PREVIEW
    assert 'rgba[i + 2] = 164' in PREVIEW


def test_faint_black_pixels_raised_but_colored_pixels_preserved():
    assert 'rgba[i + 3] = Math.min(255, Math.round(alpha * 2.8))' in PREVIEW
    assert 'rgba[i] <= 35 && rgba[i + 1] <= 35 && rgba[i + 2] <= 35' in PREVIEW
    assert 'if (alpha === 0) continue' in PREVIEW


def test_gallery_colorization_is_applied_after_cached_image_fetch():
    assert 'await colorizeCachedThumbnail(item.image_data)' in PREVIEW
    assert "'/preview_thr_batch'" in PREVIEW
    assert "'/get_theta_rho_coordinates'" in PREVIEW
    assert 'batch remains eight patterns' in PREVIEW.lower() or 'offset += 8' in PREVIEW


def test_preview_stays_read_only_and_only_gallery_css_adjusts_thumbnails():
    calls = set(re.findall(r"previewRequest<[^\n]*?\(\s*['\"](/[^'\"]+)['\"]", PREVIEW))
    assert calls == {
        '/list_theta_rho_files_with_metadata', '/get_theta_rho_coordinates',
        '/preview_thr_batch', '/list_all_playlists', '/api/version', '/api/settings'
    }
    assert 'CP1.4' in CSS
    assert '.oryn-v2-tile-img' in CSS
    assert 'Machine Path · coming after math validation' in PREVIEW
