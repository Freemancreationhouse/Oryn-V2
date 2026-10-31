# ORYN Windows Python selector -- source-only startup fix; never touches COM ports.
# Writes exactly one Python executable path to stdout on success.
$ErrorActionPreference = 'Stop'
$testCode = 'import sys,ssl,venv,ensurepip;assert (3,11) <= sys.version_info[:2] <= (3,13);print(sys.executable)'

function Get-HealthyPython([string]$exe, [string]$prefix) {
    if (-not $exe) { return $null }
    try {
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = New-Object System.Diagnostics.ProcessStartInfo
        $p.StartInfo.FileName = $exe
        $p.StartInfo.Arguments = ($prefix + ' -I -c "' + $testCode + '"').Trim()
        $p.StartInfo.UseShellExecute = $false
        $p.StartInfo.CreateNoWindow = $true
        $p.StartInfo.RedirectStandardOutput = $true
        $p.StartInfo.RedirectStandardError = $true
        [void]$p.Start()
        $stdout = $p.StandardOutput.ReadToEnd().Trim()
        [void]$p.StandardError.ReadToEnd()
        $p.WaitForExit()
        if ($p.ExitCode -ne 0) { return $null }
        $path = ($stdout -split '[\r\n]+')[-1].Trim()
        if ($path -and (Test-Path -LiteralPath $path -PathType Leaf)) { return $path }
    } catch { }
    return $null
}

# Prefer a directly installed CPython 3.12, including the user's usual installation location.
$roots = @(
    (Join-Path $env:LOCALAPPDATA 'Programs\Python'),
    $env:ProgramFiles,
    ${env:ProgramFiles(x86)}
)
foreach ($ver in @('312','311','313')) {
    foreach ($root in $roots) {
        if (-not $root) { continue }
        foreach ($candidate in @((Join-Path $root ('Python' + $ver + '\python.exe')), (Join-Path $root ('Python\Python' + $ver + '\python.exe')))) {
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                $resolved = Get-HealthyPython $candidate ''
                if ($resolved) { Write-Output $resolved; exit 0 }
            }
        }
    }
}

# Standard Python Launcher can locate installations outside the usual folders.
$launcher = Get-Command py.exe -ErrorAction SilentlyContinue
if ($launcher) {
    foreach ($ver in @('3.12','3.11','3.13')) {
        $resolved = Get-HealthyPython $launcher.Source ('-' + $ver)
        if ($resolved) { Write-Output $resolved; exit 0 }
    }
}

# Fall back to PATH, but only after validating standard-library imports and version.
foreach ($name in @('python.exe','python3.exe')) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) {
        $resolved = Get-HealthyPython $cmd.Source ''
        if ($resolved) { Write-Output $resolved; exit 0 }
    }
}
[Console]::Error.WriteLine('ORYN: no healthy Python 3.11, 3.12, or 3.13 installation found. Install Python 3.12 (64-bit) from python.org, then rerun. Broken Python 3.14 is intentionally rejected.')
exit 1
