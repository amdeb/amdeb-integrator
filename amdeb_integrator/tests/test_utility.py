# -*- coding: utf-8 -*-

from unittest2 import TestCase

# unable to run unittest in an IDE because the module imports other addons
from openerp.addons.amdeb_integrator.shared import utility


# the filename has to be test_XXX to be executed by Odoo testing
# the class name doesn't have this convention
class TestUtility(TestCase):

    def test_is_sequence_with_sequences(self):
        """Test is_sequence using some sequences"""
        subject1 = []
        subject2 = [0, ]
        subject3 = (0, )
        subject4 = {'one': 1, }

        self.assertTrue(utility.is_sequence(subject1))
        self.assertTrue(utility.is_sequence(subject2))
        self.assertTrue(utility.is_sequence(subject3))
        self.assertTrue(utility.is_sequence(subject4))

    def test_is_sequence_without_sequence(self):
        """Test is_sequence using non-sequence subjects"""
        subject1 = 0
        subject2 = None
        subject3 = "abc"

        class TestClass(object):
            pass
        subject4 = TestClass()

        self.assertFalse(utility.is_sequence(subject1))
        self.assertFalse(utility.is_sequence(subject2))
        self.assertFalse(utility.is_sequence(subject3))
        self.assertFalse(utility.is_sequence(subject4))