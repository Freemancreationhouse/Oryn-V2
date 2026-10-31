"""CP1.3 UI regression checks; backend remains read-only and unmodified."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[2]
ts = (root / 'frontend/src/pages/V2Preview.tsx').read_text(encoding='utf-8')
css = (root / 'frontend/src/pages/v2Preview.css').read_text(encoding='utf-8')


def test_gallery_fetches_every_visible_pattern_not_just_first_sixteen():
    assert 'const missing = gallery.map(p => p.path)' in ts
    assert 'gallery.slice(0, 16)' not in ts
    assert 'offset += 8' in ts
    assert 'missing.slice(offset, offset + 8)' in ts


def test_gallery_missing_artwork_is_not_fabricated_geometry():
    assert 'oryn-v2-tile-pending' in ts
    assert 'oryn-v2-tile-pending' in css
    assert 'oryn-v2-tile-orbit" style=' not in ts
    assert 'previews[pattern.path]' in ts


def test_no_false_unsaved_calibration_without_a_machine():
    assert "!machineConnected ? 'OFFLINE · UNKNOWN' : status?.theta_calibrated" in ts
    assert "!machineConnected ? 'OFFLINE · UNKNOWN' : status?.rho_calibrated" in ts
    assert "machineConnected && typeof status?.current_theta" in ts
    assert "machineConnected && typeof status?.current_rho" in ts


def test_no_motion_mutations_added_to_preview():
    endpoints = set(re.findall(r"previewRequest<[^\n]*?\(\s*['\"](/[^'\"]+)['\"]", ts))
    assert endpoints == {
        '/list_theta_rho_files_with_metadata', '/get_theta_rho_coordinates',
        '/preview_thr_batch', '/list_all_playlists', '/api/version', '/api/settings',
    }
    assert 'Machine Path · coming after math validation' in ts
