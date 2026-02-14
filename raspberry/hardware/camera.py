"""
camera.py
---------
Gestion de la caméra CSI via GStreamer pour WebRTC.

Ce module fournit :
    - CameraTrack : flux vidéo pour aiortc
    - pipeline GStreamer optimisé pour Raspberry Pi

Robuste :
    - si la caméra échoue → frame noire
    - rotation 180° (caméra montée à l’envers)
"""

import cv2
import numpy as np
from aiortc import VideoStreamTrack
from av import VideoFrame


class CameraTrack(VideoStreamTrack):
    """Flux vidéo CSI → WebRTC via GStreamer."""

    def __init__(self):
        super().__init__()

        # Pipeline GStreamer optimisé pour Raspberry Pi
        pipeline = (
            "libcamerasrc ! "
            "video/x-raw,format=YUY2,width=640,height=480,framerate=30/1 ! "
            "videoconvert ! "
            "video/x-raw,format=BGR ! "
            "appsink"
        )

        self.cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            print("[CAMERA] ERREUR : impossible d'ouvrir la caméra CSI via GStreamer")

    async def recv(self):
        """Capture une frame CSI et la convertit en VideoFrame aiortc."""
        pts, time_base = await self.next_timestamp()

        ret, frame = self.cap.read()

        if not ret or frame is None:
            # Sécurité : frame noire si caméra HS
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Rotation 180° (caméra montée à l’envers)
        frame = cv2.rotate(frame, cv2.ROTATE_180)

        # Conversion vers VideoFrame
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame
