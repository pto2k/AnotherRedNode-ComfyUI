# final_resolution_node.py
# 参考 controlaltai-nodes 的 Flux Resolution Calc 节点改写。
# 在原功能基础上新增两个选项：
#   custom_resolution      (BOOLEAN) 总开关
#   custom_resolution_size (STRING)  格式 "宽:高"，默认 1536:1024
# custom_resolution 设为 Enable 时，直接使用 custom_resolution_size 指定的尺寸，
# 优先级高于 custom_ratio（完全跳过 megapixel x ratio 计算）。
# 原有的输入、输出与取整逻辑均未改动。
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import torch


def pil2tensor(image):
    """Convert PIL image to tensor in the correct format"""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def parse_custom_size(text):
    """解析自定义尺寸字符串，返回 (width, height)。

    兼容 "1536:1024" / "1536x1024" / "1536*1024" / "1536,1024" / "1536 1024" 等写法。
    解析失败时抛出带说明的 ValueError，ComfyUI 会把它显示在节点报错里。
    """
    if not isinstance(text, str):
        raise ValueError("custom_resolution_size 需要是字符串，格式为 宽:高，例如 1536:1024")
    cleaned = text.strip()
    for sep in ("x", "X", "*", ",", " "):
        cleaned = cleaned.replace(sep, ":")
    parts = [p for p in cleaned.split(":") if p.strip() != ""]
    if len(parts) != 2:
        raise ValueError(
            f"custom_resolution_size 格式错误: {text!r}，应为 宽:高，例如 1536:1024"
        )
    try:
        width, height = int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError(
            f"custom_resolution_size 格式错误: {text!r}，宽和高必须是整数，例如 1536:1024"
        )
    if width <= 0 or height <= 0:
        raise ValueError(
            f"custom_resolution_size 宽和高必须为正数: {text!r}"
        )
    return width, height


