import base64
import io
import json
import re
from pathlib import Path

import numpy as np
import requests
import torch
from PIL import Image, ImageOps

from .jojo_prompts import MODE_OPTIONS, PROMPT_STYLES, STYLE_PRESETS, build_local_ecommerce_prompts, build_prompt


DEFAULT_API_BASE = "http://124.221.138.114:8001"
IMAGE_MODELS = ["gpt-image-2-all", "gemini-3.1-flash-image-preview"]
VISION_MODELS = ["gemini-3.1-flash-lite-preview", "gemini-3.1-flash-lite-preview-thinking-high", "gemini-3-pro-preview", "claude-opus-4-6-thinking"]
IMAGE_SIZE_OPTIONS = ["1K", "2K", "4K"]
ASPECT_RATIO_OPTIONS = ["智能比例", "1:1", "1:2", "2:1", "9:16", "16:9", "3:4", "4:3", "3:2", "2:3", "5:4", "4:5", "21:9", "9:21"]
IMAGE_QUALITY_OPTIONS = ["低画质", "标准画质", "高画质"]
IMAGE_QUALITY_MAP = {"低画质": "low", "标准画质": "standard", "高画质": "high"}
MODEL_LABELS = {
    "gpt-image-2-all": "GPT-Image-2 1K",
    "gemini-3.1-flash-image-preview": "Gemini 3.1 Flash Image",
}
_RUN_COUNTER = {"index": 0}


def _api_base(api_base):
    base = (api_base or DEFAULT_API_BASE).strip().rstrip("/")
    if base in ("http://127.0.0.1:8001", "http://localhost:8001", "https://127.0.0.1:8001", "https://localhost:8001"):
        return DEFAULT_API_BASE
    return base


def _headers(api_token):
    token = (api_token or "").strip()
    if not token:
        raise RuntimeError("请填写 Jojoagent 分配给你的 API 口令")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _decode_image(image_base64):
    raw = base64.b64decode(image_base64)
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    arr = np.array(img).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


def _pil_to_tensor(img):
    arr = np.array(img.convert("RGB")).astype(np.float32) / 255.0
    return torch.from_numpy(arr).unsqueeze(0)


