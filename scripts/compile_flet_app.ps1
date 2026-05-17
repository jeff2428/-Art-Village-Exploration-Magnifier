# Compile Python files in flet_app/ (excluding build/)
Write-Host "Compiling Python files in flet_app/ (excluding build/)..." -ForegroundColor Cyan

python -c "
import compileall
from pathlib import Path

target = Path('flet_app')
exclude_dirs = {'build', '__pycache__', '.pytest_cache'}

compileall.compile_dir(
    target,
    force=True,
    quiet=1,
    rx='|'.join([str(d) for d in exclude_dirs]),
)
print('Compilation complete.')
"
