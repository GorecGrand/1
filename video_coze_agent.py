"""Video processing pipeline with optional Coze.com integration."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from typing import Callable, Iterator, Optional

import cv2
import numpy as np
import requests


FrameProcessor = Callable[[np.ndarray, int], Optional[str]]


def read_video_frames(path: str, frame_step: int = 1) -> Iterator[np.ndarray]:
    """Yield frames from ``path`` at the desired ``frame_step`` spacing."""

    if frame_step < 1:
        raise ValueError("frame_step must be >= 1")

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open video file: {path}")

    try:
        idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % frame_step == 0:
                yield frame
            idx += 1
    finally:
        cap.release()


@dataclass
class CozeClient:
    """Minimal Coze API client for posting updates from the agent."""

    bot_id: str
    user_id: str
    api_key: str
    api_base: str = "https://api.coze.com/open_api/v1/chat"

    def send_message(self, content: str, conversation_id: Optional[str] = None) -> dict:
        """Send a text message to Coze and return the API response."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "bot_id": self.bot_id,
            "user_id": self.user_id,
            "auto_generate_name": False,
            "type": "TEXT",
            "content": content,
        }

        if conversation_id is not None:
            payload["conversation_id"] = conversation_id

        response = requests.post(self.api_base, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()


def process_video(
    path: str,
    frame_step: int = 1,
    processor: Optional[FrameProcessor] = None,
    coze_client: Optional[CozeClient] = None,
    coze_interval: int = 30,
) -> None:
    """Iterate through the video, process frames, and optionally notify Coze."""

    if processor is None:
        processor = default_processor

    conversation_id: Optional[str] = None
    for idx, frame in enumerate(read_video_frames(path, frame_step), start=1):
        summary = processor(frame, idx)

        if coze_client is not None and summary and idx % coze_interval == 0:
            result = coze_client.send_message(summary, conversation_id)
            conversation_id = result.get("conversation_id", conversation_id)


def default_processor(frame: np.ndarray, idx: int) -> str:
    """Example frame processor that converts a frame to grayscale and reports size."""

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    return f"Frame {idx}: grayscale {width}x{height} processed."


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Video agent with Coze integration")
    parser.add_argument("video_file", help="Path to the video file")
    parser.add_argument("--frame-step", type=int, default=1, help="Process every Nth frame")
    parser.add_argument(
        "--coze-bot-id",
        help="Coze bot identifier (required when using Coze integration)",
    )
    parser.add_argument(
        "--coze-user-id",
        default=os.getenv("COZE_USER_ID", "video-agent"),
        help="External user identifier used for the conversation",
    )
    parser.add_argument(
        "--coze-api-key",
        default=os.getenv("COZE_API_KEY"),
        help="Coze API key (env COZE_API_KEY)",
    )
    parser.add_argument(
        "--coze-api-base",
        default=os.getenv("COZE_API_BASE", "https://api.coze.com/open_api/v1/chat"),
        help="Override Coze API base URL if required",
    )
    parser.add_argument(
        "--coze-interval",
        type=int,
        default=30,
        help="Send updates to Coze every N processed frames",
    )
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    coze_client = None
    if args.coze_bot_id:
        if not args.coze_api_key:
            parser.error("Coze integration requires --coze-api-key or COZE_API_KEY env var")

        coze_client = CozeClient(
            bot_id=args.coze_bot_id,
            user_id=args.coze_user_id,
            api_key=args.coze_api_key,
            api_base=args.coze_api_base,
        )

    process_video(
        path=args.video_file,
        frame_step=args.frame_step,
        coze_client=coze_client,
        coze_interval=max(1, args.coze_interval),
    )


if __name__ == "__main__":
    main()

