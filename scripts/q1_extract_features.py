"""E 题问题一：原始视频三模态特征提取、时间组织与审计。

使用方法（在项目根目录执行）：
    python scripts/q1_extract_features.py

输入：
    E-q/dataset/attachment_1_raw_multimodal_samples/mosei_raw_videos_100/
    其中包含 100 条原始视频和 label-100.xlsx。

输出：
    E-q/q_1_output/<YYYYMMDD_HHMMSS_microseconds>/
    包含三模态特征、标签、有效掩码、时间映射、视频元数据、异常清单、
    典型样本摘要/图、运行配置和可复现说明。原始数据只读，不会被覆盖。

说明：
    本脚本提供不依赖外部情感数据的、可复现的特征提取基线。文本时间位置
    采用“按视频时长均匀分配词元”的显式推断规则，因为附件 1 标签表没有
    提供逐词时间戳；该信息会写入 mapping.csv 和 run_config.json，不能当作
    原始观测时间戳使用。后续可在同一接口下替换为 BERT、COVAERP、Facet
    等经核验的特征提取器。
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from openpyxl import load_workbook


DEFAULT_SEED = 20260923
DEFAULT_STEPS = 50
TEXT_HASH_DIM = 64
AUDIO_DIM = 20
VISION_DIM = 20
TEXT_DIM = TEXT_HASH_DIM + 8
SAMPLE_RATE = 16000


def set_seed(seed: int) -> None:
    """固定本脚本中使用的随机状态；当前特征提取本身是确定性的。"""
    random.seed(seed)
    np.random.seed(seed)


def json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"cannot serialize {type(value)!r}")


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=json_default),
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    """Compute a file digest for reproducibility and audit trails."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    """写出 Excel 安全 CSV，避免 ID 被 Excel 当作公式解析成 #NAME?。"""
    def excel_safe(value: Any) -> Any:
        if isinstance(value, str) and value[:1] in {"=", "+", "-", "@"}:
            return "'" + value
        return value

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: excel_safe(row.get(key, "")) for key in fieldnames})


def normalize_clip_id(value: Any) -> str:
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def load_labels(label_path: Path) -> list[dict[str, Any]]:
    workbook = load_workbook(label_path, read_only=True, data_only=True)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    workbook.close()
    if not rows:
        raise ValueError(f"标签表为空：{label_path}")
    header = [str(item).strip() if item is not None else "" for item in rows[0]]
    required = {"video_id", "clip_id", "text", "label", "annotation"}
    missing = required.difference(header)
    if missing:
        raise ValueError(f"标签表缺少字段 {sorted(missing)}，实际字段为 {header}")
    index = {name: header.index(name) for name in required}
    records: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows[1:], start=2):
        if not any(item is not None and str(item).strip() for item in row):
            continue
        video_id = str(row[index["video_id"]]).strip()
        clip_id = normalize_clip_id(row[index["clip_id"]])
        text = "" if row[index["text"]] is None else str(row[index["text"]])
        try:
            label = float(row[index["label"]])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"第 {row_number} 行 label 无法转为数值") from exc
        annotation = str(row[index["annotation"]]).strip()
        records.append(
            {
                "row_number": row_number,
                "video_id": video_id,
                "clip_id": clip_id,
                "sample_id": f"{video_id}_{clip_id}",
                "text": text,
                "label": label,
                "annotation": annotation,
            }
        )
    return records


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|[0-9]+|[^\w\s]", text)


def stable_hash_index(token: str, salt: int) -> tuple[int, float]:
    digest = hashlib.sha256(f"{salt}:{token.lower()}".encode("utf-8")).digest()
    number = int.from_bytes(digest[:8], "little")
    index = number % TEXT_HASH_DIM
    sign = 1.0 if digest[8] % 2 == 0 else -1.0
    return index, sign


