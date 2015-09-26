# -*- coding: utf-8 -*-
# Natural Language Toolkit: Stack decoder
#
# Copyright (C) 2001-2015 NLTK Project
# Author: Tah Wei Hoon <hoon.tw@gmail.com>
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

"""
Tests for stack decoder
"""

import unittest
from nltk.translate import PhraseTable
from nltk.translate import StackDecoder
from nltk.translate.stack_decoder import _Hypothesis, _Stack


class TestStackDecoder(unittest.TestCase):
    def test_find_all_src_phrases(self):
        # arrange
        phrase_table = TestStackDecoder.create_fake_phrase_table()
        stack_decoder = StackDecoder(phrase_table, None)
        sentence = ['my', 'hovercraft', 'is', 'full', 'of', 'eels']

        # act
        src_phrase_spans = stack_decoder.find_all_src_phrases(sentence)

        # assert
        self.assertEqual(src_phrase_spans[0], [2])  # 'my hovercraft'
        self.assertEqual(src_phrase_spans[1], [2])  # 'hovercraft'
        self.assertEqual(src_phrase_spans[2], [3])  # 'is'
        self.assertEqual(src_phrase_spans[3], [5, 6])  # 'full of', 'full of eels'
        self.assertFalse(src_phrase_spans[4])  # no entry starting with 'of'
        self.assertEqual(src_phrase_spans[5], [6])  # 'eels'

    def test_valid_phrases(self):
        # arrange
        hypothesis = _Hypothesis()
        # mock untranslated_spans method
        hypothesis.untranslated_spans = lambda _: [
            (0, 2),
            (3, 6)
        ]
        all_phrases_from = [
            [1, 4],
            [2],
            [],
            [5],
            [5, 6, 7],
            [],
            [7]
        ]

        # act
        phrase_spans = StackDecoder.valid_phrases(all_phrases_from, hypothesis)

        # assert
        self.assertEqual(phrase_spans, [(0, 1), (1, 2), (3, 5), (4, 5), (4, 6)])

    @staticmethod
    def create_fake_phrase_table():
        phrase_table = PhraseTable()
        phrase_table.add(('hovercraft',), ('',), 0.8)
        phrase_table.add(('my', 'hovercraft'), ('', ''), 0.7)
        phrase_table.add(('my', 'cheese'), ('', ''), 0.7)
        phrase_table.add(('is',), ('',), 0.8)
        phrase_table.add(('is',), ('',), 0.5)
        phrase_table.add(('full', 'of'), ('', ''), 0.01)
        phrase_table.add(('full', 'of', 'eels'), ('', '', ''), 0.5)
        phrase_table.add(('full', 'of', 'spam'), ('', ''), 0.5)
        phrase_table.add(('eels',), ('',), 0.5)
        phrase_table.add(('spam',), ('',), 0.5)
        return phrase_table


class TestHypothesis(unittest.TestCase):
    def setUp(self):
        root = _Hypothesis()
        child = _Hypothesis(
            score=0.5,
            src_phrase_span=(3, 7),
            trg_phrase=('hello', 'world'),
            previous=root
        )
        grandchild = _Hypothesis(
            score=0.4,
            src_phrase_span=(1, 2),
            trg_phrase=('and', 'goodbye'),
            previous=child
        )
        self.hypothesis_chain = grandchild

    def test_translation_so_far(self):
        # act
        translation = self.hypothesis_chain.translation_so_far()

        # assert
        self.assertEqual(translation, ['hello', 'world', 'and', 'goodbye'])

    def test_translation_so_far_for_empty_hypothesis(self):
        # arrange
        hypothesis = _Hypothesis()

        # act
        translation = hypothesis.translation_so_far()

        # assert
        self.assertEqual(translation, [])

    def test_total_translated_words(self):
        # act
        total_translated_words = self.hypothesis_chain.total_translated_words()

        # assert
        self.assertEqual(total_translated_words, 5)

    def test_translated_positions(self):
        # act
        translated_positions = self.hypothesis_chain.translated_positions()

        # assert
        translated_positions.sort()
        self.assertEqual(translated_positions, [1, 3, 4, 5, 6])

    def test_untranslated_spans(self):
        # act
        untranslated_spans = self.hypothesis_chain.untranslated_spans(10)

        # assert
        self.assertEqual(untranslated_spans, [(0, 1), (2, 3), (7, 10)])

    def test_untranslated_spans_for_empty_hypothesis(self):
        # arrange
        hypothesis = _Hypothesis()

        # act
        untranslated_spans = hypothesis.untranslated_spans(10)

        # assert
        self.assertEqual(untranslated_spans, [(0, 10)])


class TestStack(unittest.TestCase):
    def test_push_bumps_off_worst_hypothesis_when_stack_is_full(self):
        # arrange
        stack = _Stack(3)
        poor_hypothesis = _Hypothesis(0.01)

        # act
        stack.push(_Hypothesis(0.2))
        stack.push(poor_hypothesis)
        stack.push(_Hypothesis(0.1))
        stack.push(_Hypothesis(0.3))

        # assert
        self.assertFalse(poor_hypothesis in stack)

    def test_push_removes_hypotheses_that_fall_below_beam_threshold(self):
        # arrange
        stack = _Stack(3, 0.5)
        poor_hypothesis = _Hypothesis(0.01)
        worse_hypothesis = _Hypothesis(0.009)

        # act
        stack.push(poor_hypothesis)
        stack.push(worse_hypothesis)
        stack.push(_Hypothesis(0.9))  # greatly superior hypothesis

        # assert
        self.assertFalse(poor_hypothesis in stack)
        self.assertFalse(worse_hypothesis in stack)

    def test_push_does_not_add_hypothesis_that_falls_below_beam_threshold(self):
        # arrange
        stack = _Stack(3, 0.5)
        poor_hypothesis = _Hypothesis(0.01)

        # act
        stack.push(_Hypothesis(0.9))  # greatly superior hypothesis
        stack.push(poor_hypothesis)

        # assert
        self.assertFalse(poor_hypothesis in stack)

    def test_best_returns_the_best_hypothesis(self):
        # arrange
        stack = _Stack(3)
        best_hypothesis = _Hypothesis(0.99)

        # act
        stack.push(_Hypothesis(0.0))
        stack.push(best_hypothesis)
        stack.push(_Hypothesis(0.5))

        # assert
        self.assertEqual(stack.best(), best_hypothesis)

    def test_best_returns_none_when_stack_is_empty(self):
        # arrange
        stack = _Stack(3)

        # assert
        self.assertEqual(stack.best(), None)
