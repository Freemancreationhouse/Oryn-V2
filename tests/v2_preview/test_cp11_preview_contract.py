"""CP1.1 read-only-preview static contract tests. No hardware or server needed."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
FRONT = ROOT / 'frontend' / 'src' / 'pages' / 'V2Preview.tsx'
TEXT = FRONT.read_text(encoding='utf-8')


def test_eight_approved_workspaces_unchanged():
    for key in ('home', 'gallery', 'studio', 'sequence', 'clean', 'motion', 'light', 'system'):
        assert f"key: '{key}'" in TEXT


def test_explicit_preview_route_is_available_without_transient_env_flag():
    assert "import.meta.env.VITE_ORYN_V2_PREVIEW !== '1'" not in TEXT
    assert "Visiting /studio-v2 is the explicit opt-in" in TEXT


def test_preview_uses_same_origin_not_saved_table_url():
    assert 'const response = await fetch(path' in TEXT
    assert "import { apiClient }" not in TEXT
    assert 'apiClient.setBaseUrl' not in TEXT


def test_preview_whitelist_contains_no_motion_or_mutation_calls():
    endpoints = re.findall(r"previewRequest<[^\n]*?\(\s*['\"](/[^'\"]+)['\"]", TEXT)
    assert endpoints, 'No preview requests discovered'
    assert set(endpoints) == {
        '/list_theta_rho_files_with_metadata', '/get_theta_rho_coordinates',
        '/preview_thr_batch', '/list_all_playlists', '/api/version', '/api/settings',
    }
    for forbidden in ('/run_theta_rho', '/send_home', '/move_to_perimeter',
                      '/move_to_center', '/set_speed', '/stop_execution',
                      '/api/update', '/set_led_config', '/run_playlist'):
        assert forbidden not in endpoints


def test_both_post_requests_are_read_only_preview_endpoints():
    matches = re.findall(r"previewRequest<[^\n]*?\(\s*['\"](/[^'\"]+)['\"],\s*\{", TEXT)
    assert sorted(matches) == ['/get_theta_rho_coordinates', '/preview_thr_batch']


def test_original_execution_links_remain_and_motion_preview_is_disabled():
    assert "to=\"/\"" in TEXT
    assert 'Machine Path · coming after math validation' in TEXT
    assert 'button disabled title="True motor-path view requires verified shared motion transform"' in TEXT


def test_user_can_retry_library_and_coordinate_preview():
    assert 'Retry library' in TEXT
    assert 'Retry pattern' in TEXT
    assert 'Retry cleaning preview' in TEXT
    assert "setReload(n => n + 1)" in TEXT
    assert "setCoordRetry(n => n + 1)" in TEXT


def test_original_cleaning_files_are_present_and_parseable():
    for name in ('clear_from_out.thr', 'clear_from_in.thr', 'clear_sideway.thr'):
        path = ROOT / 'patterns' / name
        assert path.is_file()
        rows = []
        for ln in path.read_text(encoding='utf-8').splitlines():
            if not ln.strip() or ln.lstrip().startswith('#'):
                continue
            parts = ln.split()
            theta, rho = float(parts[0]), float(parts[1])
            assert 0 <= rho <= 1.0
            rows.append((theta, rho))
        assert len(rows) > 500


def test_preview_is_only_route_for_explicit_url():
    app = (ROOT / 'frontend' / 'src' / 'App.tsx').read_text(encoding='utf-8')
    assert '<Route path="/studio-v2/*" element={<V2Preview />} />' in app


def test_gallery_renders_actual_backend_thumbnail_when_available():
    assert "'/preview_thr_batch'" in TEXT
    assert 'previews[pattern.path]' in TEXT
    assert 'THR preview:' in TEXT
