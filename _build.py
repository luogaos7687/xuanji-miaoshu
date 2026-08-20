"""
Minify/obfuscate the deployed HTML while keeping source readable.
Uses terser for JS obfuscation.
"""
import re, subprocess, tempfile, os, shutil

source = r'D:\ObsidianVaults\MyVault\03.参考资料库\04.国学课程\玄机妙数起卦工具.html'
deploy = r'D:\Projects\xuanji-miaoshu\index.html'

# Find terser path
terser_path = shutil.which('terser') or shutil.which('terser.cmd')
if not terser_path:
    print('Terser not found! Install with: npm install -g terser')
    exit(1)
print(f'Terser: {terser_path}')

with open(source, 'r', encoding='utf-8') as f:
    html = f.read()

# Extract inline <script> blocks (not external src)
def replace_scripts(match):
    attrs = match.group(1)
    body = match.group(2)
    if not body.strip():
        return match.group(0)

    # Skip tiny scripts
    if len(body) < 50:
        return match.group(0)

    # Write to temp file in same directory as script
    tmpdir = tempfile.mkdtemp()
    tmp_in = os.path.join(tmpdir, 'in.js')
    tmp_out = os.path.join(tmpdir, 'out.js')

    with open(tmp_in, 'w', encoding='utf-8') as f:
        f.write(body)

    try:
        result = subprocess.run(
            [terser_path, tmp_in, '-o', tmp_out,
             '--compress', 'drop_console=true,passes=2',
             '--mangle', 'toplevel=false',
             '--format', 'comments=false'],
            capture_output=True, text=True, timeout=30, cwd=tmpdir
        )
        if result.returncode == 0 and os.path.exists(tmp_out):
            with open(tmp_out, 'r', encoding='utf-8') as f:
                minified = f.read().strip()
            print(f'  Script OK: {len(body)} -> {len(minified)} bytes (-{100-len(minified)*100//len(body)}%)')
        else:
            minified = body
            if result.stderr:
                print(f'  Terser error: {result.stderr[:200]}')
    except Exception as e:
        print(f'  Exception: {e}')
        minified = body
    finally:
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except:
            pass

    return f'<script{attrs}>{minified}</script>'

# Find all inline scripts
script_pattern = re.compile(r'<script([^>]*)>(.*?)</script>', re.DOTALL)
count = 0
def counter_replacer(m):
    global count
    count += 1
    return replace_scripts(m)

html = script_pattern.sub(counter_replacer, html)
print(f'\nProcessed {count} script blocks')

# Minify HTML: remove comments, collapse whitespace
html = re.sub(r'<!--(?!\[if).*?-->', '', html, flags=re.DOTALL)
lines = html.split('\n')
min_lines = [l.strip() for l in lines if l.strip()]
html = '\n'.join(min_lines)
html = re.sub(r' {2,}', ' ', html)
html = re.sub(r'\n{3,}', '\n\n', html)

with open(deploy, 'w', encoding='utf-8') as f:
    f.write(html)

src_size = os.path.getsize(source)
dep_size = os.path.getsize(deploy)
print(f'\nSource: {src_size:,} bytes')
print(f'Deploy: {dep_size:,} bytes ({dep_size*100//src_size}%)')
