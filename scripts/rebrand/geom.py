"""Геометрия для реальных фото: прямые по кромкам, точки схода, метрические пропорции."""
import cv2
import numpy as np


def edge_points(mask, side, lo, hi, step=1):
    pts = []
    if side in ("left", "right"):
        for y in range(lo, hi, step):
            xs = np.flatnonzero(mask[y])
            if xs.size:
                pts.append((xs[0] if side == "left" else xs[-1], y))
    else:
        for x in range(lo, hi, step):
            ys = np.flatnonzero(mask[:, x])
            if ys.size:
                pts.append((x, ys[0] if side == "top" else ys[-1]))
    return np.array(pts, np.float32)


def fit_line(pts):
    """Прямая в однородных координатах (a, b, c): a*x + b*y + c = 0."""
    vx, vy, x0, y0 = cv2.fitLine(pts, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
    return np.array([vy, -vx, vx * y0 - vy * x0], np.float64)


def line_through(p, q):
    return np.cross([p[0], p[1], 1.0], [q[0], q[1], 1.0])


def vline(x):
    return np.array([1.0, 0.0, -float(x)])


def hline(y):
    return np.array([0.0, 1.0, -float(y)])


def meet(l1, l2):
    p = np.cross(l1, l2)
    return p[:2] / p[2]


def quad_from_lines(top, right, bottom, left):
    return np.array([meet(top, left), meet(top, right), meet(bottom, right), meet(bottom, left)], np.float32)


def focal_from_vps(v1, v2, c):
    d = -np.dot(np.asarray(v1) - c, np.asarray(v2) - c)
    return float(np.sqrt(d)) if d > 0 else None


def metric_aspect(quad, f, c):
    """Реальное соотношение ширина/высота плоского прямоугольника по его проекции."""
    src = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], np.float32)
    H = cv2.getPerspectiveTransform(src, np.asarray(quad, np.float32)).astype(np.float64)
    K = np.array([[f, 0, c[0]], [0, f, c[1]], [0, 0, 1.0]])
    M = np.linalg.inv(K) @ H
    return float(np.linalg.norm(M[:, 0]) / np.linalg.norm(M[:, 1]))
