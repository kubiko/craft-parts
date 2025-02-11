# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from craft_parts import errors
from craft_parts.executor import filesets
from craft_parts.executor.filesets import Fileset


@pytest.mark.parametrize(
    "tc_data,tc_entries,tc_includes,tc_excludes",
    [
        ([], [], [], []),
        (["a", "b"], ["a", "b"], ["a", "b"], []),
        (["a", "-b"], ["a", "-b"], ["a"], ["b"]),
    ],
)
def test_fileset(tc_data, tc_entries, tc_includes, tc_excludes):
    fs = Fileset(tc_data)
    assert fs.entries == tc_entries
    assert fs.includes == tc_includes
    assert fs.excludes == tc_excludes


def test_representation():
    fs = Fileset(["foo", "bar"], name="foobar")
    assert f"{fs!r}" == "Fileset(['foo', 'bar'], name='foobar')"


def test_entries():
    fs = Fileset(["foo", "bar"])
    fs.entries.append("baz")
    assert fs.entries == ["foo", "bar"]


def test_remove():
    fs = Fileset(["foo", "bar", "baz"])
    fs.remove("bar")
    assert fs.entries == ["foo", "baz"]


@pytest.mark.parametrize(
    "tc_fs1,tc_fs2,tc_result",
    [
        ([], [], []),
        (["foo"], ["bar"], ["bar"]),
        # combine if fs2 has a wildcard
        (["foo"], ["bar", "*"], ["foo", "bar"]),
        # combine if fs2 is only excludes
        (["foo"], ["-bar"], ["foo", "-bar"]),
        (["foo", "*"], ["bar"], ["bar"]),
        (["-foo"], ["-bar"], ["-foo", "-bar"]),
        (["-foo"], ["bar"], ["bar"]),
        (["foo"], ["-bar", "baz"], ["-bar", "baz"]),
        (["-foo", "bar"], ["bar"], ["bar"]),
        # combine wildcards
        (["-*"], ["*"], ["-*"]),
        (["-*"], ["somefile", "*"], ["-*", "somefile"]),
    ],
)
def test_combine(tc_fs1, tc_fs2, tc_result):
    fs1 = Fileset(tc_fs1)
    fs2 = Fileset(tc_fs2)
    fs1.combine(fs2)
    assert sorted(fs1.entries) == sorted(tc_result)


def test_fileset_combine_conflicts():
    stage_set = Fileset(["thisfile", "otherfile"])
    prime_set = Fileset(["-otherfile"])

    with pytest.raises(errors.FilesetConflict) as raised:
        prime_set.combine(stage_set)
    assert raised.value.conflicting_files == {"otherfile"}


def test_fileset_only_includes():
    stage_set = Fileset(["opt/something", "usr/bin"])

    include, exclude = filesets._get_file_list(stage_set)

    assert include == ["opt/something", "usr/bin"]
    assert exclude == []


def test_fileset_only_excludes():
    stage_set = Fileset(["-etc", "-usr/lib/*.a"])

    include, exclude = filesets._get_file_list(stage_set)

    assert include == ["*"]
    assert exclude == ["etc", "usr/lib/*.a"]


def test_filesets_includes_without_relative_paths():
    with pytest.raises(errors.FilesetError) as raised:
        filesets._get_file_list(Fileset(["rel", "/abs/include"], name="test"))
    assert raised.value.name == "test"
    assert raised.value.message == "path '/abs/include' must be relative."


def test_filesets_excludes_without_relative_paths():
    with pytest.raises(errors.FilesetError) as raised:
        filesets._get_file_list(Fileset(["rel", "-/abs/exclude"], name="test"))
    assert raised.value.name == "test"
    assert raised.value.message == "path '/abs/exclude' must be relative."


# migratable_filesets tested in tests/unit/executor/test_step_handler.py