def text_features(text: str, duration: float, steps: int) -> tuple[np.ndarray, np.ndarray, list[dict[str, Any]]]:
    """生成词元级固定哈希表示，并按视频时长映射到公共时间窗。"""
    features = np.zeros((steps, TEXT_DIM), dtype=np.float32)
    mask = np.zeros(steps, dtype=np.uint8)
    tokens = tokenize(text)
    mapping: list[dict[str, Any]] = []
    safe_duration = max(float(duration), 1e-6)
    for token_index, token in enumerate(tokens):
        start = safe_duration * token_index / max(len(tokens), 1)
        end = safe_duration * (token_index + 1) / max(len(tokens), 1)
        center = (start + end) / 2.0
        window = min(steps - 1, max(0, int(center / safe_duration * steps)))
        vector = np.zeros(TEXT_DIM, dtype=np.float32)
        for salt in range(2):
            index, sign = stable_hash_index(token, salt)
            vector[index] += sign / math.sqrt(2.0)
        is_alpha = float(token.isalpha())
        is_numeric = float(token.isnumeric())
        is_punctuation = float(bool(re.fullmatch(r"[^A-Za-z0-9]+", token)))
        letters = re.sub(r"[^A-Za-z]", "", token.lower())
        vowel_ratio = sum(char in "aeiou" for char in letters) / max(len(letters), 1)
        vector[TEXT_HASH_DIM:] = np.array(
            [
                is_alpha,
                is_numeric,
                is_punctuation,
                min(len(token), 20) / 20.0,
                vowel_ratio,
                float(token[:1].isupper()),
                float("!" in token or "?" in token),
                float(token_index / max(len(tokens) - 1, 1)),
            ],
            dtype=np.float32,
        )
        features[window] += vector
        mask[window] = 1
        mapping.append(
            {
                "token_index": token_index,
                "token": token,
                "start_sec": start,
                "end_sec": end,
                "window_index": window,
                "time_source": "inferred_uniform_text_timing",
            }
        )
    counts = np.bincount(
        [item["window_index"] for item in mapping], minlength=steps
    ) if mapping else np.zeros(steps, dtype=np.int64)
    for window, count in enumerate(counts):
        if count:
            features[window] /= float(count)
    return features, mask, mapping


