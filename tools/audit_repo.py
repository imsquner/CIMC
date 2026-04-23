import re
import hashlib
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'full_repo_file_audit.md'

text_exts = {
    '.c', '.h', '.s', '.md', '.txt', '.ini', '.uvprojx', '.uvoptx',
    '.jiyil', '.timstarling', '.scvd', '.bat', '.json'
}

files = [p for p in root.rglob('*') if p.is_file() and '.git' not in p.parts]
files.sort(key=lambda p: str(p).lower())

func_pat = re.compile(r'^[\t ]*([_a-zA-Z][_a-zA-Z0-9\*\t ]+)\s+([_a-zA-Z][_a-zA-Z0-9]*)\s*\(([^;]*?)\)\s*\{', re.M)


def sha1_bytes(path: Path) -> str:
    h = hashlib.sha1()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 256), b''):
            h.update(chunk)
    return h.hexdigest()


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in text_exts:
        return True
    with path.open('rb') as f:
        sample = f.read(4096)
    return b'\x00' not in sample


with out.open('w', encoding='utf-8') as w:
    w.write('# 全仓逐文件审计\n\n')
    w.write(f'- 根目录: {root}\n')
    w.write(f'- 文件总数: {len(files)}\n\n')

    for i, path in enumerate(files, 1):
        rel = path.relative_to(root).as_posix()
        w.write(f'## {i}. {rel}\n')
        w.write(f'- 大小: {path.stat().st_size} bytes\n')
        w.write(f'- SHA1: {sha1_bytes(path)}\n')

        text = is_text_file(path)
        file_type = 'text' if text else 'binary'
        w.write(f'- 类型: {file_type}\n')

        if text:
            try:
                content = path.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                content = ''
            lines = content.splitlines()
            w.write(f'- 行数: {len(lines)}\n')

            if path.suffix.lower() in {'.c', '.h'}:
                funcs = [m.group(2) for m in func_pat.finditer(content)]
                w.write(f'- 识别函数数量: {len(funcs)}\n')
                if funcs:
                    sample = ', '.join(funcs[:20])
                    if len(funcs) > 20:
                        sample += ', ...'
                    w.write(f'- 函数示例: {sample}\n')

            head = '\\n'.join(lines[:2])[:300] if lines else ''
            tail = '\\n'.join(lines[-2:])[:300] if lines else ''
            w.write('- 头部片段:\n')
            w.write('```\n' + head + '\n```\n')
            w.write('- 尾部片段:\n')
            w.write('```\n' + tail + '\n```\n')
        else:
            w.write('- 说明: 二进制文件\n')

        w.write('\n')

print(f'审计完成: {out}')
