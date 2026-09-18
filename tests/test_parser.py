from biodockify_vina.docking import parse_vina_energy_table, parse_docked_pdbqt_models

SAMPLE_VINA_OUTPUT = """
#################################################################
# AutoDock Vina                                                 #
#################################################################

Reading input ... done.
Setting up the scoring function ... done.
Analyzing the binding site ... done.
Using random seed: 42
Performing search ... done.
Refining results ... done.

mode |   affinity | dist from best mode
     | (kcal/mol) | rmsd l.b.| rmsd u.b.
-----+------------+----------+----------
   1         -8.7      0.000      0.000
   2         -8.2      1.452      2.103
   3         -7.9      2.115      3.402
"""

SAMPLE_PDBQT_OUTPUT = """MODEL 1
REMARK VINA RESULT:    -8.7      0.000      0.000
ATOM      1  C1  LIG L   1      10.123  20.456  30.789  0.00  0.00    +0.05 C 
ENDMDL
MODEL 2
REMARK VINA RESULT:    -8.2      1.452      2.103
ATOM      1  C1  LIG L   1      11.123  21.456  31.789  0.00  0.00    +0.05 C 
ENDMDL
"""


def test_parse_vina_energy_table():
    entries = parse_vina_energy_table(SAMPLE_VINA_OUTPUT)
    assert len(entries) == 3
    assert entries[0]["mode"] == 1
    assert entries[0]["affinity"] == -8.7
    assert entries[1]["mode"] == 2
    assert entries[1]["affinity"] == -8.2
    assert entries[1]["rmsd_lb"] == 1.452
    assert entries[1]["rmsd_ub"] == 2.103
    assert entries[2]["mode"] == 3
    assert entries[2]["affinity"] == -7.9


def test_parse_vina_empty_output():
    entries = parse_vina_energy_table("")
    assert entries == []


def test_parse_vina_malformed_output():
    entries = parse_vina_energy_table("Some random text without table")
    assert entries == []


def test_parse_docked_pdbqt_models():
    models = parse_docked_pdbqt_models(SAMPLE_PDBQT_OUTPUT)
    assert len(models) == 2
    assert "MODEL 1" in models[0]
    assert "MODEL 2" in models[1]


def test_parse_single_model_pdbqt():
    single = "ATOM      1  C1  LIG L   1      10.123  20.456  30.789  0.00  0.00    +0.05 C \n"
    models = parse_docked_pdbqt_models(single)
    assert len(models) == 1
    assert "ATOM" in models[0]


def test_parse_empty_pdbqt():
    models = parse_docked_pdbqt_models("")
    assert models == []