def decode_audio(video_path: Path) -> tuple[np.ndarray, dict[str, Any]]:
    command = [
        "ffmpeg",
        "-nostdin",
        "-v",
        "error",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-f",
        "s16le",
        "pipe:1",
    ]
    try:
        result = subprocess.run(command, capture_output=True, timeout=90, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return np.empty(0, dtype=np.float32), {"status": "decode_failed", "error": str(exc)}
    if result.returncode != 0 or not result.stdout:
        return np.empty(0, dtype=np.float32), {
            "status": "decode_failed",
            "returncode": result.returncode,
            "stderr": result.stderr.decode("utf-8", errors="replace")[-500:],
        }
    waveform = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return waveform, {
        "status": "ok",
        "sample_rate": SAMPLE_RATE,
        "samples": int(waveform.size),
        "duration_sec": float(waveform.size / SAMPLE_RATE),
    }


def audio_window_feature(waveform: np.ndarray, start: int, end: int) -> tuple[np.ndarray, int]:
    segment = waveform[max(0, start):max(start, end)]
    if segment.size < 32:
        return np.zeros(AUDIO_DIM, dtype=np.float32), 0
    segment = segment - float(np.mean(segment))
    n_fft = min(1024, max(64, 2 ** int(math.floor(math.log2(segment.size)))))
    spectrum = np.abs(np.fft.rfft(segment, n=n_fft)) ** 2
    frequencies = np.fft.rfftfreq(n_fft, d=1.0 / SAMPLE_RATE)
    bands = np.linspace(0, SAMPLE_RATE / 2.0, 13)
    band_energy = []
    for left, right in zip(bands[:-1], bands[1:]):
        selected = spectrum[(frequencies >= left) & (frequencies < right)]
        band_energy.append(float(np.mean(selected)) if selected.size else 0.0)
    total = max(float(np.sum(spectrum)), 1e-8)
    centroid = float(np.sum(frequencies * spectrum) / total) / (SAMPLE_RATE / 2.0)
    bandwidth = float(np.sqrt(np.sum(((frequencies - centroid * SAMPLE_RATE / 2.0) ** 2) * spectrum) / total)) / (SAMPLE_RATE / 2.0)
    cumulative = np.cumsum(spectrum) / total
    rolloff_index = int(np.searchsorted(cumulative, 0.85))
    rolloff = float(frequencies[min(rolloff_index, frequencies.size - 1)]) / (SAMPLE_RATE / 2.0)
    probability = spectrum / total
    entropy = float(-np.sum(probability * np.log(probability + 1e-8)) / math.log(max(len(probability), 2)))
    rms = float(np.sqrt(np.mean(segment ** 2)))
    zcr = float(np.mean(np.abs(np.diff(np.signbit(segment)))))
    values = np.array(
        [
            *[math.log1p(value) for value in band_energy],
            rms,
            zcr,
            centroid,
            bandwidth,
            rolloff,
            entropy,
            float(np.max(np.abs(segment))),
            float(np.std(segment)),
        ],
        dtype=np.float32,
    )
    return values, int(segment.size)


def video_metadata_and_features(video_path: Path, duration_hint: float, steps: int) -> tuple[dict[str, Any], np.ndarray, np.ndarray, list[dict[str, Any]]]:
    capture = cv2.VideoCapture(str(video_path))
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frame_count_hint = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    duration = frame_count_hint / fps if fps > 0 else float(duration_hint)
    duration = max(duration, float(duration_hint), 1e-6)
    frame_features: list[np.ndarray] = []
    previous_gray: np.ndarray | None = None
    frame_index = 0
    while capture.isOpened():
        ok, frame = capture.read()
        if not ok:
            break
        frame_time = frame_index / fps if fps > 0 else duration * frame_index / max(frame_count_hint, 1)
        small = cv2.resize(frame, (64, 36), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        edges = cv2.Canny((gray * 255).astype(np.uint8), 80, 160)
        edge_density = float(np.mean(edges > 0))
        motion = float(np.mean(np.abs(gray - previous_gray))) if previous_gray is not None else 0.0
        previous_gray = gray
        h, w = rgb.shape[:2]
        center = rgb[h // 4:3 * h // 4, w // 4:3 * w // 4]
        top = np.mean(rgb[: h // 2], axis=(0, 1))
        bottom = np.mean(rgb[h // 2 :], axis=(0, 1))
        left = np.mean(rgb[:, : w // 2], axis=(0, 1))
        right = np.mean(rgb[:, w // 2 :], axis=(0, 1))
        frame_feature = np.array(
            [
                *np.mean(rgb, axis=(0, 1)),
                *np.std(rgb, axis=(0, 1)),
                float(np.mean(gray)),
                float(np.std(gray)),
                edge_density,
                motion,
                *np.mean(center, axis=(0, 1)),
                *np.abs(top - bottom),
                *np.abs(left - right),
                1.0,
            ],
            dtype=np.float32,
        )
        frame_features.append(frame_feature)
        frame_index += 1
    capture.release()
    # 部分 MP4 的容器帧数元数据可能大于实际可解码帧数。使用实际解码帧数
    # 重新分配时间窗，避免视觉有效区间因错误元数据提前结束。
    decoded_count = len(frame_features)
    if fps > 0 and decoded_count > 0:
        duration = max(decoded_count / fps, 1e-6)
    buckets: list[list[np.ndarray]] = [[] for _ in range(steps)]
    for decoded_index, feature in enumerate(frame_features):
        window = min(steps - 1, int(decoded_index / max(decoded_count, 1) * steps))
        buckets[window].append(feature)
    features = np.zeros((steps, VISION_DIM), dtype=np.float32)
    mask = np.zeros(steps, dtype=np.uint8)
    mapping: list[dict[str, Any]] = []
    for window, values in enumerate(buckets):
        if values:
            features[window] = np.mean(np.stack(values), axis=0)
            features[window, -1] = len(values) / max(frame_count_hint, 1)
            mask[window] = 1
        start = duration * window / steps
        end = duration * (window + 1) / steps
        mapping.append(
            {
                "window_index": window,
                "start_sec": start,
                "end_sec": end,
                "frame_start": int(math.floor(start * fps)) if fps > 0 else "",
                "frame_end": int(math.ceil(end * fps)) if fps > 0 else "",
                "frame_count": len(values),
                "time_source": "video_frame_index_and_fps",
            }
        )
    metadata = {
        "video_read_status": "ok" if frame_index > 0 else "read_failed",
        "fps": fps,
        "frame_count_header": frame_count_hint,
        "frame_count_decoded": decoded_count,
        "width": width,
        "height": height,
        "duration_sec": duration,
    }
    return metadata, features, mask, mapping


def probe_video_duration(video_path: Path) -> float:
    capture = cv2.VideoCapture(str(video_path))
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    frames = float(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0)
    capture.release()
    return frames / fps if fps > 0 else 0.0


def make_timeline_plot(path: Path, sample: dict[str, Any], masks: np.ndarray) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    fig, axis = plt.subplots(figsize=(12, 3.2), dpi=180)
    axis.imshow(masks.T, aspect="auto", interpolation="nearest", cmap="Greens", vmin=0, vmax=1)
    axis.set_yticks([0, 1, 2])
    axis.set_yticklabels(["text token", "audio", "vision"])
    axis.set_xlabel("common time window index")
    axis.set_title(f"Question 1 timeline audit: {sample['sample_id']}")
    axis.grid(axis="x", alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-samples", type=int, default=0, help="仅处理前 N 条，用于冒烟测试；默认处理全部")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.steps <= 0 or args.steps > 500:
        raise ValueError("--steps 必须在 1 到 500 之间")
    set_seed(args.seed)
    project_root = args.project_root.resolve()
    raw_root = project_root / "E-q" / "dataset" / "attachment_1_raw_multimodal_samples" / "mosei_raw_videos_100"
    label_path = raw_root / "label-100.xlsx"
    output_parent = project_root / "E-q" / "q_1_output"
    output_parent.mkdir(parents=True, exist_ok=True)
    run_id = time.strftime("%Y%m%d_%H%M%S") + f"_{time.time_ns() % 1_000_000_000:09d}"
    output_root = output_parent / run_id
    output_root.mkdir(parents=True, exist_ok=False)
    if not label_path.exists():
        raise FileNotFoundError(label_path)

    records = load_labels(label_path)
    original_count = len(records)
    if args.max_samples:
        records = records[: args.max_samples]
    label_keys = {(r["video_id"], r["clip_id"]) for r in records}
    if len(label_keys) != len(records):
        raise ValueError("标签表存在重复 video_id/clip_id 主键")

    config = {
        "schema_version": "q1-output-v2",
        "script": "scripts/q1_extract_features.py",
        "seed": args.seed,
        "steps": args.steps,
        "feature_dimensions": {"text": TEXT_DIM, "audio": AUDIO_DIM, "vision": VISION_DIM},
        "text_feature": "sha256-stable-token-hash-64 + 8 lexical statistics",
        "text_timing": "inferred_uniform_text_timing",
        "audio_feature": "ffmpeg mono 16 kHz + 12 log spectral bands + 8 signal statistics",
        "vision_feature": "OpenCV frame statistics: color, gray, edge, motion and spatial differences",
        "raw_root": str(raw_root),
        "label_path": str(label_path),
        "output_root": str(output_root),
        "run_id": run_id,
        "data_boundary": "attachment_1 only; no external sentiment data; original files read-only",
        "normalization": "no train-fitted normalization in question 1 baseline",
        "alignment_rule": "each sample duration is divided into steps equal half-open windows [kD/L, (k+1)D/L)",
        "padding_rule": "zero padding for invalid windows; modality_mask=0; downstream models must not infer validity from feature values",
        "valid_lengths_definition": "count of valid windows per modality, not necessarily a contiguous sequence length",
        "source_integrity": "sample_manifest.csv records source MP4 existence, size and SHA-256",
    }
    write_json(output_root / "run_config.json", config)

    text_all = np.zeros((len(records), args.steps, TEXT_DIM), dtype=np.float32)
    audio_all = np.zeros((len(records), args.steps, AUDIO_DIM), dtype=np.float32)
    vision_all = np.zeros((len(records), args.steps, VISION_DIM), dtype=np.float32)
    mask_all = np.zeros((len(records), args.steps, 3), dtype=np.uint8)
    valid_lengths = np.zeros((len(records), 3), dtype=np.int32)
    manifest_rows: list[dict[str, Any]] = []
    video_rows: list[dict[str, Any]] = []
    mapping_rows: list[dict[str, Any]] = []
    token_rows: list[dict[str, Any]] = []
    anomaly_rows: list[dict[str, Any]] = []
    started = time.time()
    typical: dict[str, Any] | None = None

    for index, record in enumerate(records):
        video_path = raw_root / record["video_id"] / f"{record['clip_id']}.mp4"
        sample_id = record["sample_id"]
        source_exists = video_path.is_file()
        source_size = video_path.stat().st_size if source_exists else 0
        source_sha256 = sha256_file(video_path) if source_exists else ""
        anomalies: list[str] = []
        if not video_path.exists():
            anomalies.append("video_file_missing")
            duration = 0.0
            video_meta = {"video_read_status": "missing"}
            video_features = np.zeros((args.steps, VISION_DIM), dtype=np.float32)
            video_mask = np.zeros(args.steps, dtype=np.uint8)
            video_mapping = []
            audio_wave = np.empty(0, dtype=np.float32)
            audio_meta = {"status": "not_attempted"}
        else:
            duration_hint = probe_video_duration(video_path)
            video_meta, video_features, video_mask, video_mapping = video_metadata_and_features(
                video_path, duration_hint, args.steps
            )
            duration = float(video_meta.get("duration_sec", duration_hint))
            audio_wave, audio_meta = decode_audio(video_path)
            if video_meta.get("video_read_status") != "ok":
                anomalies.append("video_decode_or_empty")
            if audio_meta.get("status") != "ok":
                anomalies.append("audio_decode_failed_or_missing")
            if (
                video_meta.get("frame_count_header", 0)
                and video_meta.get("frame_count_decoded", 0)
                and video_meta["frame_count_header"] != video_meta["frame_count_decoded"]
            ):
                anomalies.append("video_header_decoded_frame_count_mismatch")
        text_feature, text_mask, text_mapping = text_features(record["text"], duration, args.steps)
        audio_feature = np.zeros((args.steps, AUDIO_DIM), dtype=np.float32)
        audio_mask = np.zeros(args.steps, dtype=np.uint8)
        audio_mapping: list[dict[str, Any]] = []
        for window in range(args.steps):
            start_sec = duration * window / args.steps
            end_sec = duration * (window + 1) / args.steps
            feature, sample_count = audio_window_feature(
                audio_wave,
                int(start_sec * SAMPLE_RATE),
                int(end_sec * SAMPLE_RATE),
            )
            audio_feature[window] = feature
            audio_mask[window] = 1 if sample_count > 0 else 0
            audio_mapping.append(
                {
                    "window_index": window,
                    "start_sec": start_sec,
                    "end_sec": end_sec,
                    "audio_sample_start": int(start_sec * SAMPLE_RATE),
                    "audio_sample_end": int(end_sec * SAMPLE_RATE),
                    "audio_sample_count": sample_count,
                    "time_source": "ffmpeg_audio_sample_rate",
                }
            )
        if int(np.sum(audio_mask)) < args.steps and audio_meta.get("status") == "ok":
            anomalies.append("audio_partial_window_coverage")
        if not record["text"].strip():
            anomalies.append("empty_text")
        if not np.isfinite(record["label"]) or not -3.0 <= record["label"] <= 3.0:
            anomalies.append("label_out_of_range")
        text_all[index] = text_feature
        audio_all[index] = audio_feature
        vision_all[index] = video_features
        mask_all[index] = np.stack([text_mask, audio_mask, video_mask], axis=1)
        valid_lengths[index] = np.sum(mask_all[index], axis=0)
        for window in range(args.steps):
            base = {
                "sample_id": sample_id,
                "video_id": record["video_id"],
                "clip_id": record["clip_id"],
                "window_index": window,
                "start_sec": duration * window / args.steps,
                "end_sec": duration * (window + 1) / args.steps,
                "text_valid": int(text_mask[window]),
                "audio_valid": int(audio_mask[window]),
                "vision_valid": int(video_mask[window]),
            }
            audio_item = audio_mapping[window]
            video_item = video_mapping[window] if video_mapping else {}
            mapping_rows.append(
                {
                    **base,
                    "audio_sample_start": audio_item["audio_sample_start"],
                    "audio_sample_end": audio_item["audio_sample_end"],
                    "audio_sample_count": audio_item["audio_sample_count"],
                    "frame_start": video_item.get("frame_start", ""),
                    "frame_end": video_item.get("frame_end", ""),
                    "frame_count": video_item.get("frame_count", 0),
                    "text_time_source": "inferred_uniform_text_timing",
                    "audio_time_source": "ffmpeg_audio_sample_rate",
                    "vision_time_source": "video_frame_index_and_fps",
                }
            )
        for item in text_mapping:
            token_rows.append({"sample_id": sample_id, **item})
        video_row = {
            "sample_id": sample_id,
            "video_id": record["video_id"],
            "clip_id": record["clip_id"],
            "video_path": str(video_path),
            "file_size_bytes": video_path.stat().st_size if video_path.exists() else 0,
            **video_meta,
            "audio_status": audio_meta.get("status", ""),
            "audio_sample_rate": audio_meta.get("sample_rate", ""),
            "audio_samples": audio_meta.get("samples", ""),
            "audio_duration_sec": audio_meta.get("duration_sec", ""),
        }
        video_rows.append(video_row)
        for code in anomalies:
            anomaly_rows.append({"sample_id": sample_id, "type": code, "detail": "detected during q1 extraction"})
        manifest_rows.append(
            {
                **record,
                "feature_row_index": index,
                "video_path": str(video_path),
                "source_file_exists": int(source_exists),
                "source_file_size_bytes": source_size,
                "source_file_sha256": source_sha256,
                "duration_sec": duration,
                "text_tokens": len(text_mapping),
                "text_valid_windows": int(np.sum(text_mask)),
                "audio_valid_windows": int(np.sum(audio_mask)),
                "vision_valid_windows": int(np.sum(video_mask)),
                "text_dim": TEXT_DIM,
                "audio_dim": AUDIO_DIM,
                "vision_dim": VISION_DIM,
                "status": "ok" if not anomalies else "warning",
                "anomalies": ";".join(anomalies),
            }
        )
        if typical is None and not anomalies and len(text_mapping) >= 3:
            typical = {
                "sample_id": sample_id,
                "video_id": record["video_id"],
                "clip_id": record["clip_id"],
                "text": record["text"],
                "label": record["label"],
                "annotation": record["annotation"],
                "duration_sec": duration,
                "tokens": text_mapping[:20],
                "window_count": args.steps,
                "feature_dimensions": {"text": TEXT_DIM, "audio": AUDIO_DIM, "vision": VISION_DIM},
            }
        if (index + 1) % 10 == 0 or index + 1 == len(records):
            print(f"processed {index + 1}/{len(records)} samples", flush=True)

    np.savez_compressed(
        output_root / "q1_aligned_features.npz",
        text=text_all,
        audio=audio_all,
        vision=vision_all,
        modality_mask=mask_all,
        valid_lengths=valid_lengths,
        sample_ids=np.array([row["sample_id"] for row in manifest_rows], dtype=str),
    )
    labels_rows = [
        {key: row[key] for key in ["sample_id", "video_id", "clip_id", "text", "label", "annotation"]}
        for row in records
    ]
    write_csv(output_root / "labels.csv", labels_rows, ["sample_id", "video_id", "clip_id", "text", "label", "annotation"])
    write_csv(output_root / "sample_manifest.csv", manifest_rows, list(manifest_rows[0].keys()) if manifest_rows else ["sample_id"])
    write_csv(output_root / "video_metadata.csv", video_rows, list(video_rows[0].keys()) if video_rows else ["sample_id"])
    write_csv(
        output_root / "time_mapping.csv",
        mapping_rows,
        [
            "sample_id", "video_id", "clip_id", "window_index", "start_sec", "end_sec",
            "text_valid", "audio_valid", "vision_valid", "audio_sample_start", "audio_sample_end",
            "audio_sample_count", "frame_start", "frame_end", "frame_count", "text_time_source",
            "audio_time_source", "vision_time_source",
        ],
    )
    write_csv(output_root / "text_token_mapping.csv", token_rows, ["sample_id", "token_index", "token", "start_sec", "end_sec", "window_index", "time_source"])
    write_csv(output_root / "anomalies.csv", anomaly_rows, ["sample_id", "type", "detail"])
    write_csv(
        output_root / "input_file_manifest.csv",
        [
            {
                "feature_row_index": row["feature_row_index"],
                "sample_id": row["sample_id"],
                "video_id": row["video_id"],
                "clip_id": row["clip_id"],
                "source_path": row["video_path"],
                "exists": row["source_file_exists"],
                "size_bytes": row["source_file_size_bytes"],
                "sha256": row["source_file_sha256"],
            }
            for row in manifest_rows
        ],
        ["feature_row_index", "sample_id", "video_id", "clip_id", "source_path", "exists", "size_bytes", "sha256"],
    )

    if typical is None and records:
        typical = {
            "sample_id": manifest_rows[0]["sample_id"],
            "video_id": manifest_rows[0]["video_id"],
            "clip_id": manifest_rows[0]["clip_id"],
            "text": records[0]["text"],
            "label": records[0]["label"],
            "annotation": records[0]["annotation"],
            "duration_sec": manifest_rows[0]["duration_sec"],
            "tokens": token_rows[:20],
            "window_count": args.steps,
            "feature_dimensions": {"text": TEXT_DIM, "audio": AUDIO_DIM, "vision": VISION_DIM},
        }
    if typical:
        write_json(output_root / "typical_sample.json", typical)
        typical_index = next(i for i, row in enumerate(manifest_rows) if row["sample_id"] == typical["sample_id"])
        make_timeline_plot(output_root / "typical_sample_timeline.png", typical, mask_all[typical_index])

    status_counter = Counter(row["status"] for row in manifest_rows)
    summary = {
        "created_at_local": time.strftime("%Y-%m-%d %H:%M:%S"),
        "elapsed_sec": time.time() - started,
        "label_rows_in_source": original_count,
        "processed_samples": len(records),
        "expected_samples": 100,
        "all_source_samples_processed": len(records) == original_count == 100,
        "unique_sample_ids": len({row["sample_id"] for row in manifest_rows}),
        "status_counts": dict(status_counter),
        "anomaly_count": len(anomaly_rows),
        "files": [
            "anomalies.csv", "input_file_manifest.csv", "labels.csv",
            "output_checksums.json", "q1_aligned_features.npz", "README.md",
            "run_config.json", "run_summary.json", "sample_manifest.csv",
            "text_token_mapping.csv", "time_mapping.csv", "typical_sample.json",
            "typical_sample_timeline.png", "validation_audit.json", "video_metadata.csv",
        ],
        "feature_shapes": {
            "text": list(text_all.shape),
            "audio": list(audio_all.shape),
            "vision": list(vision_all.shape),
            "modality_mask": list(mask_all.shape),
        },
        "read_only_source": True,
        "output_contract": {
            "sample_key": "sample_id",
            "feature_row_index": "NPZ first dimension and manifest feature_row_index",
            "time_mapping_rows_per_sample": args.steps,
            "padding": "all padded values are zero and modality_mask is 0",
        },
    }
    write_json(output_root / "run_summary.json", summary)
    manifest_ids = [row["sample_id"] for row in manifest_rows]
    with np.load(output_root / "q1_aligned_features.npz", allow_pickle=False) as feature_archive:
        npz_ids = [str(value) for value in feature_archive["sample_ids"]]
    mapping_counts = Counter(row["sample_id"] for row in mapping_rows)
    audit = {
        "schema_version": "q1-audit-v2",
        "checks": {
            "source_label_count_is_100": original_count == 100,
            "all_source_rows_processed": len(records) == original_count,
            "sample_ids_unique": len(manifest_ids) == len(set(manifest_ids)),
            "manifest_labels_npz_one_to_one": manifest_ids == [row["sample_id"] for row in labels_rows] == npz_ids,
            "each_sample_has_expected_time_windows": all(count == args.steps for count in mapping_counts.values()) and len(mapping_counts) == len(records),
            "feature_shapes_match_manifest": list(text_all.shape[:2]) == [len(records), args.steps] and list(audio_all.shape[:2]) == [len(records), args.steps] and list(vision_all.shape[:2]) == [len(records), args.steps],
            "mask_values_binary": bool(np.all(np.isin(mask_all, [0, 1]))),
            "invalid_windows_are_zero": bool(np.all(text_all[mask_all[:, :, 0] == 0] == 0) and np.all(audio_all[mask_all[:, :, 1] == 0] == 0) and np.all(vision_all[mask_all[:, :, 2] == 0] == 0)),
            "finite_features": bool(np.isfinite(text_all).all() and np.isfinite(audio_all).all() and np.isfinite(vision_all).all()),
            "source_hashes_present_for_existing_files": all(not row["source_file_exists"] or len(row["source_file_sha256"]) == 64 for row in manifest_rows),
        },
        "definitions": {
            "feature_row_index": "stable zero-based row in text/audio/vision/modality_mask arrays",
            "valid_lengths": "sum of each modality mask over the 50 windows",
            "padding": "zero-valued feature vector with corresponding mask equal to 0",
            "text_alignment": "uniformly inferred token timing; not an observed word-level timestamp",
        },
    }
    audit["passed"] = all(audit["checks"].values())
    write_json(output_root / "validation_audit.json", audit)
    output_hashes = {
        path.name: sha256_file(path)
        for path in sorted(output_root.iterdir())
        if path.is_file() and path.name != "output_checksums.json"
    }
    write_json(output_root / "output_checksums.json", output_hashes)
    readme = f"""# 问题一输出说明\n\n本目录由 `scripts/q1_extract_features.py` 自动生成，运行编号为 `{run_id}`。上级目录 `E-q/q_1_output/` 保存历次运行结果，本次运行不会覆盖历史结果。\n\n## 运行\n\n```powershell\npython scripts/q1_extract_features.py\n```\n\n## CSV 兼容说明\n\nCSV 使用 UTF-8 BOM，并对以 `=、+、-、@` 开头的文本字段添加 Excel 安全前缀 `'`，防止 `video_id`、`sample_id` 等内容被 Excel 当作公式而显示为 `#NAME?`。Excel 打开时会显示原始文本；使用 Python `csv` 读取时，如需还原机器主键，应去除字段开头的单个 `'`。\n\n## 核心文件\n\n- `q1_aligned_features.npz`：`text/audio/vision` 三模态特征、`modality_mask`、`valid_lengths` 和 `sample_ids`。\n- `labels.csv`：从附件 1 标签表读取的原始标签副本。\n- `sample_manifest.csv`：100 条样本的处理状态、时长、维度和异常标记。\n- `video_metadata.csv`：视频帧率、分辨率、帧数、时长及音频解码信息。\n- `time_mapping.csv`：公共时间窗到音频采样点、视频帧和三模态有效状态的映射。\n- `text_token_mapping.csv`：词元到均匀推断时间区间的映射。\n- `anomalies.csv`：异常样本和处理状态。\n- `typical_sample.json`、`typical_sample_timeline.png`：典型样本核验材料。\n- `run_config.json`、`run_summary.json`：参数、特征定义、数据边界和运行摘要。\n\n## 特征与时间说明\n\n文本特征为固定 SHA-256 词元哈希向量加 8 个词法统计量；音频特征由 FFmpeg 解码为单声道 16 kHz 后提取 12 个频带能量和 8 个信号统计量；视觉特征由 OpenCV 提取颜色、灰度、边缘、运动和空间差异统计量。三种特征均按视频时长划分为 {args.steps} 个公共时间窗。附件 1 未提供逐词时间戳，因此文本时间区间标记为 `inferred_uniform_text_timing`，只能视为可复现的时间代理。\n\n本输出是问题一的透明基线特征，不等同于 BERT、COVAERP 或 Facet 特征。后续替换特征提取器时，应保持 `sample_id`、时间映射、有效掩码和输出文件契约。\n"""
    readme += """

## Audit contract

- `sample_manifest.csv` contains one row per source label and the stable `feature_row_index` used by all NPZ arrays.
- `input_file_manifest.csv` maps every sample to its source MP4 and records existence, size, and SHA-256.
- `validation_audit.json` checks sample coverage, one-to-one IDs, time-window counts, finite features, binary masks, and zero padding.
- `output_checksums.json` records SHA-256 digests for generated artifacts.
- Invalid windows are zero padded and must be identified through `modality_mask=0`; `valid_lengths` counts valid windows and does not claim contiguity.
"""
    (output_root / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=json_default))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
