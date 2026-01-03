import torch
import pyperclip   # 读取剪贴板：pip install pyperclip


class SSHClipboardMonitor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "force_refresh": ("BOOLEAN", {"default": True, "label": "重新抓取"}),
            },
            "optional": {
                "prefix": ("STRING", {"default": "", "multiline": False}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_text"
    CATEGORY = "utils"

    def get_text(self, force_refresh, prefix=""):
        # force_refresh 本身不用，只是用来让节点认为输入变化
        text = pyperclip.paste().strip()
        return (prefix + text,)


# 注册节点（ComfyUI 要求）
NODE_CLASS_MAPPINGS = {"ssh_clipboard_monitor": SSHClipboardMonitor}
NODE_DISPLAY_NAME_MAPPINGS = {"ssh_clipboard_monitor": "SSH Clipboard Monitor"}