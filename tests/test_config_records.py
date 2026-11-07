"""Configuration validation (unit errors), records (no overwrite), dirty-tree refusal."""

import copy
import json
import subprocess

import pytest
import yaml

from conftest import BASELINE
from picket_sim.config import ConfigError, build_array, config_sha256, validate_config
from picket_sim.records import RunDirectory


def _cfg():
    return yaml.safe_load(BASELINE.read_text())


def test_baseline_validates_and_hash_is_stable():
    c = _cfg()
    validate_config(c)
    assert config_sha256(c) == config_sha256(copy.deepcopy(c))
    c2 = copy.deepcopy(c)
    c2["physics"]["sound_speed_mps"] = 1501.0
    assert config_sha256(c2) != config_sha256(c)


@pytest.mark.parametrize(
    "path, value",
    [
        (("physics", "sound_speed_mps"), 1.5),  # km/s
        (("physics", "sound_speed_mps"), 4921.0),  # ft/s
        (("frequency_grid", "f_min_hz"), 0.1),  # kHz
        (("frequency_grid", "f_max_hz"), 50.0),  # below f_min
    ],
)
def test_unit_errors_rejected(path, value):
    c = _cfg()
    c[path[0]][path[1]] = value
    with pytest.raises(ConfigError):
        validate_config(c)


def test_geometry_unit_errors_rejected():
    with pytest.raises(ConfigError):  # millimetres instead of metres
        build_array({"id": "X", "type": "linear", "n_elements": 4, "spacing_m": 150.0})
    with pytest.raises(ConfigError):  # coincident sensors
        build_array({"id": "X", "type": "coordinates", "positions_m": [[0, 0, 0], [0, 0, 0.0001]]})
    with pytest.raises(ConfigError):
        build_array({"id": "X", "type": "hexagonal"})


def test_steering_and_grid_validation():
    c = _cfg()
    c["steering"]["rings"][0]["az_step_deg"] = 7.0
    with pytest.raises(ConfigError):
        validate_config(c)
    c = _cfg()
    c["grids"]["sphere"]["n_az"] = 361
    with pytest.raises(ConfigError):
        validate_config(c)


def test_a4_coordinates_are_configurable():
    c = _cfg()
    spec = next(a for a in c["arrays"] if a["id"] == "A4")
    spec["positions_m"] = [[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, -2]]
    g = build_array(spec)
    assert g.aperture_m == pytest.approx(2 * 2 ** 0.5)


def test_run_directory_never_overwrites(tmp_path):
    rd = RunDirectory(tmp_path, "run1")
    rd.path("tables", "x.csv").write_text("a\n1\n")
    final = rd.finalize({"run_id": "run1", "experiment_id": "T", "status": "complete"})
    rec = json.loads((final / "record.json").read_text())
    assert rec["outputs"][0]["path"] == "tables/x.csv" and len(rec["outputs"][0]["sha256"]) == 64
    with pytest.raises(FileExistsError):
        RunDirectory(tmp_path, "run1")
    assert (tmp_path / "RUN_INDEX.csv").read_text().count("run1") == 1


def test_dirty_tree_refused(tmp_path):
    from picket_sim.experiments import sim01
    from picket_sim.records import DirtyTreeError

    repo = tmp_path / "repo"
    repo.mkdir()
    cfg_path = repo / "cfg.yaml"
    cfg_path.write_text(BASELINE.read_text())
    for cmd in (["git", "init", "-q"], ["git", "add", "cfg.yaml"],
                ["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "x"]):
        subprocess.run(cmd, cwd=repo, check=True)
    cfg_path.write_text(BASELINE.read_text() + "\n# local edit\n")
    with pytest.raises(DirtyTreeError):
        sim01.run(cfg_path, output_root=tmp_path / "out", repo_dir=repo, log=lambda *a: None)
    assert not (tmp_path / "out").exists() or not any((tmp_path / "out").iterdir())
