# -*- coding: utf-8 -*-
#
#            PySceneDetect: Python-Based Video Scene Detector
#   -------------------------------------------------------------------
#     [  Site:    https://scenedetect.com                           ]
#     [  Docs:    https://scenedetect.com/docs/                     ]
#     [  Github:  https://github.com/Breakthrough/PySceneDetect/    ]
#
# Copyright (C) 2014-2023 Brandon Castellano <http://www.bcastell.com>.
# PySceneDetect is licensed under the BSD 3-Clause License; see the
# included LICENSE file, or visit one of the above pages for details.
#
""":class:`ContentDetector` compares the difference in content between adjacent frames against a
set threshold/score, which if exceeded, triggers a scene cut.

This detector is available from the command-line as the `detect-content` command.
"""
from dataclasses import dataclass
from typing import List, Optional

import numpy
import cv2

from scenedetect.scene_detector import SceneDetector

from PIL import Image
import imagehash

class SlideChangeDetector(SceneDetector):

    @dataclass
    class _FrameData:
        image: numpy.ndarray

    def __init__(
        self,
        threshold: float = 4.0,
        min_scene_len: int = 15
    ):
        """
        Arguments:
            threshold: Threshold the average change in pixel intensity must exceed to trigger a cut.
            min_scene_len: Once a cut is detected, this many frames must pass before a new one can
                be added to the scene list.
        """
        super().__init__()
        self._threshold: float = threshold
        self._min_scene_len: int = min_scene_len
        self._last_scene_cut: Optional[int] = None
        self._last_frame_hash: Optional[int] = None
        self._frame_score: Optional[float] = None

    def get_metrics(self):
        return None

    def is_processing_required(self, frame_num):
        return True

    def _calculate_frame_score(self, frame_num: int, frame_img: numpy.ndarray) -> float:
        color_converted = cv2.cvtColor(frame_img, cv2.COLOR_BGR2GRAY)
        p1=Image.fromarray(color_converted)

        hash = imagehash.phash(p1)

        if self._last_frame_hash is None:
            # Need another frame to compare with for score calculation.
            self._last_frame_hash = hash
            return 0.0

        diff = hash - self._last_frame_hash
        self._last_frame_hash = hash
        return diff


    def process_frame(self, frame_num: int, frame_img: numpy.ndarray) -> List[int]:
        """ Similar to ThresholdDetector, but using the HSV colour space DIFFERENCE instead
        of single-frame RGB/grayscale intensity (thus cannot detect slow fades with this method).

        Arguments:
            frame_num: Frame number of frame that is being passed.
            frame_img: Decoded frame image (numpy.ndarray) to perform scene
                detection on. Can be None *only* if the self.is_processing_required() method
                (inhereted from the base SceneDetector class) returns True.

        Returns:
            List of frames where scene cuts have been detected. There may be 0
            or more frames in the list, and not necessarily the same as frame_num.
        """
        if frame_img is None:
            # TODO(0.6.3): Make frame_img a required argument in the interface. Log a warning
            # that passing None is deprecated and results will be incorrect if this is the case.
            return []

        # Initialize last scene cut point at the beginning of the frames of interest.
        if self._last_scene_cut is None:
            self._last_scene_cut = frame_num

        self._frame_score = self._calculate_frame_score(frame_num, frame_img)
        if self._frame_score is None:
            return []

        # We consider any frame over the threshold a new scene, but only if
        # the minimum scene length has been reached (otherwise it is ignored).
        min_length_met = (frame_num - self._last_scene_cut) >= self._min_scene_len
        if self._frame_score >= self._threshold and min_length_met:
            self._last_scene_cut = frame_num
            return [frame_num]

        return []
