PROMPT_STYLES = {
    "产品视觉": {
        "role": "全品类商业视觉主理人、奢侈品视觉总监、ADC/D&AD 获奖平面设计师、顶级商业静物摄影大师。",
        "focus": "围绕产品材质、品类、颜色、结构和品牌气质，生成高端商业视觉提示词。",
        "rules": [
            "主体默认单体或极少量组合，禁止密集克隆、铺满、重复主体。",
            "强调留白美学、瑞士网格、解构并置、动态层级和高级材质碰撞。",
            "多屏输出必须有不同机位、不同构图和不同空间关系，避免原地换角度。",
            "参考图只用于锁定产品外观、材质、颜色、比例和结构，不凭空增加配件或标识。",
        ],
        "negative": "multiple objects, dense layout, clutter, duplicated items, busy background, wrong structure, deformed product, watermark, unreadable text",
    },
    "高级画册": {
        "role": "ADC/D&AD 获奖级画册设计师，擅长瑞士排版、先锋拼贴、动态层级和品牌视觉叙事。",
        "focus": "生成品牌画册/视觉手册/Lookbook 的连续屏次提示词。",
        "rules": [
            "从封面、目录、设计解构、核心细节、材料科学、使用场景、品牌情绪、封底等屏次中调度。",
            "强调 6pt/12 列网格、极端留白、红色锚点、粗体裁切字、照片块拼贴和精细文字层级。",
            "每屏必须有明确版式逻辑，不重复同一种画面结构。",
            "只输出可直接生图的完整提示词，不输出解释过程。",
        ],
        "negative": "messy layout, random typography, low-end catalog, clutter, watermark, unreadable text, duplicated spread",
    },
    "固定场景模特换装": {
        "role": "AI 绘画提示词分析专家，擅长人物、服装、场景、动作、光影和画面调性的融合。",
        "focus": "保持人物身份或固定场景一致，将服装、配饰和材质准确迁移到目标画面中。",
        "rules": [
            "保持人物形象、身材比例、场景构图、光影、景别、动作和画面调性一致。",
            "服装与配饰细节必须完整一致，强化布料、纹理、缝线、金属件和光影融合。",
            "提示词主体使用中文关键词，关键词之间用英文逗号分隔。",
            "禁止低俗、露骨、擦边、裸露、敏感部位、文字、Logo 和水印。",
        ],
        "negative": "NSFW, exposed body, vulgar, changed identity, changed scene, bad anatomy, logo, watermark, text",
    },
    "人像摄影视觉": {
        "role": "电影海报视觉总监、顶级人像摄影大师、当代视觉艺术家。",
        "focus": "生成户外自然场景中的电影感人像视觉大片。",
        "rules": [
            "单一人物主体，拒绝证件照、企业头像、直视镜头和拥挤背景。",
            "强调自然留白、环境共生、史诗尺度、电影海报叙事和不同镜头焦段。",
            "系列输出应锁定同一宏观自然场景，在不同角落、景别、姿态和镜头语言中游移。",
            "必须避免城市、水泥建筑、多人、肢体畸变和服装漂移。",
        ],
        "negative": "building, city, urban, passport photo, ID photo, looking at camera, multiple people, bad anatomy, changed outfit, watermark",
    },
    "人像视觉系列衍生": {
        "role": "人像视觉系列衍生提示词导演，擅长在同一人物、同一环境、同一服装下生成系列化变化。",
        "focus": "基于参考图做系列衍生，保持人物、服装和环境一致，但改变构图、动作、布局、空间关系和镜头感。",
        "rules": [
            "同一环境、同样服装、同一人物视觉身份必须稳定。",
            "每一屏需要不同构图、不同布局、不同动作、不同空间关系和不同镜头感。",
            "提示词可使用中文关键词，关键词之间用英文逗号分隔。",
            "仅输出提示词文本或 JSON，不做多余陈述。",
        ],
        "negative": "changed identity, changed outfit, changed environment, duplicate pose, same composition, bad anatomy, watermark, text",
    },
}

MODE_OPTIONS = {
    "统一视觉战役": "用于生成同一系列大片。强制抽取并锁定极强基调，同一场景/影棚/自然环境中进行微观空间游移；同批次多张图必须在不同角落、不同局部、不同镜头中变化，形成高级画册的连续叙事。",
    "多维创意宇宙": "用于前期风格探索。打碎统一限制，在审美逻辑、色彩、光影、材质、镜头、场景与构图中进行大胆变化；每张图都是一个独立的艺术平行宇宙。",
}

STYLE_PRESETS = [
    "高级极简商业摄影",
    "Apple风干净科技感",
    "小红书高端生活方式",
    "天猫国际轻奢详情页",
    "亚马逊精品A+页面",
    "未来感玻璃拟态科技",
    "自然光生活化实拍",
    "高级灰白空间美学",
    "暗调奢华棚拍",
    "清透3D产品渲染",
]

