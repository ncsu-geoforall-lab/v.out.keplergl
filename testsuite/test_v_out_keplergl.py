#!/usr/bin/env python3

"""
MODULE:    Test of v.out.keplergl

AUTHOR(S): Vaclav Petras <wenzeslaus gmail com>

PURPOSE:   Test of v.out.keplergl (example of a simple test of a module)

COPYRIGHT: (C) 2020 by Vaclav Petras and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestWatershed(TestCase):
    """The main (and only) test case for the v.out.keplergl module"""

    # Vector map(s) be used as inputs (they exist in the NC SPM sample location)
    test_input_1 = "geology"
    # Filename used as output
    output = "output.html"

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region

        These are things needed by all test function but not modified by
        any of them.
        """
        # We will use specific computational region for our process in case
        # something else is running in parallel with our tests.
        cls.use_temp_region()
        # Use of of the inputs to set computational region
        cls.runModule("g.region", vector=cls.test_input_1)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region"""
        cls.del_temp_region()

    def tearDown(self):
        """Remove the output created from the module

        This is executed after each test function run.

        Since we remove the file after running each test function,
        we can reuse the same name for all the test functions.
        """
        if os.path.isfile(self.output):
            os.remove(self.output)

    def test_output_created(self):
        """Check that the output is created"""
        # run the watershed module
        self.assertModule(
            "v.out.keplergl",
            input=self.test_input_1,
            output=self.output,
        )
        # check to see if output is in mapset
        self.assertFileExists(self.output, msg="Output was not created")

    def test_missing_parameter(self):
        """Check that the module fails when parameters are missing"""
        self.assertModuleFail(
            "v.out.keplergl",
            output=self.output,
            msg="The input parameter should be required",
        )
        self.assertModuleFail(
            "v.out.keplergl",
            input=self.test_input_1,
            msg="The output parameter should be required",
        )


if __name__ == "__main__":
    test()
