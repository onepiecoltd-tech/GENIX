"""Chạy harvest toàn bộ loài: PYTHONPATH=src python3 examples/harvest_all.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from genechain.bulk_harvest import run
run(os.path.join(os.path.dirname(__file__), ".."))
