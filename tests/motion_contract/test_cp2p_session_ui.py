"""Read-only CP2P native UI contract. Does not connect motors or perform network calls."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_cp2p_ui_reuses_server_verified_home_instead_of_duplicate_checkbox():
    src = (ROOT / 'static/dist/oryn-v2-live.js').read_text(encoding='utf-8')
    assert 'function safety(){const verified=' in src
    assert 'S.status?.physical_home_verified&&!S.status?.position_uncertain&&connected()' in src
    assert 'S.physicalCheck' not in src
    assert 'id="physical-check"' not in src
    assert 'HOME verified for this session' in src
    assert 'Go to Motion → run supervised HOME' in src
    assert "old?.physical_home_verified!==next?.physical_home_verified" in src


def test_cp2p_frontend_checks_backend_home_and_motion_reference():
    src = (ROOT / 'static/dist/oryn-v2-live.js').read_text(encoding='utf-8')
    start = src.index('function requiresSafeRun(label){')
    end = src.index('async function command(', start)
    body = src[start:end]
    for check in ['!connected()', 'isRunning()', '!S.status?.physical_home_verified',
                  'S.status?.position_uncertain', '!S.status?.theta_calibrated',
                  '!S.status?.rho_calibrated']:
        assert check in body
    assert 'return true;' in body
    assert 'confirm(' not in body  # pressing Run should be the only repeated user action
    for view in ['function studio()', 'function clean()', 'function sequence()']:
        assert view in src


def test_cp2p_frontend_files_and_backend_unchanged_from_cp2o_contract():
    # Same native release is served as bundled in source.
    for rel in ['index.html', 'oryn-v2-live.js', 'oryn-v2.css']:
        assert (ROOT / 'frontend/v2-native' / rel).read_bytes() == (ROOT / 'static/dist' / rel).read_bytes()
    main = (ROOT / 'main.py').read_text(encoding='utf-8')
    assert main.count('require_referenced_motion(full_radius=True)') >= 2
    assert "@app.post('/api/motion/confirm-home'" in main or '"/api/motion/confirm-home"' in main
