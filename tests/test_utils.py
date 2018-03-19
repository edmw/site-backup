# coding: utf-8

import pytest

from backup.utils import slugify

def testSlugify():
	assert slugify(None) == None
	assert slugify(u"") == ""
	assert slugify(u"This") == "this"
	assert slugify(u"is") == "is"
	assert slugify(u"the end") == "the-end"
	assert slugify(u"Hold your breath ") == "hold-your-breath"
	assert slugify(u" and count to ten") == "and-count-to-ten"
	assert slugify(u"Feel the 34r7|-| move and then") == "feel-the-34r7-move-and-then"
	assert slugify(u"-- Hear my heart burst again") == "-hear-my-heart-burst-again"
