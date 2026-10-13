import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainterPath, QPainterPathStroker


MIN_CABLE_LENGTH = 8.0


def node_shape(rect: QRectF) -> QPainterPath:
    """Returns the visual/intersection shape used for a device node."""
    path = QPainterPath()
    path.addRoundedRect(rect, 10.0, 10.0)
    return path


def line_path(start: QPointF, end: QPointF) -> QPainterPath:
    """Returns a straight QPainterPath between two points."""
    path = QPainterPath(start)
    path.lineTo(end)
    return path


def point_lerp(p1: QPointF, p2: QPointF, t: float) -> QPointF:
    """Linearly interpolates between two QPointF points."""
    return QPointF(p1.x() + (p2.x() - p1.x()) * t, p1.y() + (p2.y() - p1.y()) * t)


def subsegment_quad_bezier(
        p0: QPointF,
        pc: QPointF,
        p1: QPointF,
        t0: float,
        t1: float,
) -> tuple[QPointF, QPointF, QPointF]:
    """Returns (q0, qc, q1) for the subsegment of quadratic bezier from t0 to t1 using de Casteljau."""
    if t0 <= 0.0 and t1 >= 1.0:
        return p0, pc, p1
    if t0 >= 1.0 or t1 <= t0:
        pt = point_lerp(point_lerp(p0, pc, t0), point_lerp(pc, p1, t0), t0)
        return pt, pt, pt

    # First trim at t0: curve for t in [t0, 1]
    p01 = point_lerp(p0, pc, t0)
    p12 = point_lerp(pc, p1, t0)
    p_prime_0 = point_lerp(p01, p12, t0)
    p_prime_1 = p12
    p_prime_2 = p1

    # Next trim at u = (t1 - t0) / (1.0 - t0): curve for t in [t0, t1]
    u = (t1 - t0) / (1.0 - t0) if t0 < 1.0 else 0.0
    u = max(0.0, min(1.0, u))
    q0 = p_prime_0
    q1 = point_lerp(p_prime_0, p_prime_1, u)
    q12 = point_lerp(p_prime_1, p_prime_2, u)
    q2 = point_lerp(q1, q12, u)
    return q0, q1, q2


def wire_control_point(
        start: QPointF,
        end: QPointF,
        center: QPointF | None = None,
        curvature: float = 0.22,
        offset_idx: int = 0,
        curvature_offset: float = 0.12,
) -> QPointF:
    """
    Calculates the Bezier control point for a wire curved towards the center.
    If center is None or curvature == 0, returns the straight midpoint.
    """
    mid = QPointF((start.x() + end.x()) / 2.0, (start.y() + end.y()) / 2.0)
    if center is None or curvature <= 0.0:
        return mid

    dx = end.x() - start.x()
    dy = end.y() - start.y()
    chord_len = math.hypot(dx, dy)
    if chord_len < 1e-4:
        return mid

    vx = center.x() - mid.x()
    vy = center.y() - mid.y()
    dist_to_center = math.hypot(vx, vy)

    effective_curvature = curvature + offset_idx * curvature_offset

    # Perpendicular normal (pointing towards center if center is offset)
    nx = -dy / chord_len
    ny = dx / chord_len
    if (vx * nx + vy * ny) < 0:
        nx = -nx
        ny = -ny

    if dist_to_center > 1.0:
        ctrl_x = mid.x() + vx * effective_curvature
        ctrl_y = mid.y() + vy * effective_curvature
    else:
        # Opposite nodes passing through center: curve along perpendicular normal
        curve_dist = effective_curvature * chord_len * 0.25
        ctrl_x = mid.x() + nx * curve_dist
        ctrl_y = mid.y() + ny * curve_dist

    return QPointF(ctrl_x, ctrl_y)


def curved_path(
        start: QPointF,
        end: QPointF,
        control_point: QPointF | None = None,
) -> QPainterPath:
    """Returns a quadratic Bezier QPainterPath between start and end."""
    path = QPainterPath(start)
    if control_point is None:
        path.lineTo(end)
    else:
        path.quadTo(control_point, end)
    return path


def stroked_path(path: QPainterPath, width: float) -> QPainterPath:
    """Returns a widened path suitable for hit-testing."""
    stroker = QPainterPathStroker()
    stroker.setWidth(width)
    stroker.setCapStyle(Qt.RoundCap)
    stroker.setJoinStyle(Qt.RoundJoin)
    return stroker.createStroke(path)


def _first_length_outside_shape(
        path: QPainterPath,
        shape: QPainterPath,
        low: float,
        high: float,
) -> float:
    """Finds the first path length where the point is outside shape."""
    for _ in range(24):
        mid = (low + high) / 2.0
        point = path.pointAtPercent(path.percentAtLength(mid))
        if shape.contains(point):
            low = mid
        else:
            high = mid

    return high


def _last_length_before_shape(
        path: QPainterPath,
        shape: QPainterPath,
        low: float,
        high: float,
) -> float:
    """Finds the last path length before the point enters shape."""
    for _ in range(24):
        mid = (low + high) / 2.0
        point = path.pointAtPercent(path.percentAtLength(mid))
        if shape.contains(point):
            high = mid
        else:
            low = mid

    return low


