from dataclasses import dataclass


@dataclass
class PatcherWidgetConfig:
    long_press_interval: int = 400
    hover_long_press_interval: int = 500

    node_width: float = 130.0
    node_height: float = 54.0
    node_margin_padding: float = 30.0
    min_layout_radius: float = 80.0
    node_touch_padding: float = 10.0
    drag_threshold: float = 12.0
    connection_hit_threshold: float = 14.0

    wire_curvature: float = 0.22
    wire_curvature_offset: float = 0.12

    background_color: str = "#1E2227"
    background_circle_color: tuple[int, int, int, int] = (45, 52, 64, 120)
    background_circle_width: int = 2

    primary_cable_color: str = "#38DE7A"
    secondary_cable_color: str = "#61AFEF"
    drag_cable_color: str = "#E5C07B"
    drag_hover_cable_color: str = "#98C379"
    connection_line_width: float = 3.0
    connection_arrow_size: float = 13.0
    drag_line_width: float = 3.5
    drag_arrow_size: float = 15.0

    arrow_head_angle_divisor: float = 7.0

    wire_label_font_size: int = 9
    wire_label_horizontal_padding: int = 14
    wire_label_vertical_padding: int = 6
    wire_label_border_color: str = "#4B5263"
    wire_label_border_width: float = 1.0
    wire_label_background_rgba: tuple[int, int, int, int] = (33, 37, 43, 230)
    wire_label_text_color: str = "#ECEFF4"
    wire_label_radius: float = 6.0
    wire_label_padding: float = 3.0

    node_background_color: str = "#282C34"
    node_border_color: str = "#4B5263"
    node_border_width: float = 1.5
    node_hover_border_color: str = "#98C379"
    node_hover_border_width: float = 3.0
    node_hover_background_color: str = "#2D3748"
    node_drag_border_color: str = "#E5C07B"
    node_drag_border_width: float = 3.0
    node_drag_background_color: str = "#3E3D32"
    node_pressed_border_color: str = "#61AFEF"
    node_pressed_border_width: float = 2.5
    node_pressed_background_color: str = "#2C313A"
    node_connected_border_color: str = "#528BFF"
    node_connected_border_width: float = 2.0

    node_active_text_color: str = "#FFFFFF"
    node_text_color: str = "#E5E9F0"
    node_name_font_size: int = 11
    node_port_font_size: int = 8
    node_name_rect_x_padding: float = 6.0
    node_name_rect_y_padding: float = 6.0
    node_name_rect_height: float = 22.0
    node_port_rect_x_padding: float = 4.0
    node_port_rect_y: float = 28.0
    node_port_rect_height: float = 20.0
    node_output_port_color: str = "#98C379"
    node_no_output_port_color: str = "#ABB2BF"

    info_font_size: int = 10
    info_text_rgba: tuple[int, int, int, int] = (150, 160, 175, 180)
    info_rect_width: float = 240.0
    info_rect_height: float = 40.0

    port_selector_max_rows: int = 4
    port_selector_grid_spacing: int = 8
    port_selector_grid_margin: int = 4
    port_selector_layout_margin_left: int = 16
    port_selector_layout_margin_top: int = 14
    port_selector_layout_margin_right: int = 16
    port_selector_layout_margin_bottom: int = 14
    port_selector_layout_spacing: int = 10
    port_selector_base_col_width: int = 175
    port_selector_min_width: int = 360
    port_selector_parent_margin: int = 40
    port_selector_max_width: int = 1200
    port_selector_extra_width: int = 80
    port_selector_width_padding: int = 48
    port_selector_base_height: int = 150
    port_selector_row_height: int = 52
    port_selector_max_height: int = 420
