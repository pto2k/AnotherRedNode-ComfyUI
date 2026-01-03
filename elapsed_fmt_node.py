# elapsed_fmt_node.py
import torch

class ElapsedFmt:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prefix": ("STRING", {"default": "[time(%Y-%m-%d_%I-%M%p)]_", "multiline": False}),
                "milliseconds": ("INT", {"default": 0, "min": 0, "max": 999999999}),
                "suffix": ("STRING", {"default": "", "multiline": False})
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "fmt"
    CATEGORY = "utils"

    def fmt(self, milliseconds, prefix="", suffix=""):
        # 把 Tensor → Python int
        if isinstance(milliseconds, torch.Tensor):
            milliseconds = milliseconds.squeeze().item()   # 关键修复
        ms = int(milliseconds)

        if ms < 1000:
            formatted_time = f"{ms:03d}ms"
        else:
            sec, ms = divmod(ms, 1000)
            if sec < 60:
                # 只在ms>0时显示毫秒
                if ms > 0:
                    formatted_time = f"{sec:d}s{ms:03d}ms"
                else:
                    formatted_time = f"{sec:d}s"
            else:
                min, sec = divmod(sec, 60)
                if min < 60:
                    # 只在sec>0时显示秒
                    if sec > 0:
                        formatted_time = f"{min:d}m{sec:02d}s"
                    else:
                        formatted_time = f"{min:d}m"
                else:
                    hour, min = divmod(min, 60)
                    time_parts = []
                    
                    # 只添加非零的时间单位
                    time_parts.append(f"{hour:d}h")
                    if min > 0:
                        time_parts.append(f"{min:02d}m")
                    if sec > 0:
                        time_parts.append(f"{sec:02d}s")
                    
                    # 如果分钟和秒都是0，只显示小时
                    formatted_time = "".join(time_parts)
        
        return (f"{prefix}{formatted_time}{suffix}",)

NODE_CLASS_MAPPINGS = {"ElapsedFmt": ElapsedFmt}
NODE_DISPLAY_NAME_MAPPINGS = {"ElapsedFmt": "Elapsed Format (ms→str)"}
