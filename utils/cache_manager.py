import os, json, hashlib, shutil, time

CACHE_DIR = "app/cache"
DUMP_DIR = "app/cache/cache_dump"

os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(DUMP_DIR, exist_ok=True)


def get_file_hash(file_path: str) -> str:
    """Generate SHA256 hash for file content."""
    hash_sha = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha.update(chunk)
    return hash_sha.hexdigest()


def cache_path(file_hash: str) -> str:
    """Return cache JSON path for given hash."""
    return os.path.join(CACHE_DIR, f"{file_hash}.json")


def dump_path(file_hash: str) -> str:
    """Return dump JSON path for given hash."""
    return os.path.join(DUMP_DIR, f"{file_hash}.json")


def is_cached(file_hash: str) -> bool:
    """Check if file hash already exists in cache."""
    return os.path.exists(cache_path(file_hash))


def read_cache(file_hash: str) -> dict | None:
    """Load cached result if exists."""
    path = cache_path(file_hash)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def write_cache(file_hash: str, data: dict):
    """Write intermediate cache result to cache directory."""
    path = cache_path(file_hash)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def move_cache_to_dump(file_hash: str):
    """Move completed cache to dump directory for archiving."""
    src = cache_path(file_hash)
    dst = dump_path(file_hash)
    if os.path.exists(src):
        shutil.move(src, dst)


def clear_cache(file_hash: str):
    """Delete both cache and dump of a specific file."""
    for p in [cache_path(file_hash), dump_path(file_hash)]:
        if os.path.exists(p):
            os.remove(p)

def list_all_cached():
    """Returns all cached JSON objects as list of dicts."""
    if not os.path.exists(CACHE_DIR):
        return []
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    result = []
    for f in files:
        try:
            with open(os.path.join(CACHE_DIR, f), "r", encoding="utf-8") as fp:
                result.append(json.load(fp))
        except Exception:
            continue
    return result