def _tensor_to_pil(image):
    if len(image.shape) > 3:
        image = image[0]
    arr = (image.cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
    return Image.fromarray(arr).convert("RGB")


def _tensor_to_base64(image, max_side=1536, quality=92):
    img = _tensor_to_pil(image)
    width, height = img.size
    longest = max(width, height)
    if max_side and longest > max_side:
        scale = max_side / float(longest)
        img = img.resize((round(width * scale), round(height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=int(quality), optimize=True)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _split_text_items(text):
    raw = str(text or "").strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass
    return [x.strip() for x in re.split(r"\n+|---+", raw) if x.strip()]


def _request_image(api_base, api_token, model, prompt, output_size="1K", aspect_ratio="1:1", image_quality="标准画质", seed=-1, reference_images=None):
    payload = {
        "model": model,
        "prompt": prompt,
        "output_size": output_size,
        "aspect_ratio": aspect_ratio,
        "image_quality": IMAGE_QUALITY_MAP.get(image_quality, image_quality),
        "seed": int(seed),
        "images": reference_images or [],
    }
    res = requests.post(f"{_api_base(api_base)}/api/generate-image", headers=_headers(api_token), json=payload, timeout=240)
    if res.status_code != 200:
        raise RuntimeError(f"生成失败: HTTP {res.status_code} {res.text[:800]}")
    data = res.json().get("data", {})
    return _decode_image(data["image_base64"]), data


class JojoAccount:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"操作": (["查询余额", "最近用量"], {"default": "查询余额"}), "api_base": ("STRING", {"default": DEFAULT_API_BASE}), "api_token": ("STRING", {"default": ""}), "用量条数": ("INT", {"default": 20, "min": 1, "max": 100})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("account_info",)
    FUNCTION = "run"
    CATEGORY = "Jojoagent/API"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def run(self, 操作, api_base, api_token, 用量条数):
        url = f"{_api_base(api_base)}/api/usage?limit={int(用量条数)}" if 操作 == "最近用量" else f"{_api_base(api_base)}/api/balance"
        res = requests.get(url, headers=_headers(api_token), timeout=30)
        if res.status_code != 200:
            raise RuntimeError(f"Jojoagent API 请求失败: HTTP {res.status_code} {res.text[:500]}")
        data = res.json().get("data", {})
        if 操作 == "最近用量":
            lines = ["最近用量："]
            for item in data:
                lines.append(f"- {item.get('created_at', '')} | {item.get('model', '')} | {item.get('status', '')} | 扣除 {item.get('cost', 0)}")
            return ("\n".join(lines),)
        return (f"用户：{data.get('name', '')}\n剩余额度：{data.get('balance', 0)}\n状态：{data.get('status', '')}\n到期：{data.get('expires_at') or '无'}",)


class JojoImageGenerate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_base": ("STRING", {"default": DEFAULT_API_BASE}),
                "api_token": ("STRING", {"default": ""}),
                "模型": (IMAGE_MODELS, {"default": "gpt-image-2-all"}),
                "提示词": ("STRING", {"multiline": True, "default": "一张高级质感的商品主图"}),
                "图像规格": (IMAGE_SIZE_OPTIONS, {"default": "1K"}),
                "图片比例": (ASPECT_RATIO_OPTIONS, {"default": "1:1"}),
                "图像质量": (IMAGE_QUALITY_OPTIONS, {"default": "标准画质"}),
                "随机种子": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
            "optional": {
                "参考图1": ("IMAGE",),
                "参考图2": ("IMAGE",),
                "参考图3": ("IMAGE",),
                "参考图4": ("IMAGE",),
                "参考图5": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "run_info")
    FUNCTION = "generate"
    CATEGORY = "Jojoagent/API"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def generate(self, api_base, api_token, 模型, 提示词, 图像规格, 图片比例, 图像质量, 随机种子, 参考图1=None, 参考图2=None, 参考图3=None, 参考图4=None, 参考图5=None):
        reference_images = [_tensor_to_base64(image) for image in [参考图1, 参考图2, 参考图3, 参考图4, 参考图5] if image is not None]
        image, data = _request_image(api_base, api_token, 模型, 提示词, 图像规格, 图片比例, 图像质量, 随机种子, reference_images)
        info = f"模型：{MODEL_LABELS.get(data.get('model'), data.get('model'))}\n规格：{data.get('output_size')} / {data.get('aspect_ratio')} / {图像质量}\n尺寸：{data.get('width')}x{data.get('height')}\n随机种子：{data.get('seed')}\n参考图：{len(reference_images)} 张\n扣除积分：{data.get('cost')}\n基础成本：{data.get('t8_cost')}\n倍率：{data.get('multiplier')}\n请求ID：{data.get('request_id')}"
        return (image, info)


class JojoImageBatch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_base": ("STRING", {"default": DEFAULT_API_BASE}),
                "api_token": ("STRING", {"default": ""}),
                "批量模式": (["多提示词生图", "单提示词多次"], {"default": "多提示词生图"}),
                "模型": (IMAGE_MODELS, {"default": "gpt-image-2-all"}),
                "提示词列表": ("STRING", {"multiline": True, "default": ""}),
                "单提示词": ("STRING", {"multiline": True, "default": ""}),
                "生成次数": ("INT", {"default": 1, "min": 1, "max": 100}),
                "图像规格": (IMAGE_SIZE_OPTIONS, {"default": "1K"}),
                "图片比例": (ASPECT_RATIO_OPTIONS, {"default": "1:1"}),
                "图像质量": (IMAGE_QUALITY_OPTIONS, {"default": "标准画质"}),
                "随机种子": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
            },
            "optional": {
                "参考图1": ("IMAGE",),
                "参考图2": ("IMAGE",),
                "参考图3": ("IMAGE",),
                "参考图4": ("IMAGE",),
                "参考图5": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "batch_info")
    FUNCTION = "generate_batch"
    CATEGORY = "Jojoagent/API"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def generate_batch(self, api_base, api_token, 批量模式, 模型, 提示词列表, 单提示词, 生成次数, 图像规格, 图片比例, 图像质量, 随机种子, 参考图1=None, 参考图2=None, 参考图3=None, 参考图4=None, 参考图5=None):
        prompts = _split_text_items(提示词列表) if 批量模式 == "多提示词生图" else [单提示词 or ""] * int(生成次数)
        if not prompts:
            prompts = [单提示词 or ""]
        reference_images = [_tensor_to_base64(image) for image in [参考图1, 参考图2, 参考图3, 参考图4, 参考图5] if image is not None]
        tensors, lines, total_cost = [], [], 0.0
        for i, prompt in enumerate(prompts, 1):
            seed = int(随机种子)
            current_seed = seed + i - 1 if seed >= 0 else -1
            image, data = _request_image(api_base, api_token, 模型, prompt, 图像规格, 图片比例, 图像质量, current_seed, reference_images)
            tensors.append(image)
            total_cost += float(data.get("cost") or 0)
            lines.append(f"{i}. {data.get('request_id')} | {data.get('width')}x{data.get('height')} | seed={data.get('seed')} | 扣除 {data.get('cost')}")
        info = f"完成 {len(tensors)} 张\n规格：{图像规格} / {图片比例} / {图像质量}\n参考图：{len(reference_images)} 张\n总扣除：{round(total_cost, 4)}\n" + "\n".join(lines)
        return (torch.cat(tensors, dim=0), info)


class JojoCreditDetail:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_base": ("STRING", {"default": DEFAULT_API_BASE}),
                "api_token": ("STRING", {"default": ""}),
                "显示条数": ("INT", {"default": 10, "min": 1, "max": 100}),
                "只看成功扣费": (["是", "否"], {"default": "否"}),
            },
            "optional": {
                "刷新触发": ("*",),
            },
        }

    RETURN_TYPES = ("STRING", "FLOAT", "INT")
    RETURN_NAMES = ("扣费详情", "合计扣除", "记录数量")
    FUNCTION = "show"
    CATEGORY = "Jojoagent/API"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def show(self, api_base, api_token, 显示条数, 只看成功扣费, 刷新触发=None):
        usage_res = requests.get(f"{_api_base(api_base)}/api/usage?limit={int(显示条数)}", headers=_headers(api_token), timeout=30)
        if usage_res.status_code != 200:
            raise RuntimeError(f"扣费详情读取失败: HTTP {usage_res.status_code} {usage_res.text[:500]}")
        balance_res = requests.get(f"{_api_base(api_base)}/api/balance", headers=_headers(api_token), timeout=30)
        balance_text = ""
        if balance_res.status_code == 200:
            balance = balance_res.json().get("data", {}).get("balance", "")
            balance_text = f"当前余额：{balance}\n"

        rows = usage_res.json().get("data", [])
        if 只看成功扣费 == "是":
            rows = [row for row in rows if row.get("status") == "success"]

        total = round(sum(float(row.get("cost") or 0) for row in rows if row.get("status") == "success"), 4)
        lines = [
            "Jojo 本次/最近扣费详情",
            balance_text + f"显示记录：{len(rows)} 条",
            f"成功扣费合计：{total}",
            "",
        ]
        for index, row in enumerate(rows, 1):
            status = row.get("status", "")
            cost = float(row.get("cost") or 0)
            message = row.get("message") or ""
            lines.append(
                f"{index}. {row.get('created_at', '')}\n"
                f"   模型：{row.get('model', '')}\n"
                f"   状态：{status} | 扣除：{round(cost, 4)}\n"
                f"   请求ID：{row.get('request_id', '')}\n"
                f"   详情：{message}"
            )
        return ("\n".join(lines).strip(), total, len(rows))


class JojoPromptOptimizer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "模板": (list(PROMPT_STYLES.keys()), {"default": "产品视觉"}),
                "模式": (list(MODE_OPTIONS.keys()), {"default": "统一视觉战役"}),
                "屏次": ("INT", {"default": 1, "min": 1, "max": 100}),
                "品牌名": ("STRING", {"default": "选填"}),
                "输出语言": (["中文", "英文"], {"default": "中文"}),
                "识图模型": (VISION_MODELS, {"default": "gemini-3-pro-preview"}),
                "api_base": ("STRING", {"default": DEFAULT_API_BASE}),
                "api_token": ("STRING", {"default": ""}),
                "最大输出": ("INT", {"default": 4096, "min": 1024, "max": 32768, "step": 512}),
                "基础指令": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "图像1": ("IMAGE",),
                "图像2": ("IMAGE",),
                "图像3": ("IMAGE",),
                "图像4": ("IMAGE",),
                "图像5": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("optimized_prompt", "prompts_list", "prompts_count")
    FUNCTION = "optimize"
    CATEGORY = "Jojoagent/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def optimize(self, 模板, 模式, 屏次, 品牌名, 输出语言, 识图模型, api_base, api_token, 最大输出, 基础指令, 图像1=None, 图像2=None, 图像3=None, 图像4=None, 图像5=None):
        images = [_tensor_to_base64(image) for image in [图像1, 图像2, 图像3, 图像4, 图像5] if image is not None]
        count = max(1, int(屏次))
        local_prompts = [build_prompt(模板, 基础指令, 输出语言, i, 品牌名, 模式, len(images)) for i in range(1, count + 1)]
        local_prompt = local_prompts[0]
        local_prompts_text = "\n---\n".join(local_prompts)
        if not images:
            return (local_prompt, local_prompts_text, len(local_prompts))

        instruction = (
            f"{build_prompt(模板, 基础指令, 输出语言, 屏次, 品牌名, 模式, len(images))}\n\n"
            "请结合上传图像进行视觉识别：图像可分别作为主体、产品、人物、服装、场景或风格参考。"
            "保留参考图中需要稳定的身份、材质、服装、产品结构与场景气质，同时根据模板和模式生成多屏提示词。"
            f"必须生成 {count} 条提示词，每条对应一个屏次；每条都要有不同构图、镜头、动作或空间关系。"
            "请优先输出 JSON 字符串数组；如果无法输出数组，也要用换行分隔每条提示词。"
        )
        payload = {
            "images": images,
            "instruction": instruction,
            "model": 识图模型,
            "reference_mode": f"{模板}-{模式}",
            "target_ratio": f"第{int(屏次)}屏",
            "output_language": 输出语言,
            "temperature": 0.35,
            "max_tokens": int(最大输出),
        }
        res = requests.post(f"{_api_base(api_base)}/api/reverse-prompt", headers=_headers(api_token), json=payload, timeout=300)
        if res.status_code != 200:
            raise RuntimeError(f"提示词识图优化失败: HTTP {res.status_code} {res.text[:800]}")
        data = res.json().get("data", {})
        prompt_list = data.get("prompt_list")
        if isinstance(prompt_list, list):
            prompts = [str(x).strip() for x in prompt_list if str(x).strip()]
        else:
            raw = str(data.get("optimized_prompt", "")).strip()
            prompts = _split_text_items(raw)
        if len(prompts) < count:
            prompts = local_prompts
        prompts = prompts[:count]
        return (prompts[0], "\n---\n".join(prompts), len(prompts))


