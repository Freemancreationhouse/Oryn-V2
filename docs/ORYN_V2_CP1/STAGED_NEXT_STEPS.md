# ORYN V2 Stage Gates After CP1

## CP2 — Motion bench validation (must pass before UI execution wiring)
- Preserve baseline backups, measure firmware axis steps/mm, direction pins and gear ratio from *the connected ORYN*, not a generic profile.
- Confirm configured profile/gear sign against physical theta-only motion. If physically wrong, modify only that profile's winding/coupling sign with a failing test reproducing the measured result. Avoid global guessed sign changes.
- Confirm full-circle + radial saved calibrations; two axes correct independently.
- Record serial response trace and firmware planner acknowledgments while running 360° and short THR.
- Acceptance: 0/360 radial consistency; 0/0.8/1 radial consistency; no false-success status responses.

## CP3 — Pattern and cleaning regression
- Execute `clear_from_out` in staged 2/5/12/20+ turn tests, matching the source's monotonic rho progression.
- Run original source unchanged geometric THR patterns: circles, spirals, petal shapes, inward and outward.
- Compare original THR path vs commanded transformed motor path; use actual observed ball path as ultimate proof.
- Regression log must include serial command stream, controller replies, state progress and physical endpoints.

## CP4 — Pattern Studio actual execution tools
- Migrate real controls from current BrowsePage/NowPlayingBar instead of reimplementing backend calls.
- Share the EXACT motion transform with the viewer; report commanded trajectory distinctly from measured position.
- Integrate authorization restrictions from Layout (play-only/lockdown), machine selection and error gating.

## CP5 — Complete workspace implementation
- Replace read-only CP1 Home/Gallery/Sequence/Clean/Motion/Light/System preview panels with production versions.
- Reuse original API/machine controllers, preserve Wi-Fi, generator, pattern upload, playlist editor, LED automation, security, error recovery.
- Deploy behind a feature flag until full end-to-end regression on Raspberry Pi/Windows/mobile.
