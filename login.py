# login.py
import requests
import re
import json
import os
import sys

# Discuz! 论坛配置
BASE_URL = "https://www.rosabc.com"
LOGIN_URL = f"{BASE_URL}/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def get_formhash(session):
    """获取登录页面中的 formhash（防CSRF令牌）"""
    resp = session.get(f"{BASE_URL}/member.php?mod=logging&action=login", headers={
        "User-Agent": USER_AGENT,
        "Referer": BASE_URL
    })
    
    # 从源码中提取 formhash
    match = re.search(r'name="formhash" value="([a-f0-9]{8})"', resp.text)
    if match:
        return match.group(1)
    
    # 尝试从公用变量中提取（Discuz! 通常在页面头部定义）
    match = re.search(r'formhash=([a-f0-9]{8})', resp.text)
    if match:
        return match.group(1)
    
    raise Exception("无法获取 formhash")

def login():
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")
    
    if not username or not password:
        print("❌ 缺少用户名或密码")
        sys.exit(1)
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Referer": BASE_URL,
        "X-Requested-With": "XMLHttpRequest"
    })
    
    try:
        # 1. 获取 formhash
        print("🔍 获取 formhash...")
        formhash = get_formhash(session)
        print(f"✅ Formhash: {formhash}")
        
        # 2. 提交登录（Discuz! 标准登录接口）
        login_data = {
            "formhash": formhash,
            "referer": BASE_URL,
            "username": username,
            "password": password,
            "questionid": "0",  # 安全提问，默认0为无
            "answer": "",
            "cookietime": "2592000"  # 30天Cookie有效期
        }
        
        print(f"🔐 正在登录用户: {username}")
        resp = session.post(LOGIN_URL, data=login_data, allow_redirects=True)
        
        # 3. 验证登录结果
        if "欢迎" in resp.text or username in resp.text or "登录成功" in resp.text:
            print("✅ 登录成功!")
            
            # 检查用户空间确认登录状态
            user_check = session.get(f"{BASE_URL}/home.php?mod=spacecp", allow_redirects=False)
            if user_check.status_code == 200:
                # 匹配用户积分信息（你源码中的格式）
                credit_match = re.search(r'积分[:：]\s*(\d+)', user_check.text)
                if credit_match:
                    print(f"💰 当前积分: {credit_match.group(1)}")
                
                # 保存 Cookie 供后续使用（如签到）
                cookies = {c.name: c.value for c in session.cookies}
                with open("cookies.json", "w", encoding="utf-8") as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                
                return True
        
        # 检查常见错误
        if "密码错误" in resp.text or "登录失败" in resp.text:
            print("❌ 密码错误或账户不存在")
        elif "验证码" in resp.text:
            print("❌ 需要验证码，请使用方案2（Playwright）")
        else:
            print("⚠️ 登录状态未知，请检查响应")
            # 调试时可取消下面注释查看返回内容
            # print(resp.text[:2000])
        
        return False
        
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = login()
    sys.exit(0 if success else 1)