class JojoEcommercePrompts:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "商品名称": ("STRING", {"default": "手机"}),
                "卖点列表": ("STRING", {"multiline": True, "default": "核心卖点\n材质细节\n使用场景"}),
                "视觉风格": (["选填/自动"] + STYLE_PRESETS, {"default": "选填/自动"}),
                "生成屏数": ("INT", {"default": 6, "min": 1, "max": 30}),
                "输出语言": (["中文", "英文"], {"default": "中文"}),
                "识图模型": (VISION_MODELS, {"default": "gemini-3-pro-preview"}),
                "api_base": ("STRING", {"default": DEFAULT_API_BASE}),
                "api_token": ("STRING", {"default": ""}),
                "最大输出": ("INT", {"default": 8192, "min": 1024, "max": 32768, "step": 512}),
            },
            "optional": {
                "正面图": ("IMAGE",),
                "背面图": ("IMAGE",),
                "侧面图": ("IMAGE",),
                "风格参考1": ("IMAGE",),
                "风格参考2": ("IMAGE",),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("prompts_list", "prompts_count")
    FUNCTION = "build"
    CATEGORY = "Jojoagent/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def build(self, 商品名称, 卖点列表, 视觉风格, 生成屏数, 输出语言, 识图模型, api_base, api_token, 最大输出, 正面图=None, 背面图=None, 侧面图=None, 风格参考1=None, 风格参考2=None):
        style = "" if 视觉风格 == "选填/自动" else 视觉风格
        images = []
        for image in [正面图, 背面图, 侧面图, 风格参考1, 风格参考2]:
            if image is not None:
                images.append(_tensor_to_base64(image))
        if images:
            instruction = f"请基于商品多角度图和风格参考图，为商品“{商品名称}”生成{生成屏数}屏电商详情页提示词。卖点：{卖点列表}。视觉风格：{style or '由模型结合参考图自动判断'}。"
            payload = {"images": images, "instruction": instruction, "model": 识图模型, "reference_mode": "电商详情页", "target_ratio": "详情页单屏", "output_language": 输出语言, "temperature": 0.35, "max_tokens": int(最大输出)}
            res = requests.post(f"{_api_base(api_base)}/api/reverse-prompt", headers=_headers(api_token), json=payload, timeout=300)
            if res.status_code != 200:
                raise RuntimeError(f"电商详情页识图生成失败: HTTP {res.status_code} {res.text[:800]}")
            data = res.json().get("data", {})
            prompt_list = data.get("prompt_list")
            if isinstance(prompt_list, list):
                prompts = [str(x) for x in prompt_list]
            else:
                raw = data.get("optimized_prompt", "")
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        prompts = [str(x) for x in parsed]
                    else:
                        prompts = _split_text_items(raw)
                except Exception:
                    prompts = _split_text_items(raw)
            if len(prompts) < int(生成屏数):
                prompts = build_local_ecommerce_prompts(商品名称, 卖点列表, style, 生成屏数, 输出语言)
        else:
            prompts = build_local_ecommerce_prompts(商品名称, 卖点列表, style, 生成屏数, 输出语言)
        prompts = prompts[: int(生成屏数)]
        return ("\n---\n".join(prompts), len(prompts))


class JojoReversePrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image1": ("IMAGE",),
                "api_base": ("STRING", {"default": DEFAULT_API_BASE}),
                "api_token": ("STRING", {"default": ""}),
                "识图模型": (VISION_MODELS, {"default": "gemini-3-pro-preview"}),
                "用户指令": ("STRING", {"multiline": True, "default": "分析图片并反推适合生图的高质量提示词"}),
                "参考模式": (["完整参考", "只参考风格", "只参考构图", "只参考色彩光影", "商品主体保持"], {"default": "完整参考"}),
                "目标画幅": (["自动", "1:1", "16:9", "9:16", "4:3", "3:4", "4:5"], {"default": "自动"}),
                "输出语言": (["中文", "英文"], {"default": "中文"}),
                "创造性": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 2.0, "step": 0.05}),
                "最大输出": ("INT", {"default": 4096, "min": 256, "max": 32768, "step": 128}),
            },
            "optional": {"image2": ("IMAGE",), "image3": ("IMAGE",), "image4": ("IMAGE",), "image5": ("IMAGE",), "image6": ("IMAGE",), "image7": ("IMAGE",), "image8": ("IMAGE",)},
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("optimized_prompt", "image_analysis", "negative_prompt", "run_info")
    FUNCTION = "run"
    CATEGORY = "Jojoagent/Prompt"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def run(self, image1, api_base, api_token, 识图模型, 用户指令, 参考模式, 目标画幅, 输出语言, 创造性, 最大输出, image2=None, image3=None, image4=None, image5=None, image6=None, image7=None, image8=None):
        images = [_tensor_to_base64(image) for image in [image1, image2, image3, image4, image5, image6, image7, image8] if image is not None]
        payload = {"images": images, "instruction": 用户指令, "model": 识图模型, "reference_mode": 参考模式, "target_ratio": 目标画幅, "output_language": 输出语言, "temperature": float(创造性), "max_tokens": int(最大输出)}
        res = requests.post(f"{_api_base(api_base)}/api/reverse-prompt", headers=_headers(api_token), json=payload, timeout=300)
        if res.status_code != 200:
            raise RuntimeError(f"识图反推失败: HTTP {res.status_code} {res.text[:800]}")
        data = res.json().get("data", {})
        analysis = data.get("image_analysis", "")
        if isinstance(analysis, list):
            analysis = "\n".join(f"- {item}" for item in analysis)
        info = f"模型：{data.get('model')}\n图片数：{data.get('image_count')}\n扣除积分：{data.get('cost')}\n倍率：{data.get('multiplier')}\n请求ID：{data.get('request_id')}\n备注：{data.get('model_notes', '')}"
        return (str(data.get("optimized_prompt", "")), str(analysis or ""), str(data.get("negative_prompt", "")), info)


