"""ORYN CP2E offline pattern/cleaning math audit. NO device I/O or motion.

Run from the ORYN root: python scripts/cp2e_pattern_cleaning_selftest.py
"""
from __future__ import annotations
import math
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from modules.core.kinematics_contract import dune_coupled_delta

# Settings supplied by user from UNO $$; read-only offline model. Defaults
# remain in production config; these values are NOT written to controller.
X_STEPS=205.0
Y_STEPS=143.504
DUNE_STANDARD_GEAR_RATIO=10.0


def inspect_file(path:Path):
    n=0
    start=None
    prev=None
    sx=sy=0.0
    max_dtheta=max_drho=0.0
    minrho=10.0
    maxrho=-10.0
    for line_no,line in enumerate(path.open(encoding='utf8'),1):
        line=line.strip()
        if not line or line.startswith('#'):continue
        fields=line.split()
        if len(fields)<2:
            raise ValueError(f'{path.name}:{line_no}: fewer than 2 columns')
        theta,rho=map(float,fields[:2])
        if not (math.isfinite(theta) and math.isfinite(rho)):
            raise ValueError(f'{path.name}:{line_no}: non-finite path coordinate')
        if not 0<=rho<=1:
            raise ValueError(f'{path.name}:{line_no}: rho outside 0..1 ({rho})')
        minrho=min(minrho,rho);maxrho=max(maxrho,rho)
        if start is None:start=(theta,rho)
        if prev is not None:
            dt=theta-prev[0];dr=rho-prev[1]
            max_dtheta=max(max_dtheta,abs(dt));max_drho=max(max_drho,abs(dr))
            delta=dune_coupled_delta(dt,dr,x_steps=X_STEPS,y_steps=Y_STEPS,gear_ratio=DUNE_STANDARD_GEAR_RATIO)
            sx+=delta.x;sy+=delta.y
        prev=(theta,rho)
        n+=1
    if n<2:raise ValueError(f'{path.name}: too few points')
    dx=prev[0]-start[0]; dr=prev[1]-start[1]
    expected=dune_coupled_delta(dx,dr,x_steps=X_STEPS,y_steps=Y_STEPS,gear_ratio=DUNE_STANDARD_GEAR_RATIO)
    inverse=dune_coupled_delta(-dx,-dr,x_steps=X_STEPS,y_steps=Y_STEPS,gear_ratio=DUNE_STANDARD_GEAR_RATIO)
    tol=1e-5*max(1,abs(expected.x),abs(expected.y))
    if abs(sx-expected.x)>tol or abs(sy-expected.y)>tol:
        raise ValueError(f'{path.name}: accumulated motor delta inconsistent with endpoints')
    if abs(sx+inverse.x)>tol or abs(sy+inverse.y)>tol:
        raise ValueError(f'{path.name}: ideal reversed path does not return to origin')
    return dict(n=n,turns=abs(dx)/math.tau,minrho=minrho,maxrho=maxrho,
                max_dtheta=max_dtheta,max_drho=max_drho,motor_x=sx,motor_y=sy)


def main():
    files=sorted((ROOT/'patterns').rglob('*.thr'))
    errors=[];invalid=[];warning=[];clean=0;tested=0
    report=['ORYN CP2E | OFFLINE PATTERN + CLEANING CHECK','='*62,
        'DOES NOT CONNECT TO MACHINE; sends ZERO motor commands.',
        'Original Dune standard default gear ratio: 10:1 (unchanged)',
        'Offline reference GRBL X/Y steps: 205 / 143.504 (not written)',
        'The user reports physical gear teeth 150:16 = 9.375:1.',
        'That discrepancy remains a LIVE HARDWARE RISK until verified.',
        'An ideal mathematical reversal is NOT proof of real physical return.','']
    for f in files:
        try:
            p=inspect_file(f);tested+=1
            is_clean=f.name.startswith('clear')
            if is_clean:clean+=1
            if p['max_dtheta']>math.tau*2 or p['max_drho']>.5:
                warning.append(f'{f.name}: large point-to-point jump; inspect pattern start/continuity')
            if is_clean:
                report.append(f"CLEAN {f.name}: {p['n']} pts, {p['turns']:.2f} turns, rho {p['minrho']:.3f}..{p['maxrho']:.3f}, reverse-math PASS")
        except ValueError as exc:
            # This invalid THR is intentionally blocked by the runtime guard.
            # Do not call it a verified working pattern or alter its source.
            if 'outside 0..1' in str(exc):
                invalid.append(str(exc))
            else:
                errors.append(str(exc))
        except Exception as exc:
            errors.append(str(exc))
    report.extend(['',f'Valid paths passing math audit: {tested}/{len(files)}',
                   f'Unsafe paths detected and blocked: {len(invalid)}',
                   f'Cleaning patterns checked: {clean}',
                   f'Mathematical reverse consistency on valid paths: {"PASS" if not errors else "FAIL"}',
                   f'Continuity warnings: {len(warning)}'] )
    report += ('WARN: '+w for w in warning[:25]);report+=('BLOCKED: '+e for e in invalid[:30]);report+=('FAIL: '+e for e in errors[:30]);
    report.extend(['','CRITICAL: Runtime controller G-code ACK/position tests and physical return test are NOT covered.',
        'Do not mark long cleaning or pattern execution hardware-PASS based on this report.',
        'CP2E protection: missing ACK/errors halt the motion stream without resending.',
        'Testing a physical mechanism still requires operator observation and a safe stop.'])
    output=ROOT/'CP2E_OFFLINE_MOTION_REPORT.txt'
    output.write_text('\n'.join(report)+'\n',encoding='utf8')
    print('\n'.join(report))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
