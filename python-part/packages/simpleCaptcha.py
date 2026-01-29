"""
简单的图形验证码生成模块
生成 4 位数字/字母验证码，不区分大小写
"""

import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import base64


class SimpleCaptcha:
    """简单验证码生成类"""
    
    def __init__(self, length=4, width=120, height=50):
        """
        初始化验证码生成器
        :param length: 验证码长度，默认4位
        :param width: 图片宽度
        :param height: 图片高度
        """
        self.length = length
        self.width = width
        self.height = height
        # 验证码字符集：数字和字母（不包含容易混淆的字符如0OIl1）
        self.chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    
    def generate_code(self):
        """
        生成随机验证码文本
        :return: 验证码字符串
        """
        return ''.join(random.choice(self.chars) for _ in range(self.length))
    
    def generate_captcha_image(self, code=None):
        """
        生成验证码图片
        :param code: 指定的验证码文本，如果为None则自动生成
        :return: (验证码文本, base64编码的图片)
        """
        # 生成验证码文本
        if code is None:
            code = self.generate_code()
        
        # 创建图片，背景使用浅色
        bg_color = self._random_color(240, 255)
        image = Image.new('RGB', (self.width, self.height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # 绘制背景干扰线（增加数量和粗细）
        for _ in range(random.randint(5, 8)):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line([(x1, y1), (x2, y2)], fill=self._random_color(150, 200), width=random.randint(1, 2))
        
        # 绘制曲线干扰线
        for _ in range(random.randint(2, 3)):
            points = []
            for j in range(5):
                x = self.width * j // 4 + random.randint(-5, 5)
                y = random.randint(0, self.height)
                points.append((x, y))
            draw.line(points, fill=self._random_color(150, 200), width=1)
        
        # 绘制干扰点（增加数量）
        for _ in range(random.randint(100, 150)):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill=self._random_color(100, 200))
        
        # 尝试加载字体，如果失败则使用默认字体
        try:
            # Windows 系统字体路径
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            try:
                # Linux 系统字体路径
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
            except:
                # 如果都失败，使用默认字体
                font = ImageFont.load_default()
        
        # 计算字符间距，确保字符不会超出边界
        # 留出左右各10像素的边距
        padding = 10
        usable_width = self.width - 2 * padding
        char_width = usable_width // self.length
        
        # 绘制验证码文本
        for i, char in enumerate(code):
            # 创建临时图片用于旋转字符
            char_image = Image.new('RGBA', (char_width, self.height), (255, 255, 255, 0))
            char_draw = ImageDraw.Draw(char_image)
            
            # 随机颜色（深色，确保可读性）
            color = self._random_color(10, 80)
            
            # 在临时图片中心位置绘制字符
            # 使用 textbbox 获取文本边界框
            try:
                bbox = char_draw.textbbox((0, 0), char, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
            except:
                # 如果 textbbox 不可用（旧版本 Pillow），使用估算值
                text_width = char_width // 2
                text_height = self.height // 2
            
            # 计算居中位置
            text_x = (char_width - text_width) // 2
            text_y = (self.height - text_height) // 2 - 5
            
            char_draw.text((text_x, text_y), char, font=font, fill=color)
            
            # 随机旋转字符（-20到20度）
            angle = random.randint(-20, 20)
            char_image = char_image.rotate(angle, expand=False, fillcolor=(255, 255, 255, 0))
            
            # 计算粘贴位置
            x = padding + char_width * i + random.randint(-3, 3)
            y = random.randint(-5, 5)
            
            # 将旋转后的字符粘贴到主图片
            image.paste(char_image, (x, y), char_image)
        
        # 添加更多干扰线覆盖在文字上
        for _ in range(random.randint(2, 3)):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line([(x1, y1), (x2, y2)], fill=self._random_color(180, 220), width=1)
        
        # 添加高斯模糊（轻微）
        image = image.filter(ImageFilter.GaussianBlur(radius=0.8))
        
        # 转换为base64
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return code, img_base64
    
    def _random_color(self, min_val=0, max_val=255):
        """
        生成随机颜色
        :param min_val: RGB最小值
        :param max_val: RGB最大值
        :return: (R, G, B) 元组
        """
        return (
            random.randint(min_val, max_val),
            random.randint(min_val, max_val),
            random.randint(min_val, max_val)
        )


# 创建全局实例
captcha_generator = SimpleCaptcha()


def generate_captcha():
    """
    生成验证码
    :return: (验证码文本, base64编码的图片)
    """
    return captcha_generator.generate_captcha_image()


def verify_captcha_code(user_input, correct_code):
    """
    验证验证码（不区分大小写）
    :param user_input: 用户输入的验证码
    :param correct_code: 正确的验证码
    :return: 是否正确
    """
    if not user_input or not correct_code:
        return False
    return user_input.upper() == correct_code.upper()