class JojoTextTools:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"功能": (["文本分割", "选择单条", "范围选择", "重复文本", "批次分组", "标记提取"], {"default": "文本分割"}), "文本": ("STRING", {"multiline": True, "default": ""}), "分隔符": ("STRING", {"default": "\\n"}), "索引": ("INT", {"default": 0, "min": 0, "max": 999999}), "起始": ("INT", {"default": 0, "min": 0, "max": 999999}), "结束": ("INT", {"default": 10, "min": 0, "max": 999999}), "重复次数": ("INT", {"default": 2, "min": 1, "max": 1000}), "批次大小": ("INT", {"default": 5, "min": 1, "max": 1000}), "开始标记": ("STRING", {"default": "{|"}), "结束标记": ("STRING", {"default": "|}"})}}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("text", "count")
    FUNCTION = "process"
    CATEGORY = "Jojoagent/Text"

    def process(self, 功能, 文本, 分隔符, 索引, 起始, 结束, 重复次数, 批次大小, 开始标记, 结束标记):
        sep = 分隔符.encode("utf-8").decode("unicode_escape")
        if 功能 == "文本分割":
            items = [x.strip() for x in str(文本).split(sep) if x.strip()]
        elif 功能 == "标记提取":
            pattern = re.escape(开始标记) + r"(.*?)" + re.escape(结束标记)
            items = [m.strip() for m in re.findall(pattern, str(文本), flags=re.S) if m.strip()]
        else:
            items = _split_text_items(文本)
        if 功能 == "选择单条":
            return (items[min(索引, len(items) - 1)] if items else "", len(items))
        if 功能 == "范围选择":
            picked = items[起始:结束]
            return ("\n".join(picked), len(picked))
        if 功能 == "重复文本":
            return ("\n".join([str(文本)] * int(重复次数)), int(重复次数))
        if 功能 == "批次分组":
            groups = ["\n".join(items[i:i + 批次大小]) for i in range(0, len(items), 批次大小)]
            return ("\n---\n".join(groups), len(groups))
        return ("\n".join(items), len(items))


