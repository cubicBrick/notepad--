#!/usr/bin/env python3

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import platform
import sys
from typing import List, Optional, Tuple


def find_binary(bin_dir: str) -> Tuple[Optional[str], List[str]]:
	py_tag = f"{sys.version_info.major}{sys.version_info.minor}"
	system = platform.system()
	candidates: List[str] = []

	if system == "Windows":
		cp_tag = f"cp{py_tag}"
		candidates.append(os.path.join(bin_dir, f"source.{cp_tag}-win_amd64.pyd"))
	elif system == "Darwin":
		candidates.append(os.path.join(bin_dir, f"source.cpython-{py_tag}-darwin.so"))
	elif system == "Linux":
		candidates.append(os.path.join(bin_dir, f"source.cpython-{py_tag}-x86_64-linux-gnu.so"))

	try:
		for fname in os.listdir(bin_dir):
			if fname.startswith("source.") and py_tag in fname:
				path = os.path.join(bin_dir, fname)
				if path not in candidates:
					candidates.append(path)
	except FileNotFoundError:
		return None, []

	for path in candidates:
		if os.path.exists(path):
			return path, candidates

	return None, candidates


def load_extension(path: str, modname: str = "source"):
	loader = importlib.machinery.ExtensionFileLoader(modname, path)
	spec = importlib.util.spec_from_loader(modname, loader)
	if spec is None or spec.loader is None:
		raise ImportError(f"Could not create spec for {path}")
	module = importlib.util.module_from_spec(spec)
	loader.exec_module(module)
	return module


def main(argv: List[str] | None = None) -> int:
	argv = list(argv or sys.argv[1:])
	here = os.path.dirname(os.path.abspath(__file__))
	bin_dir = os.path.join(here, "bin")

	path, tried = find_binary(bin_dir)
	if not path:
		print("No suitable binary found in ./bin")
		if tried:
			print("Tried candidates:")
			for t in tried:
				print(" -", os.path.basename(t))
		else:
			print("No candidates generated (bin directory missing or empty).")
		# show available files for debugging
		try:
			avail = os.listdir(bin_dir)
			if avail:
				print("Available files in bin:")
				for a in avail:
					print(" -", a)
		except FileNotFoundError:
			pass
		return 2

	try:
		module = load_extension(path)
	except Exception as exc:  # pragma: no cover - runtime error handling
		print(f"Failed to load extension {path}: {exc}")
		return 3
	
	module.main()
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