def trimmed_curved_path_between_shapes(
        start_shape: QPainterPath,
        start_center: QPointF,
        end_shape: QPainterPath | None,
        end_point: QPointF,
        center: QPointF | None = None,
        curvature: float = 0.22,
        offset_idx: int = 0,
        curvature_offset: float = 0.12,
) -> QPainterPath:
    """
    Builds a QPainterPath from start_center to end_point, curved towards the center,
    and trimmed so it begins at start_shape boundary and ends at end_shape boundary.
    """
    ctrl = wire_control_point(
        start=start_center,
        end=end_point,
        center=center,
        curvature=curvature,
        offset_idx=offset_idx,
        curvature_offset=curvature_offset,
    )
    raw_path = curved_path(start_center, end_point, ctrl)
    total_length = raw_path.length()
    if total_length < MIN_CABLE_LENGTH:
        return QPainterPath()

    start_length = 0.0
    end_length = total_length

    if start_shape.contains(start_center):
        start_length = _first_length_outside_shape(
            raw_path,
            start_shape,
            0.0,
            total_length,
        )

    if end_shape is not None and end_shape.contains(end_point):
        end_length = _last_length_before_shape(
            raw_path,
            end_shape,
            start_length,
            total_length,
        )

    if end_length - start_length < MIN_CABLE_LENGTH:
        return QPainterPath()

    t0 = raw_path.percentAtLength(start_length)
    t1 = raw_path.percentAtLength(end_length)

    q0, qc, q1 = subsegment_quad_bezier(start_center, ctrl, end_point, t0, t1)
    return curved_path(q0, q1, qc)


def path_endpoints(path: QPainterPath) -> tuple[QPointF, QPointF]:
    """Returns the start and end points for a non-empty path."""
    return path.pointAtPercent(0.0), path.pointAtPercent(1.0)


def path_midpoint(path: QPainterPath) -> QPointF:
    """Returns the midpoint by path length."""
    return path.pointAtPercent(path.percentAtLength(path.length() / 2.0))


def path_end_tangent_angle(path: QPainterPath) -> float:
    """Returns the tangent angle in radians at the end of the path (for arrow head)."""
    length = path.length()
    if length < 1e-4:
        return 0.0
    p_end = path.pointAtPercent(1.0)
    sample_len = max(0.0, length - min(6.0, length * 0.1))
    p_prev = path.pointAtPercent(path.percentAtLength(sample_len))
    dx = p_end.x() - p_prev.x()
    dy = p_end.y() - p_prev.y()
    return math.atan2(dy, dx)


def calculate_wire_label_rect(
        path: QPainterPath,
        t_fraction: float,
        badge_width: float,
        badge_height: float,
) -> QRectF:
    """Computes badge bounding rect centered at t_fraction (0.0 to 1.0) along path length."""
    length = path.length()
    target_length = max(0.0, min(length, t_fraction * length))
    point = path.pointAtPercent(path.percentAtLength(target_length))
    return QRectF(
        point.x() - badge_width / 2.0,
        point.y() - badge_height / 2.0,
        badge_width,
        badge_height,
    )


def find_non_overlapping_label_rect(
        path: QPainterPath,
        badge_width: float,
        badge_height: float,
        offset_idx: int = 0,
        total_pair_conns: int = 1,
        existing_rects: list[QRectF] | None = None,
        obstacle_rects: list[QRectF] | None = None,
        padding: float = 3.0,
) -> QRectF:
    """
    Finds a badge position along the path that does not overlap with existing label rects
    or obstacle rects (such as device nodes).
    """
    existing = existing_rects or []
    obstacles = obstacle_rects or []

    if total_pair_conns <= 1:
        preferred_t = 0.54
    else:
        step = min(0.14, 0.36 / max(1, total_pair_conns - 1))
        preferred_t = 0.54 + (offset_idx - (total_pair_conns - 1) / 2.0) * step
        preferred_t = max(0.28, min(0.72, preferred_t))

    candidates = [preferred_t]
    for delta in [0.05, -0.05, 0.10, -0.10, 0.15, -0.15, 0.20, -0.20]:
        cand = preferred_t + delta
        if 0.24 <= cand <= 0.76:
            candidates.append(cand)

    best_rect: QRectF | None = None
    min_penalty = float("inf")

    for cand in candidates:
        rect = calculate_wire_label_rect(path, cand, badge_width, badge_height)
        padded_rect = rect.adjusted(-padding, -padding, padding, padding)

        overlaps_existing = any(padded_rect.intersects(other) for other in existing)
        overlaps_obstacle = any(rect.intersects(obs) for obs in obstacles)

        if not overlaps_existing and not overlaps_obstacle:
            return rect

        penalty = 0.0
        if overlaps_existing:
            for other in existing:
                inter = rect.intersected(other)
                if not inter.isEmpty():
                    penalty += inter.width() * inter.height() * 100.0
        if overlaps_obstacle:
            for obs in obstacles:
                inter = rect.intersected(obs)
                if not inter.isEmpty():
                    penalty += inter.width() * inter.height() * 10.0
        penalty += abs(cand - preferred_t) * 50.0

        if penalty < min_penalty:
            min_penalty = penalty
            best_rect = rect

    return best_rect if best_rect is not None else calculate_wire_label_rect(
        path, preferred_t, badge_width, badge_height
    )