class JojoImageTools:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"功能": (["加载图片", "缩放图片", "范围选择", "保存预览"], {"default": "加载图片"}), "文件路径": ("STRING", {"default": ""}), "宽度": ("INT", {"default": 1024, "min": 1, "max": 8192}), "高度": ("INT", {"default": 1024, "min": 1, "max": 8192}), "起始": ("INT", {"default": 0, "min": 0, "max": 999999}), "结束": ("INT", {"default": 1, "min": 0, "max": 999999})}, "optional": {"image": ("IMAGE",)}}

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "info")
    FUNCTION = "process"
    CATEGORY = "Jojoagent/Image"

    def process(self, 功能, 文件路径, 宽度, 高度, 起始, 结束, image=None):
        if 功能 == "加载图片":
            p = Path(文件路径).expanduser()
            if not p.exists():
                raise RuntimeError(f"图片不存在：{p}")
            return (_pil_to_tensor(ImageOps.exif_transpose(Image.open(p)).convert("RGB")), str(p))
        if image is None:
            raise RuntimeError("该功能需要连接 image 输入")
        if 功能 == "缩放图片":
            return (_pil_to_tensor(_tensor_to_pil(image).resize((宽度, 高度), Image.LANCZOS)), f"缩放到 {宽度}x{高度}")
        if 功能 == "范围选择":
            total = image.shape[0] if len(image.shape) == 4 else 1
            s, e = min(max(起始, 0), total), min(max(结束, 起始 + 1), total)
            return (image[s:e] if len(image.shape) == 4 else image, f"选择 {s}:{e} / {total}")
        return (image, "预览透传")


