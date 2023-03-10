# Copyright (C) 2021 Cancer Care Associates

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import pathlib
import subprocess

import docuscope._utilities.test as pmp_test_utils

HERE = pathlib.Path(__file__).parent.resolve()


def run_test_commands_with_gui_process(commands):
    gui_command = [
        pmp_test_utils.get_executable_even_when_embedded(),
        "-m",
        "docuscope",
        "gui",
    ]

    with pmp_test_utils.process(gui_command, cwd=HERE):
        for command in commands:
            subprocess.check_call(command, cwd=HERE, shell=True)