class FinalResolutionNode:
    @classmethod
    def INPUT_TYPES(cls):
        # Generate megapixel options from 0.1 to 2.5 with 0.1 increments
        megapixel_options = [f"{i/10:.1f}" for i in range(1, 26)]  # 0.1 to 2.5

        return {
            "required": {
                "megapixel": (megapixel_options, {"default": "1.0"}),
                "aspect_ratio": ([
                    "1:1 (Perfect Square)",
                    "2:3 (Classic Portrait)", "3:4 (Golden Ratio)", "3:5 (Elegant Vertical)", "4:5 (Artistic Frame)", "5:7 (Balanced Portrait)", "5:8 (Tall Portrait)",
                    "7:9 (Modern Portrait)", "9:16 (Slim Vertical)", "9:19 (Tall Slim)", "9:21 (Ultra Tall)", "9:32 (Skyline)",
                    "3:2 (Golden Landscape)", "4:3 (Classic Landscape)", "5:3 (Wide Horizon)", "5:4 (Balanced Frame)", "7:5 (Elegant Landscape)", "8:5 (Cinematic View)",
                    "9:7 (Artful Horizon)", "16:9 (Panorama)", "19:9 (Cinematic Ultrawide)", "21:9 (Epic Ultrawide)", "32:9 (Extreme Ultrawide)"
                ], {"default": "1:1 (Perfect Square)"}),
                "divisible_by": (["8", "16", "32", "64"], {"default": "64"}),
                "custom_ratio": ("BOOLEAN", {"default": False, "label_on": "Enable", "label_off": "Disable"}),
                # 注意：custom_aspect_ratio 原在 optional 区，但 ComfyUI 前端固定先渲染
                # required 再渲染 optional（源码 {..required, ..optional} 合并），
                # 为满足 custom_ratio -> custom_aspect_ratio -> custom_resolution 的
                # 控件顺序，将其移入 required。默认值不变，功能行为完全一致。
                "custom_aspect_ratio": ("STRING", {"default": "1:1"}),
                # --- 新增选项（原选项未做任何修改）---
                "custom_resolution": ("BOOLEAN", {"default": False, "label_on": "Enable", "label_off": "Disable"}),
                "custom_resolution_size": ("STRING", {"default": "1536:1024"}),
            },
        }

    RETURN_TYPES = ("INT", "INT", "STRING", "IMAGE")
    RETURN_NAMES = ("width", "height", "resolution", "preview")
    FUNCTION = "calculate_dimensions"
    CATEGORY = "AnotherRedNode/Resolution"
    OUTPUT_NODE = True

    def create_preview_image(self, width, height, resolution, ratio_display):
        # 1024x1024 preview size
        preview_size = (1024, 1024)
        image = Image.new('RGB', preview_size, (0, 0, 0))  # Black background
        draw = ImageDraw.Draw(image)

        # Draw grid with grey lines
        grid_color = '#333333'  # Dark grey for grid
        grid_spacing = 50  # Adjusted grid spacing
        for x in range(0, preview_size[0], grid_spacing):
            draw.line([(x, 0), (x, preview_size[1])], fill=grid_color)
        for y in range(0, preview_size[1], grid_spacing):
            draw.line([(0, y), (0, preview_size[0])], fill=grid_color)

        # Calculate preview box dimensions
        preview_width = 800  # Increased size
        preview_height = int(preview_width * (height / width))

        # Adjust if height is too tall
        if preview_height > 800:  # Adjusted for larger preview
            preview_height = 800
            preview_width = int(preview_height * (width / height))

        # Calculate center position
        x_offset = (preview_size[0] - preview_width) // 2
        y_offset = (preview_size[1] - preview_height) // 2

        # Draw the aspect ratio box with thicker outline
        draw.rectangle(
            [(x_offset, y_offset), (x_offset + preview_width, y_offset + preview_height)],
            outline='red',
            width=4  # Thicker outline
        )

        # Add text with larger font sizes
        try:
            # Draw text (centered)
            text_y = y_offset + preview_height//2

            # Resolution text in red
            draw.text((preview_size[0]//2, text_y),
                     f"{width}x{height}",
                     fill='red',
                     anchor="mm",
                     font=ImageFont.truetype("arial.ttf", 48))

            # Aspect ratio text in red
            draw.text((preview_size[0]//2, text_y + 60),
                     f"({ratio_display})",
                     fill='red',
                     anchor="mm",
                     font=ImageFont.truetype("arial.ttf", 36))

            # Resolution text at bottom in white
            draw.text((preview_size[0]//2, y_offset + preview_height + 60),
                     f"Resolution: {resolution}",
                     fill='white',  # Changed to white
                     anchor="mm",
                     font=ImageFont.truetype("arial.ttf", 32))

        except:
            # Fallback if font loading fails
            draw.text((preview_size[0]//2, text_y), f"{width}x{height}", fill='red', anchor="mm")
            draw.text((preview_size[0]//2, text_y + 60), f"({ratio_display})", fill='red', anchor="mm")
            draw.text((preview_size[0]//2, y_offset + preview_height + 60), f"Resolution: {resolution}", fill='white', anchor="mm")

        # Convert to tensor using the helper function
        return pil2tensor(image)

    def calculate_dimensions(self, megapixel, aspect_ratio, divisible_by, custom_ratio,
                             custom_aspect_ratio=None, custom_resolution=False,
                             custom_resolution_size="1536:1024"):
        round_to = int(divisible_by)

        if custom_resolution:
            # 优先级最高：直接使用自定义尺寸，跳过 megapixel x ratio 计算，
            # 也高于 custom_ratio（两者同时开启时以本分支为准）。
            width, height = parse_custom_size(custom_resolution_size)
            ratio_display = f"{width}:{height} (custom)"
        else:
            megapixel = float(megapixel)

            if custom_ratio and custom_aspect_ratio:
                numeric_ratio = custom_aspect_ratio
                ratio_display = custom_aspect_ratio  # Keep original format for display
            else:
                numeric_ratio = aspect_ratio.split(' ')[0]
                ratio_display = numeric_ratio  # Keep original format for display

            width_ratio, height_ratio = map(int, numeric_ratio.split(':'))

            total_pixels = megapixel * 1_000_000
            dimension = (total_pixels / (width_ratio * height_ratio)) ** 0.5
            width = int(dimension * width_ratio)
            height = int(dimension * height_ratio)

        # Apply user-selected rounding
        width = round(width / round_to) * round_to
        height = round(height / round_to) * round_to

        resolution = f"{width} x {height}"

        # Generate preview image with original ratio format
        preview = self.create_preview_image(width, height, resolution, ratio_display)

        return width, height, resolution, preview


NODE_CLASS_MAPPINGS = {
    "FinalResolutionNode": FinalResolutionNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FinalResolutionNode": "Final Resolution",
}