class JojoFolderScanner:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"文件夹": ("STRING", {"default": ""}), "类型": (["全部", "图片", "文本", "视频", "音频"], {"default": "图片"}), "递归": (["是", "否"], {"default": "是"}), "排序": (["名称升序", "名称降序", "时间升序", "时间降序"], {"default": "名称升序"}), "最大数量": ("INT", {"default": 200, "min": 1, "max": 10000})}}

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("paths", "count")
    FUNCTION = "scan"
    CATEGORY = "Jojoagent/Utils"

    def scan(self, 文件夹, 类型, 递归, 排序, 最大数量):
        root = Path(文件夹).expanduser()
        if not root.exists():
            raise RuntimeError(f"文件夹不存在：{root}")
        exts = {"图片": {".png", ".jpg", ".jpeg", ".webp", ".bmp"}, "文本": {".txt", ".md", ".json", ".csv"}, "视频": {".mp4", ".mov", ".avi", ".mkv", ".webm"}, "音频": {".mp3", ".wav", ".m4a", ".flac", ".aac"}}.get(类型)
        files = [p for p in (root.rglob("*") if 递归 == "是" else root.glob("*")) if p.is_file()]
        if exts:
            files = [p for p in files if p.suffix.lower() in exts]
        reverse = 排序 in ("名称降序", "时间降序")
        key = (lambda p: p.stat().st_mtime) if 排序.startswith("时间") else (lambda p: str(p).lower())
        files = sorted(files, key=key, reverse=reverse)[:最大数量]
        return ("\n".join(str(p) for p in files), len(files))


class JojoPathLoader:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"路径": ("STRING", {"default": ""}), "类型": (["视频", "音频", "任意文件"], {"default": "视频"})}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("path",)
    FUNCTION = "load"
    CATEGORY = "Jojoagent/Utils"

    def load(self, 路径, 类型):
        p = Path(路径).expanduser()
        if not p.exists():
            raise RuntimeError(f"文件不存在：{p}")
        return (str(p),)


class JojoRunIndex:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"操作": (["自增", "重置"], {"default": "自增"}), "起始值": ("INT", {"default": 0, "min": -999999, "max": 999999})}}

    RETURN_TYPES = ("INT",)
    RETURN_NAMES = ("index",)
    FUNCTION = "run"
    CATEGORY = "Jojoagent/Utils"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("NaN")

    def run(self, 操作, 起始值):
        if 操作 == "重置":
            _RUN_COUNTER["index"] = int(起始值)
            return (_RUN_COUNTER["index"],)
        current = _RUN_COUNTER["index"]
        _RUN_COUNTER["index"] += 1
        return (current,)


NODE_CLASS_MAPPINGS = {
    "JojoAccount": JojoAccount,
    "JojoImageGenerate": JojoImageGenerate,
    "JojoImageBatch": JojoImageBatch,
    "JojoCreditDetail": JojoCreditDetail,
    "JojoPromptOptimizer": JojoPromptOptimizer,
    "JojoEcommercePrompts": JojoEcommercePrompts,
    "JojoReversePrompt": JojoReversePrompt,
    "JojoTextTools": JojoTextTools,
    "JojoImageTools": JojoImageTools,
    "JojoFolderScanner": JojoFolderScanner,
    "JojoPathLoader": JojoPathLoader,
    "JojoRunIndex": JojoRunIndex,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JojoAccount": "Jojo 账号与用量",
    "JojoImageGenerate": "Jojo AI 图像生成",
    "JojoImageBatch": "Jojo AI 批量图像生成",
    "JojoCreditDetail": "Jojo 扣费详情",
    "JojoPromptOptimizer": "Jojo 提示词优化器",
    "JojoEcommercePrompts": "Jojo 电商详情页提示词",
    "JojoReversePrompt": "Jojo 识图提示词反推",
    "JojoTextTools": "Jojo 文本工具",
    "JojoImageTools": "Jojo 图片工具",
    "JojoFolderScanner": "Jojo 文件夹扫描",
    "JojoPathLoader": "Jojo 媒体路径加载",
    "JojoRunIndex": "Jojo 运行索引",
}