ECOMMERCE_SKILL = """
你是 Jojoagent 电商详情页提示词总监，兼具电商视觉全案设计和 AIGC 提示词工程能力。

目标：
为一个商品生成多屏详情页图像提示词。每一屏必须是完整、可直接用于图像生成的提示词。整体叙事遵循：
首屏核心视觉引流 -> 用户痛点/卖点展开 -> 功能与材质证明 -> 使用场景 -> 对比/背书 -> 转化收口。

素材规则：
1. 正面图、背面图、侧面图统一视为同一产品的不同角度，用于锁定产品外观、比例、材质、颜色、结构、接口、Logo 与细节。
2. 风格参考图只提取色调、版式、空间气质、字体层级、光影和构图节奏，不复制其中人物、产品、品牌或具体实体。
3. 如果产品参考图背景杂乱，应在提示词中自动重构为专业棚拍、生活化实景或电商设计场景。
4. 不得凭空增加参考图中不存在的产品部件、配件、品牌标识。

每屏固定包含五个模块：
中文模式：主文案、副文案、版式与字体、画面主体构图、画质质感细节。
英文模式：Main Copy, Sub Copy, Layout & Typography, Visual & Composition, Quality & Details.

输出要求：
只输出字符串数组。数组数量必须等于用户指定的生成屏数/帧数。不要输出 Markdown、解释、代码块或额外字段。
每个数组元素是一条完整提示词，适合直接交给图像生成模型。
"""

NEGATIVE_GUARDRAILS = "避免低清晰度、畸形结构、重复主体、错误文字、水印、脏乱背景、过曝、商品外观改变、比例错误、材质漂移、无关配件。"


def build_prompt(style, instruction, language="中文", screen_index=1, brand_name="选填", mode="统一视觉战役", image_count=0):
    config = PROMPT_STYLES.get(style, PROMPT_STYLES["产品视觉"])
    mode_text = MODE_OPTIONS.get(mode, mode)
    brand = "" if not brand_name or brand_name == "选填" else str(brand_name).strip()
    output_rule = (
        "请输出中文提示词，表达清晰、可直接用于图像生成。"
        if language == "中文"
        else "Output the final image prompt in professional English."
    )
    parts = [
        f"模板：{style}",
        f"角色：{config['role']}",
        f"核心目标：{config['focus']}",
        f"模式：{mode}。{mode_text}",
        f"屏次：第 {int(screen_index)} 屏。请让本屏拥有独立构图价值，并与同系列其他屏次形成差异。",
        f"品牌名：{brand or '不强制出现品牌文字；如需要文字，仅作为版式占位，不生成乱码。'}",
        f"基础指令：{(instruction or '').strip() or '根据参考图和模板规则生成高级视觉提示词。'}",
    ]
    if image_count:
        parts.append(f"参考图数量：{image_count}。请从参考图中提取主体、服装、产品、材质、场景、构图或风格信息，并按模板规则融合。")
    parts.extend(["必须遵守："])
    parts.extend([f"- {rule}" for rule in config["rules"]])
    parts.extend([
        f"输出语言：{output_rule}",
        f"负面约束：{config.get('negative') or NEGATIVE_GUARDRAILS}",
        "输出格式：只输出最终提示词文本，不要解释、不要 Markdown、不要标题。",
    ])
    return "\n".join(parts).strip()


def build_local_ecommerce_prompts(product, selling_points, style, count, language="中文"):
    points = [p.strip() for p in str(selling_points or "").replace("；", "\n").replace(";", "\n").splitlines() if p.strip()]
    if not points:
        points = ["核心卖点", "材质细节", "使用场景"]
    style = style or "高级极简商业摄影"
    sections = ["首屏核心视觉", "用户痛点共鸣", "核心卖点证明", "材质细节特写", "使用场景展示", "对比背书", "转化收口"]
    prompts = []
    for i in range(max(1, int(count))):
        section = sections[i % len(sections)]
        point = points[i % len(points)]
        if language == "英文":
            prompt = (
                f"{section}. Product: {product}. Key message: {point}. Style: {style}. "
                "Main Copy: concise premium headline. Sub Copy: short supporting selling point. "
                "Layout & Typography: ecommerce detail-page layout, clean hierarchy, reserved text area. "
                "Visual & Composition: product remains visually consistent, clear hero composition, suitable for one screen of a product detail page. "
                f"Quality & Details: premium lighting, accurate material, sharp product edges. Avoid: {NEGATIVE_GUARDRAILS}"
            )
        else:
            prompt = (
                f"{section}。商品：{product}。本屏卖点：{point}。视觉风格：{style}。"
                "主文案：一句高级、简洁、有转化力的标题。"
                "副文案：一句辅助说明，突出卖点价值。"
                "版式与字体：电商详情页单屏布局，层级清晰，预留文案区域。"
                "画面主体构图：商品外观保持一致，主体清晰，适合作为详情页连续画面。"
                f"画质质感细节：高级光影，材质准确，边缘清晰。负面约束：{NEGATIVE_GUARDRAILS}"
            )
        prompts.append(prompt)
    return prompts
