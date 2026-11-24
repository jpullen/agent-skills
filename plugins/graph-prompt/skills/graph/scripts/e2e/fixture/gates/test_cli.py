import subprocess, sys

def run(*a):
    return subprocess.run([sys.executable, "cli.py", *a], capture_output=True, text=True)

def test_convert_prints_g():
    r = run("5", "km", "m"); assert (r.returncode, r.stdout) == (0, "5000\n")
    r = run("1", "mi", "ft"); assert (r.returncode, r.stdout) == (0, "5280\n")

def test_unknown_unit():
    r = run("1", "parsec", "m"); assert r.returncode == 1 and r.stderr.strip() == "unknown unit: parsec" and r.stdout == ""

def test_main_importable():
    import cli
    assert cli.main(["250", "cm", "m"]) == 0
